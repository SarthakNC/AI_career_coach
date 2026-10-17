from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID
import httpx
from fastapi import HTTPException, status
from services.database_service import get_user_headers, get_rest_base_url
from schemas.assessment import (
    AssessmentOptionsResponse,
    AssessmentOptionJob,
    AssessmentOptionRepo,
    RequirementResultItem,
    PrioritizedGapItem,
    AssessmentRecommendationItem,
    ScoreExplanation
)


def get_assessment_options(user_id: UUID, token: str) -> Dict[str, Any]:
    """
    Retrieves available analyzed jobs and successfully analyzed repositories
    for the authenticated user.
    """
    base_url = get_rest_base_url()
    headers = get_user_headers(token)

    try:
        with httpx.Client(timeout=10.0) as client:
            # 1. Fetch user's analyzed jobs with requirements count
            jobs_url = f"{base_url}/jobs?user_id=eq.{str(user_id)}&select=id,job_title,company_name,source_url,created_at,job_requirements(id)&order=created_at.desc"
            jobs_res = client.get(jobs_url, headers=headers)
            if jobs_res.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to fetch jobs for assessment options: {jobs_res.text}"
                )
            raw_jobs = jobs_res.json()
            available_jobs = []
            for j in raw_jobs:
                reqs = j.pop("job_requirements", [])
                req_count = len(reqs) if isinstance(reqs, list) else 0
                available_jobs.append({
                    "id": j["id"],
                    "job_title": j.get("job_title") or "Untitled Role",
                    "company_name": j.get("company_name") or "Unknown Company",
                    "source_url": j.get("source_url"),
                    "requirement_count": req_count,
                    "created_at": j.get("created_at")
                })

            # 2. Fetch user's analyzed repositories with latest completed analysis run
            repos_url = f"{base_url}/repositories?user_id=eq.{str(user_id)}&select=id,full_name,name,language,last_analyzed_commit_sha,analysis_runs(id,commit_sha,status,evidence_count,created_at,completed_at)&order=updated_at.desc"
            repos_res = client.get(repos_url, headers=headers)
            if repos_res.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to fetch repositories for assessment options: {repos_res.text}"
                )
            raw_repos = repos_res.json()
            available_repos = []
            for r in raw_repos:
                runs = r.pop("analysis_runs", [])
                # Filter for completed runs
                completed_runs = [run for run in runs if run.get("status") == "completed"]
                if completed_runs:
                    completed_runs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
                    latest_run = completed_runs[0]
                    available_repos.append({
                        "id": r["id"],
                        "full_name": r.get("full_name"),
                        "name": r.get("name"),
                        "language": r.get("language"),
                        "latest_analysis_id": latest_run.get("id"),
                        "last_analyzed_commit_sha": latest_run.get("commit_sha") or r.get("last_analyzed_commit_sha"),
                        "evidence_count": latest_run.get("evidence_count", 0),
                        "analyzed_at": latest_run.get("completed_at") or latest_run.get("created_at")
                    })

            return {
                "jobs": available_jobs,
                "repositories": available_repos
            }

    except HTTPException:
        raise
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection error: {str(e)}"
        )


