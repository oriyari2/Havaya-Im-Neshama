from __future__ import annotations

import json
from uuid import uuid4

import httpx
from psycopg.rows import dict_row

from backend.app.db.connection import get_connection
from backend.app.infrastructure.repositories import knowledge_retrieval_repository
from rag.embedding_client import OllamaEmbeddingClient
from rag.embedding_formatting import (
    KnowledgeDocumentText,
    format_document_embedding_input,
    format_query_embedding_input,
)
from rag.evaluation import (
    EvaluationCase,
    RetrievalHit,
    calculate_failure_report,
    calculate_raw_metrics,
    calculate_threshold_metrics,
    generate_candidate_thresholds,
    load_evaluation_cases,
)


MODELS = ["nomic-embed-text", "nomic-embed-text-v2-moe", "bge-m3"]
SOURCE_PREFIX = "eval://task16-hebrew-model-comparison/"
THRESHOLDS = [
    0.25,
    0.30,
    0.35,
    0.40,
    0.45,
    0.46,
    0.47,
    0.48,
    0.49,
    0.50,
    0.55,
    0.60,
    0.61,
    0.62,
    0.63,
    0.64,
    0.65,
    0.66,
    0.67,
    0.68,
    0.69,
    0.70,
    0.71,
    0.72,
    0.73,
]

DOCUMENTS = [
    ("Task16 Eval Equipment", "equipment", ["manager", "instructor", "customer"], "תפוס את האור", "לפני פעילות תפוס את האור יש לטעון את כל יחידות האור, לבדוק מטענים, סוללות גיבוי וערכות ציוד מלאות."),
    ("Task16 Eval Preparation", "preparation", ["manager", "instructor", "customer"], "סדנאות יצירה", "לפני סדנת תיקים או סוכה יש להכין שולחנות עבודה, חומרי יצירה, משטחי עבודה ואריזות לפי מספר המשתתפים."),
    ("Task16 Eval Arrival", "arrival", ["manager", "instructor", "customer"], "כל הפעילויות", "המדריך מגיע לפני תחילת האירוע, בודק את מיקום הפעילות, מסדר ציוד ומוודא שהלקוח יודע מתי הקבוצה נכנסת."),
    ("Task16 Eval Pricing", "pricing", ["manager"], "מחירון דמו", "מחירי הדמו אינם מאושרים מסחרית. תפוס את האור מוצג כ-1200 שקלים עד 60 משתתפים ותוספת דמו לכל משתתף נוסף."),
    ("Task16 Eval Activity", "activity", ["manager", "instructor", "customer"], "קטלוג", "לקבוצה גדולה אפשר להציע תפוס את האור, מירוץ קוד או פעילות יצירה עונתית כמו חנוכיות וסוכה לפי גיל, עונה ותקציב."),
    ("Task16 Eval Proposal", "proposal", ["manager"], "הצעות", "הצעת מחיר צריכה לכלול שם פעילות, כמות משתתפים, מחיר דמו לבדיקה, ציוד נדרש והערה שהטיוטה דורשת אישור מנהל."),
    ("Task16 Eval Policy", "policy", ["manager", "instructor", "customer"], "מדיניות", "המערכת היא לקריאה בלבד עבור AI. מדריך אינו משנה מחיר או פרטי לקוח. לקוח רואה רק מידע שמותר ללקוחות."),
    ("Task16 Eval Instructor Internal", "equipment", ["manager", "instructor"], "מדריכים", "הוראות מדריך פנימיות כוללות בדיקת ציוד גיבוי, מטענים נוספים וספירת ערכות לפני יציאה לאירוע."),
]


def main() -> None:
    cases = load_evaluation_cases("rag/evaluation_fixture_task16_he.json")
    installed = _installed_models()
    report = {"installed_models": sorted(installed), "unavailable_models": [], "results": {}}
    for model in MODELS:
        if model not in installed:
            report["unavailable_models"].append(model)
            continue
        report["results"][model] = _evaluate_model(model, cases)
    print(json.dumps(report, ensure_ascii=False, indent=2))


def _installed_models() -> set[str]:
    response = httpx.get("http://localhost:11434/api/tags", timeout=10.0)
    response.raise_for_status()
    names: set[str] = set()
    for item in response.json().get("models", []):
        name = str(item.get("name", ""))
        names.add(name)
        names.add(name.split(":", 1)[0])
    return names


