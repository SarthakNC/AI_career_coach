import json
import logging
import uuid
from typing import Any, Dict, List, Optional, Set
from uuid import UUID

from schemas.assessment import (
    RequirementResultItem,
    PrioritizedGapItem,
    AssessmentRecommendationItem,
    ScoreExplanation,
    ASSESSMENT_STATUS_LITERAL,
    RECOMMENDATION_PRIORITY_LITERAL
)
from services.skill_normalizer import (
    normalize_skill_name,
    are_skills_equivalent,
    skill_keyword_match
)
from services.assessment_scorer import (
    get_requirement_weight,
    get_status_score,
    calculate_match_score,
    prioritize_skill_gaps
)
from services.llm_service import call_llm_api, clean_llm_json_response

logger = logging.getLogger(__name__)


def match_requirement_against_evidence_pool(
    requirement: Dict[str, Any],
    evidence_pool: List[Dict[str, Any]],
    repo_map: Dict[str, str]
) -> RequirementResultItem:
    """
    Evaluates a single job requirement against verified repository evidence.
    Assigns: 'demonstrated' | 'partially_demonstrated' | 'not_demonstrated'
    """
    req_id = requirement.get("id")
    raw_skill = requirement.get("skill_name", "Unknown")
    category = requirement.get("category", "Core concepts and soft skills")
    importance = requirement.get("importance", "required")
    weight = get_requirement_weight(importance)
    norm_skill = normalize_skill_name(raw_skill)

    matched_evidence: List[Dict[str, Any]] = []

    for ev in evidence_pool:
        ev_skill = ev.get("skill_name", "")
        is_match = False

        # 1. Equivalent skill match
        if are_skills_equivalent(raw_skill, ev_skill):
            is_match = True
        # 2. Keyword match in summary or code excerpt
        elif skill_keyword_match(raw_skill, ev.get("evidence_summary", "") or ""):
            is_match = True
        elif skill_keyword_match(raw_skill, ev.get("code_excerpt", "") or ""):
            is_match = True
        elif skill_keyword_match(raw_skill, ev.get("file_path", "") or ""):
            is_match = True

        if is_match:
            # Attach repository name to evidence snapshot for display
            repo_id_str = str(ev.get("repository_id", ""))
            repo_name = repo_map.get(repo_id_str, "Repository")
            ev_copy = dict(ev)
            ev_copy["repository_name"] = repo_name
            matched_evidence.append(ev_copy)

    # 3. Overarching Competencies Grounded Match (e.g., Software Engineering, Web Development, Programming)
    # If a candidate wrote real code and tests in the repository, overarching engineering requirements
    # are directly supported by their verified source code and test implementations.
    OVERARCHING_COMPETENCIES = {
        "software engineering", "software development", "web development",
        "full stack development", "backend development", "frontend development",
        "programming", "coding", "computer science", "application development",
        "software architecture", "system design"
    }

    is_overarching = norm_skill.lower() in OVERARCHING_COMPETENCIES
    if not matched_evidence and is_overarching and evidence_pool:
        # Prioritize source_code and test items
        candidate_items = [
            ev for ev in evidence_pool
            if ev.get("evidence_type") in ("source_code", "test")
            or ev.get("status_label") in ("Strong evidence", "Some evidence")
        ]
        if not candidate_items:
            candidate_items = evidence_pool

        for ev in candidate_items[:5]:
            repo_id_str = str(ev.get("repository_id", ""))
            repo_name = repo_map.get(repo_id_str, "Repository")
            ev_copy = dict(ev)
            ev_copy["repository_name"] = repo_name
            matched_evidence.append(ev_copy)

    # Determine status based on verified evidence
    if not matched_evidence:
        status: ASSESSMENT_STATUS_LITERAL = "not_demonstrated"
        explanation = (
            f"No verified code, tests, or dependencies for {raw_skill} were detected "
            f"in the analyzed files across the selected repositories."
        )
        limitations = (
            "Absence of evidence in the analyzed repositories does not necessarily mean "
            "the candidate lacks knowledge or capability in this area."
        )
        next_step = f"Build a practical feature or add a test suite demonstrating {raw_skill}."
    else:
        # Check evidence strength
        has_strong = any(
            ev.get("status_label") == "Strong evidence" or
            (ev.get("evidence_type") in ("source_code", "test") and float(ev.get("confidence", 0.8)) >= 0.75)
            for ev in matched_evidence
        )

        first_match = matched_evidence[0]
        first_repo = first_match.get("repository_name", "selected repository")
        first_file = first_match.get("file_path", "source code")

        if has_strong:
            status = "demonstrated"
            if is_overarching:
                explanation = (
                    f"Direct technical evidence for {raw_skill} is demonstrated through verified source code "
                    f"and architecture in {first_repo} ({first_file})."
                )
            else:
                explanation = (
                    f"Direct technical evidence for {raw_skill} was verified in {first_repo} "
                    f"({first_file})."
                )
            limitations = None
            next_step = f"Continue expanding test coverage or modularity for {raw_skill} implementations."
        else:
            status = "partially_demonstrated"
            explanation = (
                f"Partial evidence for {raw_skill} was found in {first_repo} ({first_file}), "
                f"such as configuration or package dependencies, but full direct code implementation is unverified."
            )
            limitations = "Evidence is limited to configuration or high-level reference without full implementation depth."
            next_step = f"Add direct source code logic and unit tests exercising {raw_skill}."

    status_score = get_status_score(status)
    evidence_ids = [UUID(str(ev["id"])) for ev in matched_evidence if ev.get("id")]

    return RequirementResultItem(
        requirement_id=UUID(str(req_id)) if req_id else None,
        skill_name=raw_skill,
        normalized_skill_name=norm_skill,
        category=category,
        importance=importance,
        requirement_weight=weight,
        status=status,
        status_score=status_score,
        score_contribution=0.0,  # Will be populated during score calculation
        explanation=explanation,
        supporting_evidence_ids=evidence_ids,
        supporting_evidence=matched_evidence,
        limitations=limitations,
        suggested_next_step=next_step
    )


