from typing import Any, Dict, List, Optional, Tuple
from schemas.assessment import (
    RequirementResultItem,
    PrioritizedGapItem,
    ScoreExplanation,
    ASSESSMENT_STATUS_LITERAL,
    RECOMMENDATION_PRIORITY_LITERAL
)

# Standard deterministic scoring parameters
WEIGHT_MAPPING: Dict[str, float] = {
    "required": 1.0,
    "preferred": 0.5,
}
DEFAULT_WEIGHT: float = 1.0

STATUS_SCORE_MAPPING: Dict[ASSESSMENT_STATUS_LITERAL, float] = {
    "demonstrated": 1.0,
    "partially_demonstrated": 0.5,
    "not_demonstrated": 0.0,
}


def get_requirement_weight(importance: Optional[str]) -> float:
    """Returns normalized weight for requirement importance."""
    if not importance:
        return DEFAULT_WEIGHT
    clean = importance.strip().lower()
    return WEIGHT_MAPPING.get(clean, DEFAULT_WEIGHT)


def get_status_score(status: ASSESSMENT_STATUS_LITERAL) -> float:
    """Returns numerical score corresponding to evidence status."""
    return STATUS_SCORE_MAPPING.get(status, 0.0)


def calculate_match_score(
    results: List[RequirementResultItem]
) -> Tuple[Optional[float], ScoreExplanation]:
    """
    Computes explainable, deterministic portfolio match score.
    Formula:
        match_score = 100 * sum(weight * status_score) / sum(weight)

    Returns:
        (match_score, score_explanation)
    """
    if not results:
        explanation = ScoreExplanation(
            method="weighted_average_v1",
            match_score=None,
            total_requirements=0,
            demonstrated_count=0,
            partially_demonstrated_count=0,
            not_demonstrated_count=0,
            required_count=0,
            preferred_count=0,
            required_demonstrated_ratio=None,
            methodology_note="No valid job requirements were available to assess."
        )
        return None, explanation

    total_weight = 0.0
    weighted_sum = 0.0

    demonstrated_count = 0
    partially_demonstrated_count = 0
    not_demonstrated_count = 0

    required_count = 0
    preferred_count = 0
    required_demonstrated_count = 0

    for res in results:
        weight = res.requirement_weight if res.requirement_weight > 0 else DEFAULT_WEIGHT
        total_weight += weight
        weighted_sum += weight * res.status_score

        if res.status == "demonstrated":
            demonstrated_count += 1
        elif res.status == "partially_demonstrated":
            partially_demonstrated_count += 1
        else:
            not_demonstrated_count += 1

        is_required = res.importance.lower() == "required"
        if is_required:
            required_count += 1
            if res.status == "demonstrated":
                required_demonstrated_count += 1
        else:
            preferred_count += 1

    if total_weight <= 0:
        return None, ScoreExplanation(
            method="weighted_average_v1",
            match_score=None,
            total_requirements=len(results),
            demonstrated_count=demonstrated_count,
            partially_demonstrated_count=partially_demonstrated_count,
            not_demonstrated_count=not_demonstrated_count,
            required_count=required_count,
            preferred_count=preferred_count,
        )

    # Calculate overall match score rounded to 1 decimal place
    raw_score = (weighted_sum / total_weight) * 100.0
    match_score = round(raw_score, 1)

    # Populate individual score contribution in results
    for res in results:
        res.score_contribution = round(
            100.0 * (res.requirement_weight * res.status_score) / total_weight,
            2
        )

    required_ratio = round(required_demonstrated_count / required_count, 2) if required_count > 0 else None

    explanation = ScoreExplanation(
        method="weighted_average_v1",
        match_score=match_score,
        total_requirements=len(results),
        demonstrated_count=demonstrated_count,
        partially_demonstrated_count=partially_demonstrated_count,
        not_demonstrated_count=not_demonstrated_count,
        required_count=required_count,
        preferred_count=preferred_count,
        required_demonstrated_ratio=required_ratio,
        methodology_note=(
            "Deterministic portfolio evidence match score reflecting directly verifiable "
            "evidence found in analyzed repository files. It does not measure personal ability or guarantee employment."
        )
    )

    return match_score, explanation


def prioritize_skill_gaps(
    results: List[RequirementResultItem]
) -> List[PrioritizedGapItem]:
    """
    Ranks unfulfilled and partially fulfilled requirements deterministically.
    Gaps are ordered by:
        1. Requirement importance ('required' > 'preferred')
        2. Status ('not_demonstrated' > 'partially_demonstrated')
        3. Weight (higher weight first)
        4. Alphabetical tie-breaker
    """
    gaps: List[PrioritizedGapItem] = []

    for item in results:
        if item.status in ("not_demonstrated", "partially_demonstrated"):
            # Determine existing evidence summary
            evidence_summary = None
            if item.supporting_evidence:
                first_ev = item.supporting_evidence[0]
                evidence_summary = first_ev.get("evidence_summary") or f"Found in {first_ev.get('file_path', 'repo')}"

            # Provide clear gap reason
            if item.status == "not_demonstrated":
                gap_reason = (
                    f"No direct code, test, or dependency evidence for {item.skill_name} "
                    f"was detected across the analyzed repositories."
                )
                action = f"Build a practical module, integration, or feature implementing {item.skill_name}."
                artifact = f"Code files and tests clearly demonstrating {item.skill_name} usage and architecture."
            else:
                gap_reason = (
                    f"Partial evidence exists for {item.skill_name}, but it lacks direct implementation depth "
                    f"or comprehensive testing in the analyzed files."
                )
                action = f"Deepen {item.skill_name} implementation with unit/integration tests and error handling."
                artifact = f"Production-grade test suite and documented implementation of {item.skill_name}."

            gaps.append(
                PrioritizedGapItem(
                    requirement_id=item.requirement_id,
                    skill_name=item.skill_name,
                    category=item.category,
                    importance=item.importance,
                    status=item.status,
                    status_score=item.status_score,
                    gap_reason=gap_reason,
                    existing_evidence_summary=evidence_summary,
                    suggested_action=action,
                    expected_artifact=artifact
                )
            )

    # Sort gaps
    def gap_sort_key(g: PrioritizedGapItem):
        importance_rank = 0 if g.importance.lower() == "required" else 1
        status_rank = 0 if g.status == "not_demonstrated" else 1
        return (importance_rank, status_rank, g.status_score, g.skill_name.lower())

    gaps.sort(key=gap_sort_key)
    return gaps
