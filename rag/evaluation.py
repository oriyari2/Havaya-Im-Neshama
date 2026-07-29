from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path


@dataclass(frozen=True)
class EvaluationCase:
    query: str
    authenticated_role: str
    should_retrieve: bool
    expected_sources: tuple[str, ...] = ()
    expected_category: str | None = None
    forbidden_sources: tuple[str, ...] = ()


@dataclass(frozen=True)
class RetrievalHit:
    source_title: str
    category: str | None
    distance: float
    authorized: bool


@dataclass(frozen=True)
class RawEvaluationMetrics:
    top_1_accuracy: float
    top_3_recall: float
    relevant_first_result_distance_range: tuple[float | None, float | None]
    unrelated_first_result_distance_range: tuple[float | None, float | None]
    relevant_distance_range: tuple[float | None, float | None]
    unrelated_distance_range: tuple[float | None, float | None]
    first_to_second_margin_range: tuple[float | None, float | None]
    unauthorized_retrieval_count: int
    forbidden_retrieval_count: int


@dataclass(frozen=True)
class ThresholdEvaluationMetrics:
    relevant_queries_accepted: int
    relevant_queries_rejected: int
    unrelated_queries_accepted: int
    unrelated_queries_rejected: int
    precision: float
    recall: float
    false_positive_rate: float
    unrelated_rejection_rate: float
    accepted_top_1_accuracy: float
    wrong_top_1_accepted_count: int
    forbidden_source_accepted_count: int
    unauthorized_retrieval_count: int
    first_accepted_expected_count: int


@dataclass(frozen=True)
class EvaluationFailure:
    query: str
    authenticated_role: str
    should_retrieve: bool
    expected_sources: tuple[str, ...]
    forbidden_sources: tuple[str, ...]
    returned_source_titles: tuple[str, ...]
    returned_distances: tuple[float, ...]
    passed_threshold: tuple[bool, ...]
    failure_reason: str


def load_evaluation_cases(path: str | Path) -> list[EvaluationCase]:
    raw = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(raw, list):
        raise ValueError("Evaluation fixture must be a list")
    cases: list[EvaluationCase] = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(f"Evaluation case {index} must be an object")
        query = str(item.get("query", "")).strip()
        role = str(item.get("authenticated_role", "")).strip()
        should_retrieve = item.get("should_retrieve")
        if not query or role not in {"manager", "instructor", "customer"} or not isinstance(should_retrieve, bool):
            raise ValueError(f"Evaluation case {index} is missing required fields")

        expected_sources = _strings(item.get("expected_sources", []))
        legacy_expected_source = item.get("expected_source")
        if legacy_expected_source:
            expected_sources = (*expected_sources, str(legacy_expected_source))
        expected_category = item.get("expected_category")
        forbidden_sources = _strings(item.get("forbidden_sources", []))
        if should_retrieve and not expected_sources and not expected_category:
            raise ValueError(f"Evaluation case {index} needs expected_sources or expected_category")
        if expected_sources and expected_category:
            raise ValueError(f"Evaluation case {index} must not mix expected_sources and expected_category")

        cases.append(
            EvaluationCase(
                query=query,
                authenticated_role=role,
                should_retrieve=should_retrieve,
                expected_sources=expected_sources,
                expected_category=str(expected_category) if expected_category else None,
                forbidden_sources=forbidden_sources,
            )
        )
    return cases


def calculate_raw_metrics(results: list[tuple[EvaluationCase, list[RetrievalHit]]]) -> RawEvaluationMetrics:
    relevant_cases = [item for item in results if item[0].should_retrieve]
    unrelated_cases = [item for item in results if not item[0].should_retrieve]
    top_1 = sum(1 for case, hits in relevant_cases if hits and _matches(case, hits[0]))
    top_3 = sum(1 for case, hits in relevant_cases if any(_matches(case, hit) for hit in hits[:3]))
    relevant_first = [hits[0].distance for _, hits in relevant_cases if hits]
    unrelated_first = [hits[0].distance for _, hits in unrelated_cases if hits]
    relevant_distances = [hit.distance for case, hits in relevant_cases for hit in hits[:3] if _matches(case, hit)]
    unrelated_distances = [hit.distance for _, hits in unrelated_cases for hit in hits[:3]]
    margins = [hits[1].distance - hits[0].distance for _, hits in results if len(hits) > 1]
    unauthorized = sum(1 for _, hits in results for hit in hits if not hit.authorized)
    forbidden = sum(1 for case, hits in results for hit in hits if hit.source_title in case.forbidden_sources)
    return RawEvaluationMetrics(
        top_1_accuracy=_ratio(top_1, len(relevant_cases)),
        top_3_recall=_ratio(top_3, len(relevant_cases)),
        relevant_first_result_distance_range=_range(relevant_first),
        unrelated_first_result_distance_range=_range(unrelated_first),
        relevant_distance_range=_range(relevant_distances),
        unrelated_distance_range=_range(unrelated_distances),
        first_to_second_margin_range=_range(margins),
        unauthorized_retrieval_count=unauthorized,
        forbidden_retrieval_count=forbidden,
    )