def generate_recommendations(
    gaps: List[PrioritizedGapItem],
    repositories: List[Dict[str, Any]],
    job_title: Optional[str] = None
) -> List[AssessmentRecommendationItem]:
    """
    Generates actionable, grounded portfolio improvement recommendations.
    Uses LLM when available, strictly validates against real IDs, and falls
    back gracefully to deterministic rule-based recommendations.
    """
    if not gaps:
        return [
            AssessmentRecommendationItem(
                title="Maintain High Portfolio Quality",
                related_requirement_ids=[],
                related_skills=[],
                priority="low",
                reason="All identified job requirements have direct evidence in the analyzed repositories.",
                suggested_task="Keep dependencies updated and ensure CI/CD workflows run cleanly on new commits.",
                expected_artifact="Automated GitHub Actions workflow badge and green test runs.",
                evidence_to_produce="Clean commit history and continuous integration logs.",
                limitations="Covers requirements extracted from the analyzed job posting."
            )
        ]

    # Map candidate IDs for anti-hallucination verification
    valid_req_ids: Set[str] = {str(g.requirement_id) for g in gaps if g.requirement_id}
    req_skill_map: Dict[str, str] = {str(g.requirement_id): g.skill_name for g in gaps if g.requirement_id}
    valid_repo_ids: Set[str] = {str(r.get("id")) for r in repositories if r.get("id")}
    repo_name_map: Dict[str, str] = {str(r.get("id")): r.get("full_name") or r.get("name") for r in repositories if r.get("id")}

    # Default fallback recommendations if LLM fails or is disabled
    def build_deterministic_recommendations() -> List[AssessmentRecommendationItem]:
        recs: List[AssessmentRecommendationItem] = []
        # Group by top 3 highest priority gaps
        top_gaps = gaps[:4]

        # First repo to suggest enhancements on
        first_repo_id = UUID(str(repositories[0]["id"])) if repositories and repositories[0].get("id") else None
        first_repo_name = repositories[0].get("name", "existing project") if repositories else None

        for idx, gap in enumerate(top_gaps):
            priority: RECOMMENDATION_PRIORITY_LITERAL = "high" if gap.importance.lower() == "required" else "medium"
            req_id_list = [UUID(str(gap.requirement_id))] if gap.requirement_id else []

            if gap.status == "not_demonstrated":
                title = f"Demonstrate {gap.skill_name} in {first_repo_name or 'a targeted module'}"
                task = (
                    f"Create a dedicated module or service implementing {gap.skill_name} with "
                    f"proper error handling and validated request/response models."
                )
                artifact = f"New source files in {first_repo_name or 'repository'} showing functional {gap.skill_name} usage."
                evidence = f"Code commits, unit test cases, and configuration files for {gap.skill_name}."
            else:
                title = f"Deepen {gap.skill_name} Test Coverage & Architecture"
                task = (
                    f"Add automated unit and integration tests covering the existing {gap.skill_name} "
                    f"logic in {first_repo_name or 'the project'}."
                )
                artifact = f"Automated test suite (e.g. pytest or jest) validating {gap.skill_name} integration."
                evidence = f"Passing test run commits and test specification files."

            recs.append(
                AssessmentRecommendationItem(
                    title=title,
                    related_requirement_ids=req_id_list,
                    related_skills=[gap.skill_name],
                    priority=priority,
                    reason=f"Fulfills the {gap.importance} requirement for {gap.skill_name} in '{job_title or 'target job'}'.",
                    suggested_task=task,
                    expected_artifact=artifact,
                    evidence_to_produce=evidence,
                    related_repository_id=first_repo_id,
                    related_repository_name=first_repo_name,
                    estimated_effort="3-5 hours" if priority == "high" else "1-2 hours",
                    limitations="Guidance reflects missing evidence in currently analyzed repository files."
                )
            )
        return recs

    # Attempt LLM-assisted recommendation generation
    try:
        gap_summaries = [
            {
                "requirement_id": str(g.requirement_id),
                "skill_name": g.skill_name,
                "category": g.category,
                "importance": g.importance,
                "status": g.status,
                "gap_reason": g.gap_reason,
            }
            for g in gaps[:5]
        ]
        repo_summaries = [
            {
                "id": str(r.get("id")),
                "name": r.get("name"),
                "language": r.get("language")
            }
            for r in repositories
        ]

        system_prompt = """You are a software engineering career coach and tech lead.
You are generating personalized portfolio improvement recommendations for a developer to bridge skill gaps for a specific job.

CRITICAL CONSTRAINTS:
1. ONLY reference requirement_id values that exist in the provided GAPS list.
2. ONLY reference related_repository_id values that exist in the provided REPOSITORIES list (or null).
3. Do NOT hallucinate technologies or tools unrelated to the job requirements.
4. Prefer enhancing an existing repository where appropriate rather than always creating a new repository.
5. Output clean JSON only with this schema:
{
  "recommendations": [
    {
      "title": "Actionable task title",
      "related_requirement_ids": ["uuid-from-gaps"],
      "priority": "high", // "high" | "medium" | "low"
      "reason": "Why this closes the gap for the target role",
      "suggested_task": "Concrete architectural or coding task",
      "expected_artifact": "Specific file or feature (e.g. tests/test_api.py)",
      "evidence_to_produce": "What code or test to commit",
      "related_repository_id": "uuid-from-repos-or-null",
      "estimated_effort": "2-4 hours"
    }
  ]
}
"""
        user_prompt = f"""Target Job Title: {job_title or 'Software Engineer'}

Gaps to address:
{json.dumps(gap_summaries, indent=2)}

Candidate Repositories:
{json.dumps(repo_summaries, indent=2)}
"""
        llm_response = call_llm_api(
            prompt=system_prompt,
            user_prompt=user_prompt
        )

        parsed_recs: List[AssessmentRecommendationItem] = []
        raw_list = llm_response.get("recommendations", [])
        if isinstance(raw_list, list) and len(raw_list) > 0:
            for item in raw_list:
                # Anti-hallucination validation on requirement IDs
                raw_req_ids = item.get("related_requirement_ids", [])
                safe_req_ids: List[UUID] = []
                safe_skills: List[str] = []
                for rid in raw_req_ids:
                    s_rid = str(rid).strip()
                    if s_rid in valid_req_ids:
                        safe_req_ids.append(UUID(s_rid))
                        if s_rid in req_skill_map:
                            safe_skills.append(req_skill_map[s_rid])

                # Anti-hallucination validation on repo ID
                raw_repo_id = item.get("related_repository_id")
                safe_repo_id: Optional[UUID] = None
                safe_repo_name: Optional[str] = None
                if raw_repo_id and str(raw_repo_id).strip() in valid_repo_ids:
                    s_repo_id = str(raw_repo_id).strip()
                    safe_repo_id = UUID(s_repo_id)
                    safe_repo_name = repo_name_map.get(s_repo_id)

                priority = item.get("priority", "medium").lower()
                if priority not in ("high", "medium", "low"):
                    priority = "medium"

                parsed_recs.append(
                    AssessmentRecommendationItem(
                        title=item.get("title") or "Improve Portfolio Coverage",
                        related_requirement_ids=safe_req_ids,
                        related_skills=safe_skills,
                        priority=priority,
                        reason=item.get("reason") or "Directly addresses unverified skill requirements.",
                        suggested_task=item.get("suggested_task") or "Implement feature and tests.",
                        expected_artifact=item.get("expected_artifact") or "Source code and tests.",
                        evidence_to_produce=item.get("evidence_to_produce") or "Git commit with verified tests.",
                        related_repository_id=safe_repo_id,
                        related_repository_name=safe_repo_name,
                        estimated_effort=item.get("estimated_effort") or "2-4 hours",
                        limitations="Recommendation is based on analyzed job description and selected repository files."
                    )
                )

        if parsed_recs:
            return parsed_recs
        else:
            return build_deterministic_recommendations()

    except Exception as e:
        logger.warning(f"LLM recommendation generation failed, falling back to deterministic recommendations: {str(e)}")
        return build_deterministic_recommendations()


