from __future__ import annotations

import json
import sys
from uuid import UUID

from psycopg.rows import dict_row

from backend.app.application.services.knowledge_ingestion_service import KnowledgeIngestionService
from backend.app.application.services.knowledge_retrieval_service import KnowledgeRetrievalService
from backend.app.db.connection import get_connection
from backend.app.schemas.knowledge import KnowledgeIngestRequest
from rag.embedding_client import OllamaEmbeddingClient


MODEL = "nomic-embed-text-v2-moe"
EXPECTED_DIMENSIONS = 768

DOCUMENTS = [
    (
        "Task16 Demo Equipment",
        "demo://knowledge/equipment-guide",
        "equipment",
        ["manager", "instructor", "customer"],
        "תפוס את האור",
        "לפני פעילות תפוס את האור יש לטעון את כל יחידות האור, לבדוק מטענים, סוללות גיבוי וערכות ציוד מלאות.",
    ),
    (
        "Task16 Demo Preparation",
        "demo://knowledge/preparation-guide",
        "preparation",
        ["manager", "instructor", "customer"],
        "סדנאות יצירה",
        "לפני סדנת תיקים או סוכה יש להכין שולחנות עבודה, חומרי יצירה, משטחי עבודה ואריזות לפי מספר המשתתפים.",
    ),
    (
        "Task16 Demo Arrival",
        "demo://knowledge/arrival-guide",
        "arrival",
        ["manager", "instructor", "customer"],
        "כל הפעילויות",
        "המדריך מגיע לפני תחילת האירוע, בודק את מיקום הפעילות, מסדר ציוד ומוודא שהלקוח יודע מתי הקבוצה נכנסת.",
    ),
    (
        "Task16 Demo Pricing",
        "demo://knowledge/internal-pricing",
        "pricing",
        ["manager"],
        "מחירון דמו",
        "מחירי הדמו אינם מאושרים מסחרית. תפוס את האור מוצג כ-1200 שקלים עד 60 משתתפים ותוספת דמו לכל משתתף נוסף.",
    ),
    (
        "Task16 Demo Activity",
        "demo://knowledge/activity-catalog",
        "activity",
        ["manager", "instructor", "customer"],
        "קטלוג",
        "לקבוצה גדולה אפשר להציע תפוס את האור, מירוץ קוד או פעילות יצירה עונתית כמו חנוכיות וסוכה לפי גיל, עונה ותקציב.",
    ),
    (
        "Task16 Demo Proposal",
        "demo://knowledge/internal-proposal",
        "proposal",
        ["manager"],
        "הצעות",
        "הצעת מחיר צריכה לכלול שם פעילות, כמות משתתפים, מחיר דמו לבדיקה, ציוד נדרש והערה שהטיוטה דורשת אישור מנהל.",
    ),
    (
        "Task16 Demo Policy",
        "demo://knowledge/role-policy",
        "policy",
        ["manager", "instructor", "customer"],
        "מדיניות",
        "המערכת היא לקריאה בלבד עבור AI. מדריך אינו משנה מחיר או פרטי לקוח. לקוח רואה רק מידע שמותר ללקוחות.",
    ),
    (
        "Task16 Demo Instructor Internal",
        "demo://knowledge/instructor-equipment",
        "equipment",
        ["manager", "instructor"],
        "מדריכים",
        "הוראות מדריך פנימיות כוללות בדיקת ציוד גיבוי, מטענים נוספים וספירת ערכות לפני יציאה לאירוע.",
    ),
]

RELEVANT_QUERIES = [
    ("instructor", "מה צריך לבדוק לפני פעילות תפוס את האור?"),
    ("customer", "מה ההורים צריכים להכין לפני סדנת תיקים?"),
    ("manager", "מה חשוב לכתוב בהצעת מחיר?"),
]
UNSUPPORTED_QUERIES = [
    ("customer", "איך מתקנים מדפסת לייזר במשרד?"),
    ("manager", "האם אפשר לשלם בתשלומים?"),
]
AUTHORIZATION_QUERIES = [
    ("manager", "מחירי הדמו אינם מאושרים מסחרית"),
    ("instructor", "מחירי הדמו אינם מאושרים מסחרית"),
    ("customer", "הוראות מדריך פנימיות"),
]


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    before_counts = _table_counts()
    deleted_rows = _delete_knowledge_chunks()
    created_by = _manager_id()
    service = KnowledgeIngestionService(OllamaEmbeddingClient(model=MODEL))
    recreated_rows = 0
    for title, uri, category, roles, activity, content in DOCUMENTS:
        result = service.ingest(
            KnowledgeIngestRequest(
                source_title=title,
                source_uri=uri,
                content=content,
                metadata={"category": category, "allowed_roles": roles, "activity": activity},
            ),
            created_by=created_by,
        )
        recreated_rows += result.chunk_count

    after_counts = _table_counts()
    model_rows = _model_dimension_counts()
    service = KnowledgeRetrievalService(OllamaEmbeddingClient(model=MODEL), max_cosine_distance=0.58)
    report = {
        "deleted_rows": deleted_rows,
        "recreated_rows": recreated_rows,
        "model_dimension_counts": model_rows,
        "relevant_query_results": _run_queries(service, RELEVANT_QUERIES),
        "unsupported_query_results": _run_queries(service, UNSUPPORTED_QUERIES),
        "authorization_results": _run_queries(service, AUTHORIZATION_QUERIES),
        "unrelated_table_counts_before": before_counts,
        "unrelated_table_counts_after": after_counts,
        "only_knowledge_chunks_changed": _only_knowledge_chunks_changed(before_counts, after_counts),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


def _table_counts() -> dict[str, int]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            names = ["users", "customers", "activities", "bookings", "booking_events", "knowledge_chunks"]
            counts = {}
            for name in names:
                cur.execute(f"SELECT COUNT(*) FROM {name}")
                counts[name] = cur.fetchone()[0]
    return counts


def _delete_knowledge_chunks() -> int:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM knowledge_chunks")
            deleted = cur.rowcount
        conn.commit()
    return int(deleted)


def _manager_id() -> UUID:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT id FROM users WHERE role = 'manager' ORDER BY id LIMIT 1")
            row = cur.fetchone()
    if not row:
        raise RuntimeError("No manager user exists for knowledge chunk created_by")
    return row["id"]


def _model_dimension_counts() -> list[dict]:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT embedding_model, embedding_dimensions, COUNT(*) AS row_count
                FROM knowledge_chunks
                GROUP BY embedding_model, embedding_dimensions
                ORDER BY embedding_model, embedding_dimensions;
                """
            )
            return list(cur.fetchall())


def _run_queries(service: KnowledgeRetrievalService, queries: list[tuple[str, str]]) -> list[dict]:
    output = []
    for role, query in queries:
        result = service.search(query=query, authenticated_role=role, limit=5)
        output.append(
            {
                "role": role,
                "query": query,
                "results": [
                    {
                        "source_title": item.source_title,
                        "source_uri": item.source_uri,
                        "distance": round(item.distance, 6),
                        "category": item.metadata.get("category"),
                    }
                    for item in result.results
                ],
            }
        )
    return output


def _only_knowledge_chunks_changed(before: dict[str, int], after: dict[str, int]) -> bool:
    return all(before[name] == after[name] for name in before if name != "knowledge_chunks")


if __name__ == "__main__":
    main()
