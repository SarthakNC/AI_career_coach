from typing import Any, Dict, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from services.auth_service import AuthenticatedUser, get_current_user
from services.database_service import get_user_job_by_id
from services.github_db_service import get_user_repository_by_id, get_latest_repository_analysis
from services.assessment_engine import run_skill_gap_assessment
from services.assessment_db_service import (
    get_assessment_options,
    create_assessment_record,
    list_user_assessments,
    get_assessment_by_id,
    delete_assessment,
)
from schemas.assessment import (
    AssessmentCreateRequest,
    AssessmentOptionsResponse,
    AssessmentDetailResponse,
    AssessmentSummaryResponse,
)

router = APIRouter(prefix="/api/v1/assessments", tags=["Skill Gap Assessments"])


@router.get("/options", response_model=AssessmentOptionsResponse, status_code=status.HTTP_200_OK)
def get_options(
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Returns the authenticated user's available analyzed jobs and
    successfully analyzed repositories for running an assessment.
    """
    options = get_assessment_options(
        user_id=current_user.user_id,
        token=current_user.token
    )
    return options


@router.post("", response_model=AssessmentDetailResponse, status_code=status.HTTP_201_CREATED)
def create_assessment(
    request: AssessmentCreateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Executes an AI-powered skill-gap assessment:
    1. Validates job ownership and presence of extracted requirements.
    2. Validates repository ownership and completed analysis runs.
    3. Gathers verified skill evidence across all selected repositories.
    4. Evaluates requirements, normalizes skills, matches evidence.
    5. Calculates explainable, deterministic match score.
    6. Prioritizes skill gaps and generates actionable recommendations.
    7. Persists complete assessment and returns immutable snapshot.
    """
    # 1. Fetch & validate job
    job = get_user_job_by_id(
        job_id=request.job_id,
        user_id=current_user.user_id,
        token=current_user.token
    )
    requirements = job.get("requirements", [])
    if not requirements or len(requirements) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "The selected job posting contains no extracted requirements. "
                "Please analyze a valid job posting in the Job Analysis section before running an assessment."
            )
        )

    # 2. Fetch & validate repositories and completed analysis runs
    selected_repos: List[Dict[str, Any]] = []
    evidence_pool: List[Dict[str, Any]] = []

    for repo_id in request.repository_ids:
        repo = get_user_repository_by_id(
            repo_id=repo_id,
            user_id=current_user.user_id,
            token=current_user.token
        )
        analysis = get_latest_repository_analysis(
            repo_id=repo_id,
            user_id=current_user.user_id,
            token=current_user.token
        )

        if not analysis or analysis.get("status") != "completed":
            repo_name = repo.get("full_name") or repo.get("name") or str(repo_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Repository '{repo_name}' has not been successfully analyzed. "
                    "Please navigate to the GitHub Portfolio page and complete an analysis run for this repository first."
                )
            )

        selected_repos.append(repo)
        repo_evidence = analysis.get("evidence", [])
        evidence_pool.extend(repo_evidence)

    # 3. Run assessment pipeline
    assessment_data = run_skill_gap_assessment(
        job=job,
        repositories=selected_repos,
        evidence_pool=evidence_pool,
        user_id=current_user.user_id
    )

    # 4. Persist assessment record and child tables
    saved_assessment = create_assessment_record(
        user_id=current_user.user_id,
        token=current_user.token,
        assessment_data=assessment_data
    )

    return saved_assessment


@router.get("", response_model=List[AssessmentSummaryResponse], status_code=status.HTTP_200_OK)
def list_assessments(
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Returns a list of saved assessments belonging to the authenticated user.
    """
    return list_user_assessments(
        user_id=current_user.user_id,
        token=current_user.token
    )


@router.get("/{assessment_id}", response_model=AssessmentDetailResponse, status_code=status.HTTP_200_OK)
def get_assessment(
    assessment_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Retrieves full details of a previously completed assessment,
    including requirement results, supporting evidence snapshots,
    prioritized gaps, and recommendations. Reopens without recomputation.
    """
    return get_assessment_by_id(
        assessment_id=assessment_id,
        user_id=current_user.user_id,
        token=current_user.token
    )


@router.delete("/{assessment_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_assessment(
    assessment_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Deletes an assessment and cascades deletion of requirement results
    and recommendations.
    """
    delete_assessment(
        assessment_id=assessment_id,
        user_id=current_user.user_id,
        token=current_user.token
    )
    return None