def _evaluate_model(model: str, cases: list[EvaluationCase]) -> dict:
    client = OllamaEmbeddingClient(model=model)
    uri_prefix = f"{SOURCE_PREFIX}{model}/{uuid4()}"
    inserted_ids: list[str] = []
    try:
        with get_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute("SELECT id FROM users WHERE role = 'manager' ORDER BY id LIMIT 1")
                created_by = cur.fetchone()["id"]
                for index, (title, category, roles, activity, content) in enumerate(DOCUMENTS):
                    metadata = {"category": category, "allowed_roles": roles, "activity": activity}
                    embedding_input = format_document_embedding_input(
                        model=model,
                        document=KnowledgeDocumentText(source_title=title, content=content, metadata=metadata),
                    )
                    embedding = client.embed(embedding_input)
                    cur.execute(
                        """
                        INSERT INTO knowledge_chunks (
                            source_title, source_uri, chunk_index, content, metadata,
                            embedding_model, embedding_dimensions, embedding, content_hash, created_by
                        )
                        VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s, %s::vector, %s, %s)
                        RETURNING id;
                        """,
                        (
                            title,
                            f"{uri_prefix}/{index}",
                            0,
                            content,
                            json.dumps(metadata, ensure_ascii=False),
                            model,
                            len(embedding),
                            _vector_literal(embedding),
                            f"task16-eval-{model}-{index}",
                            created_by,
                        ),
                    )
                    inserted_ids.append(str(cur.fetchone()["id"]))
            conn.commit()
        raw_results = _run_cases(client, model, cases, uri_prefix)
        threshold_values = sorted(set(THRESHOLDS + generate_candidate_thresholds(raw_results)))
        raw_metrics = calculate_raw_metrics(raw_results)
        metrics_at_default = _metrics_for_threshold(raw_results, 0.45)
        thresholds = {str(threshold): _metrics_for_threshold(raw_results, threshold) for threshold in threshold_values}
        failure_reports = {
            str(threshold): [failure.__dict__ for failure in calculate_failure_report(raw_results, threshold)]
            for threshold in THRESHOLDS
        }
        return {
            "temporary_rows": len(inserted_ids),
            "embedding_dimensions": _first_embedding_dimensions(client, model),
            "raw_metrics": raw_metrics.__dict__,
            "metrics_at_0.45": metrics_at_default,
            "thresholds": thresholds,
            "failures_by_explicit_threshold": failure_reports,
        }
    finally:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM knowledge_chunks WHERE source_uri LIKE %s", (f"{uri_prefix}%",))
            conn.commit()


def _run_cases(
    client: OllamaEmbeddingClient,
    model: str,
    cases: list[EvaluationCase],
    uri_prefix: str,
) -> list[tuple[EvaluationCase, list[RetrievalHit]]]:
    output: list[tuple[EvaluationCase, list[RetrievalHit]]] = []
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            for case in cases:
                embedding = client.embed(format_query_embedding_input(model=model, query=case.query))
                rows = knowledge_retrieval_repository.search_knowledge_chunks(
                    cur,
                    query_embedding=embedding,
                    authenticated_role=case.authenticated_role,
                    embedding_model=model,
                    embedding_dimensions=len(embedding),
                    limit=3,
                    max_cosine_distance=None,
                    source_uri_prefix=uri_prefix,
                )
                hits = [
                    RetrievalHit(
                        row["source_title"],
                        (row["metadata"] or {}).get("category"),
                        float(row["distance"]),
                        _is_authorized(case.authenticated_role, row["metadata"] or {}),
                    )
                    for row in rows
                ]
                output.append((case, hits))
    return output


def _metrics_for_threshold(results: list[tuple[EvaluationCase, list[RetrievalHit]]], threshold: float) -> dict:
    return calculate_threshold_metrics(results, threshold).__dict__


def _is_authorized(role: str, metadata: dict) -> bool:
    if role == "manager":
        return True
    allowed_roles = metadata.get("allowed_roles")
    return isinstance(allowed_roles, list) and role in allowed_roles


def _first_embedding_dimensions(client: OllamaEmbeddingClient, model: str) -> int:
    return len(client.embed(format_query_embedding_input(model=model, query="בדיקת ממדים")))


def _vector_literal(values: list[float]) -> str:
    return "[" + ",".join(str(float(value)) for value in values) + "]"


if __name__ == "__main__":
    main()