def calculate_threshold_metrics(
    results: list[tuple[EvaluationCase, list[RetrievalHit]]],
    threshold: float,
) -> ThresholdEvaluationMetrics:
    filtered = [(case, [hit for hit in hits if hit.distance <= threshold]) for case, hits in results]
    relevant_cases = [item for item in filtered if item[0].should_retrieve]
    unrelated_cases = [item for item in filtered if not item[0].should_retrieve]
    relevant_accepted = sum(1 for case, hits in relevant_cases if any(_matches(case, hit) for hit in hits))
    relevant_rejected = len(relevant_cases) - relevant_accepted
    unrelated_accepted = sum(1 for _, hits in unrelated_cases if hits)
    unrelated_rejected = len(unrelated_cases) - unrelated_accepted
    unauthorized = sum(1 for _, hits in filtered for hit in hits if not hit.authorized)
    forbidden = sum(1 for case, hits in filtered for hit in hits if hit.source_title in case.forbidden_sources)
    accepted_relevant_cases = [(case, hits) for case, hits in relevant_cases if any(_matches(case, hit) for hit in hits)]
    first_expected = sum(1 for case, hits in accepted_relevant_cases if hits and _matches(case, hits[0]))
    wrong_top_1_accepted = sum(1 for case, hits in accepted_relevant_cases if hits and not _matches(case, hits[0]))
    return ThresholdEvaluationMetrics(
        relevant_queries_accepted=relevant_accepted,
        relevant_queries_rejected=relevant_rejected,
        unrelated_queries_accepted=unrelated_accepted,
        unrelated_queries_rejected=unrelated_rejected,
        precision=_ratio(relevant_accepted, relevant_accepted + unrelated_accepted),
        recall=_ratio(relevant_accepted, len(relevant_cases)),
        false_positive_rate=_ratio(unrelated_accepted, len(unrelated_cases)),
        unrelated_rejection_rate=_ratio(unrelated_rejected, len(unrelated_cases)),
        accepted_top_1_accuracy=_ratio(first_expected, len(accepted_relevant_cases)),
        wrong_top_1_accepted_count=wrong_top_1_accepted,
        forbidden_source_accepted_count=forbidden,
        unauthorized_retrieval_count=unauthorized,
        first_accepted_expected_count=first_expected,
    )


def calculate_failure_report(
    results: list[tuple[EvaluationCase, list[RetrievalHit]]],
    threshold: float,
) -> list[EvaluationFailure]:
    failures: list[EvaluationFailure] = []
    for case, hits in results:
        accepted_hits = [hit for hit in hits if hit.distance <= threshold]
        accepted_expected = [hit for hit in accepted_hits if _matches(case, hit)]
        reasons: list[str] = []
        if case.should_retrieve:
            if not accepted_expected:
                reasons.append("expected source did not pass threshold")
            elif accepted_hits and not _matches(case, accepted_hits[0]):
                reasons.append("first accepted result is not an expected source")
        elif accepted_hits:
            reasons.append("unrelated query had accepted retrieval")
        if any(hit.source_title in case.forbidden_sources for hit in accepted_hits):
            reasons.append("forbidden source passed threshold")
        if any(not hit.authorized for hit in accepted_hits):
            reasons.append("unauthorized result passed threshold")
        if reasons:
            failures.append(
                EvaluationFailure(
                    query=case.query,
                    authenticated_role=case.authenticated_role,
                    should_retrieve=case.should_retrieve,
                    expected_sources=case.expected_sources,
                    forbidden_sources=case.forbidden_sources,
                    returned_source_titles=tuple(hit.source_title for hit in hits),
                    returned_distances=tuple(hit.distance for hit in hits),
                    passed_threshold=tuple(hit.distance <= threshold for hit in hits),
                    failure_reason="; ".join(reasons),
                )
            )
    return failures


def generate_candidate_thresholds(results: list[tuple[EvaluationCase, list[RetrievalHit]]]) -> list[float]:
    distances: set[float] = set()
    relevant_distances: list[float] = []
    unrelated_distances: list[float] = []
    for case, hits in results:
        if hits:
            distances.add(hits[0].distance)
        for hit in hits:
            if case.should_retrieve and _matches(case, hit):
                distances.add(hit.distance)
                relevant_distances.append(hit.distance)
            if not case.should_retrieve:
                unrelated_distances.append(hit.distance)
    for relevant in relevant_distances:
        for unrelated in unrelated_distances:
            distances.add((relevant + unrelated) / 2)
    return sorted(round(distance, 6) for distance in distances)


def _matches(case: EvaluationCase, hit: RetrievalHit) -> bool:
    return (
        (bool(case.expected_sources) and hit.source_title in case.expected_sources)
        or (case.expected_category is not None and hit.category == case.expected_category)
    )


def _strings(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(str(item) for item in value if str(item).strip())


def _ratio(count: int, total: int) -> float:
    return 0.0 if total == 0 else count / total


def _range(values: list[float]) -> tuple[float | None, float | None]:
    return (None, None) if not values else (min(values), max(values))