def run_skill_gap_assessment(
    job: Dict[str, Any],
    repositories: List[Dict[str, Any]],
    evidence_pool: List[Dict[str, Any]],
    user_id: UUID
) -> Dict[str, Any]:
    """
    Executes complete AI-Powered Skill-Gap Assessment pipeline:
    1. Evaluates all job requirements against repository evidence.
    2. Calculates explainable, deterministic match score.
    3. Prioritizes skill gaps.
    4. Generates validated, actionable recommendations.
    5. Assembles immutable result snapshot ready for persistence.
    """
    job_id = UUID(str(job["id"]))
    job_title = job.get("job_title", "Software Engineer")
    company_name = job.get("company_name", "Target Company")
    requirements = job.get("requirements", [])

    # Map repository IDs to names for evidence tagging
    repo_map: Dict[str, str] = {
        str(r["id"]): r.get("full_name") or r.get("name") or "Repository"
        for r in repositories
    }

    # 1. Match each requirement against evidence using RAG + fallback
    requirement_results: List[RequirementResultItem] = []
    selected_repo_uuids = [UUID(str(r["id"])) for r in repositories if r.get("id")]

    for req in requirements:
        skill_name = req.get("skill_name", "")
        category = req.get("category", "")
        desc = req.get("description", "") or req.get("source_excerpt", "")

        # Semantic retrieval from ChromaDB
        retrieved_chunks = []
        try:
            from services.rag_vector_service import retrieve_evidence_for_skill
            retrieved_chunks = retrieve_evidence_for_skill(
                user_id=user_id,
                repository_ids=selected_repo_uuids,
                skill_name=skill_name,
                category=category,
                query_context=desc,
                top_k=4
            )
        except Exception as e:
            logger.warning(f"RAG retrieval skipped for skill '{skill_name}': {e}")

        # If chunks found via RAG, evaluate with RAG evaluator
        if retrieved_chunks and any(c.get("relevance_score", 0.0) >= 0.25 for c in retrieved_chunks):
            from services.rag_assessment_evaluator import evaluate_requirement_with_rag
            result_item = evaluate_requirement_with_rag(req, retrieved_chunks, repo_map)
        else:
            # Fallback to static evidence pool matching
            result_item = match_requirement_against_evidence_pool(req, evidence_pool, repo_map)

        requirement_results.append(result_item)

    # 2. Deterministic Scoring
    match_score, score_explanation = calculate_match_score(requirement_results)

    # 3. Prioritize Gaps
    prioritized_gaps = prioritize_skill_gaps(requirement_results)

    # 4. Generate Grounded Recommendations
    recommendations = generate_recommendations(
        gaps=prioritized_gaps,
        repositories=repositories,
        job_title=job_title
    )

    # Repositories snapshot for immutable historical record
    repo_snapshots = [
        {
            "id": str(r["id"]),
            "full_name": r.get("full_name"),
            "name": r.get("name"),
            "language": r.get("language"),
            "last_analyzed_commit_sha": r.get("last_analyzed_commit_sha"),
        }
        for r in repositories
    ]

    selected_repo_ids = [UUID(str(r["id"])) for r in repositories]

    return {
        "job_id": job_id,
        "job_title": job_title,
        "company_name": company_name,
        "selected_repository_ids": selected_repo_ids,
        "repositories_snapshot": repo_snapshots,
        "status": "completed",
        "match_score": match_score,
        "scoring_method": score_explanation.method,
        "total_requirements": score_explanation.total_requirements,
        "demonstrated_count": score_explanation.demonstrated_count,
        "partially_demonstrated_count": score_explanation.partially_demonstrated_count,
        "not_demonstrated_count": score_explanation.not_demonstrated_count,
        "score_explanation": score_explanation.model_dump(),
        "assessment_limitations": (
            "Assessment reflects directly verifiable technical evidence extracted from "
            "analyzed repositories. Absence of evidence does not indicate lack of competence."
        ),
        "requirement_results": requirement_results,
        "prioritized_gaps": prioritized_gaps,
        "recommendations": recommendations,
    }