def create_assessment_record(
    user_id: UUID,
    token: str,
    assessment_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Persists the assessment header, requirement results, and recommendations
    into Supabase using RLS-scoped user token.
    """
    base_url = get_rest_base_url()
    headers = get_user_headers(token)

    completed_time = datetime.now(timezone.utc).isoformat()

    assessment_payload = {
        "user_id": str(user_id),
        "job_id": str(assessment_data["job_id"]),
        "job_title": assessment_data.get("job_title"),
        "company_name": assessment_data.get("company_name"),
        "selected_repository_ids": [str(rid) for rid in assessment_data["selected_repository_ids"]],
        "repositories_snapshot": assessment_data.get("repositories_snapshot", []),
        "status": assessment_data.get("status", "completed"),
        "match_score": assessment_data.get("match_score"),
        "scoring_method": assessment_data.get("scoring_method", "weighted_average_v1"),
        "total_requirements": assessment_data.get("total_requirements", 0),
        "demonstrated_count": assessment_data.get("demonstrated_count", 0),
        "partially_demonstrated_count": assessment_data.get("partially_demonstrated_count", 0),
        "not_demonstrated_count": assessment_data.get("not_demonstrated_count", 0),
        "score_explanation": assessment_data.get("score_explanation", {}),
        "assessment_limitations": assessment_data.get("assessment_limitations"),
        "completed_at": completed_time,
    }

    try:
        with httpx.Client(timeout=15.0) as client:
            # 1. Insert assessment
            res_as = client.post(f"{base_url}/assessments", json=assessment_payload, headers=headers)
            if res_as.status_code not in (200, 201):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to save assessment record: {res_as.text}"
                )
            created_assessment = res_as.json()[0]
            assessment_id = created_assessment["id"]

            # 2. Bulk insert requirement results
            req_results: List[RequirementResultItem] = assessment_data.get("requirement_results", [])
            req_payloads = [
                {
                    "assessment_id": assessment_id,
                    "requirement_id": str(rr.requirement_id) if rr.requirement_id else None,
                    "user_id": str(user_id),
                    "skill_name": rr.skill_name,
                    "normalized_skill_name": rr.normalized_skill_name,
                    "category": rr.category,
                    "importance": rr.importance,
                    "requirement_weight": rr.requirement_weight,
                    "status": rr.status,
                    "status_score": rr.status_score,
                    "score_contribution": rr.score_contribution,
                    "explanation": rr.explanation,
                    "supporting_evidence_ids": [str(eid) for eid in rr.supporting_evidence_ids],
                    "supporting_evidence": rr.supporting_evidence,
                    "limitations": rr.limitations,
                    "suggested_next_step": rr.suggested_next_step,
                }
                for rr in req_results
            ]

            saved_reqs = []
            if req_payloads:
                res_reqs = client.post(f"{base_url}/assessment_requirement_results", json=req_payloads, headers=headers)
                if res_reqs.status_code not in (200, 201):
                    # Clean up orphaned assessment
                    client.delete(f"{base_url}/assessments?id=eq.{assessment_id}", headers=headers)
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Failed to save requirement results: {res_reqs.text}"
                    )
                saved_reqs = res_reqs.json()

            # 3. Bulk insert recommendations
            recommendations: List[AssessmentRecommendationItem] = assessment_data.get("recommendations", [])
            rec_payloads = [
                {
                    "assessment_id": assessment_id,
                    "user_id": str(user_id),
                    "title": rec.title,
                    "related_requirement_ids": [str(rid) for rid in rec.related_requirement_ids],
                    "related_skills": rec.related_skills,
                    "priority": rec.priority,
                    "reason": rec.reason,
                    "suggested_task": rec.suggested_task,
                    "expected_artifact": rec.expected_artifact,
                    "evidence_to_produce": rec.evidence_to_produce,
                    "related_repository_id": str(rec.related_repository_id) if rec.related_repository_id else None,
                    "related_repository_name": rec.related_repository_name,
                    "estimated_effort": rec.estimated_effort,
                    "limitations": rec.limitations,
                }
                for rec in recommendations
            ]

            saved_recs = []
            if rec_payloads:
                res_recs = client.post(f"{base_url}/assessment_recommendations", json=rec_payloads, headers=headers)
                if res_recs.status_code in (200, 201):
                    saved_recs = res_recs.json()

            created_assessment["requirement_results"] = saved_reqs
            created_assessment["prioritized_gaps"] = [g.model_dump() for g in assessment_data.get("prioritized_gaps", [])]
            created_assessment["recommendations"] = saved_recs
            return created_assessment

    except HTTPException:
        raise
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection error: {str(e)}"
        )


def list_user_assessments(user_id: UUID, token: str) -> List[Dict[str, Any]]:
    """Lists summary of all saved assessments belonging to the user."""
    base_url = get_rest_base_url()
    headers = get_user_headers(token)

    url = f"{base_url}/assessments?user_id=eq.{str(user_id)}&order=created_at.desc&select=id,user_id,job_id,job_title,company_name,selected_repository_ids,status,match_score,total_requirements,demonstrated_count,partially_demonstrated_count,not_demonstrated_count,created_at,completed_at"

    try:
        with httpx.Client(timeout=10.0) as client:
            res = client.get(url, headers=headers)
            if res.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to fetch assessments: {res.text}"
                )
            return res.json()
    except HTTPException:
        raise
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection error: {str(e)}"
        )


def get_assessment_by_id(assessment_id: UUID, user_id: UUID, token: str) -> Dict[str, Any]:
    """
    Retrieves complete assessment details, requirement results with evidence snapshots,
    and recommendations. Enforces user ownership.
    """
    base_url = get_rest_base_url()
    headers = get_user_headers(token)

    as_url = f"{base_url}/assessments?id=eq.{str(assessment_id)}&user_id=eq.{str(user_id)}&select=*"

    try:
        with httpx.Client(timeout=10.0) as client:
            res = client.get(as_url, headers=headers)
            if res.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to fetch assessment: {res.text}"
                )
            items = res.json()
            if not items:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Assessment not found or access denied."
                )
            assessment = items[0]

            # Fetch requirement results
            reqs_url = f"{base_url}/assessment_requirement_results?assessment_id=eq.{str(assessment_id)}&order=created_at.asc&select=*"
            res_reqs = client.get(reqs_url, headers=headers)
            requirement_results = res_reqs.json() if res_reqs.status_code == 200 else []

            # Fetch recommendations
            recs_url = f"{base_url}/assessment_recommendations?assessment_id=eq.{str(assessment_id)}&order=created_at.asc&select=*"
            res_recs = client.get(recs_url, headers=headers)
            recommendations = res_recs.json() if res_recs.status_code == 200 else []

            # Build prioritized gaps from requirement_results
            from services.assessment_scorer import prioritize_skill_gaps
            from schemas.assessment import RequirementResultItem

            pydantic_reqs = [
                RequirementResultItem(
                    requirement_id=rr.get("requirement_id"),
                    skill_name=rr.get("skill_name"),
                    normalized_skill_name=rr.get("normalized_skill_name"),
                    category=rr.get("category"),
                    importance=rr.get("importance", "required"),
                    requirement_weight=float(rr.get("requirement_weight", 1.0)),
                    status=rr.get("status"),
                    status_score=float(rr.get("status_score", 0.0)),
                    score_contribution=float(rr.get("score_contribution", 0.0)),
                    explanation=rr.get("explanation"),
                    supporting_evidence_ids=rr.get("supporting_evidence_ids") or [],
                    supporting_evidence=rr.get("supporting_evidence") or [],
                    limitations=rr.get("limitations"),
                    suggested_next_step=rr.get("suggested_next_step")
                )
                for rr in requirement_results
            ]
            prioritized_gaps = prioritize_skill_gaps(pydantic_reqs)

            assessment["requirement_results"] = requirement_results
            assessment["prioritized_gaps"] = [g.model_dump() for g in prioritized_gaps]
            assessment["recommendations"] = recommendations

            return assessment

    except HTTPException:
        raise
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection error: {str(e)}"
        )


def delete_assessment(assessment_id: UUID, user_id: UUID, token: str) -> None:
    """Deletes an assessment belonging to the authenticated user."""
    # First verify ownership
    get_assessment_by_id(assessment_id, user_id, token)

    base_url = get_rest_base_url()
    headers = get_user_headers(token)

    url = f"{base_url}/assessments?id=eq.{str(assessment_id)}&user_id=eq.{str(user_id)}"

    try:
        with httpx.Client(timeout=10.0) as client:
            res = client.delete(url, headers=headers)
            if res.status_code not in (200, 204):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to delete assessment: {res.text}"
                )
    except HTTPException:
        raise
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection error: {str(e)}"
        )
