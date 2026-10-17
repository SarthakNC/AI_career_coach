import json
import uuid
from typing import Any, Dict, List
from unittest.mock import patch, MagicMock
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from main import app
from schemas.assessment import (
    RequirementResultItem,
    PrioritizedGapItem,
    AssessmentRecommendationItem,
)
from services.skill_normalizer import (
    normalize_skill_name,
    are_skills_equivalent,
    skill_keyword_match,
)
from services.assessment_scorer import (
    calculate_match_score,
    prioritize_skill_gaps,
    get_requirement_weight,
    get_status_score,
)
from services.assessment_engine import (
    match_requirement_against_evidence_pool,
    generate_recommendations,
    run_skill_gap_assessment,
)
from services.auth_service import AuthenticatedUser, get_current_user

client = TestClient(app)

USER_A_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
USER_B_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
TOKEN_A = "mock_token_user_a"
TOKEN_B = "mock_token_user_b"


def override_user_a():
    return AuthenticatedUser(user_id=USER_A_ID, token=TOKEN_A, email="usera@test.com")


def override_user_b():
    return AuthenticatedUser(user_id=USER_B_ID, token=TOKEN_B, email="userb@test.com")


# ─── 1. SKILL NORMALIZATION & EQUIVALENCE TESTS ───

def test_skill_normalization_canonical_aliases():
    assert normalize_skill_name("js") == "JavaScript"
    assert normalize_skill_name("React.js") == "React"
    assert normalize_skill_name("Postgres") == "PostgreSQL"
    assert normalize_skill_name("k8s") == "Kubernetes"
    assert normalize_skill_name("python 3.11") == "Python"
    assert normalize_skill_name("restful apis") == "REST API"


def test_are_skills_equivalent_matches():
    assert are_skills_equivalent("JavaScript", "JS")
    assert are_skills_equivalent("reactjs", "React.js")
    assert are_skills_equivalent("PostgreSQL", "postgres")
    assert are_skills_equivalent("TypeScript", "ts")
    assert are_skills_equivalent("FastAPI", "fast-api")


def test_false_friend_protection():
    # Strict check: Java and JavaScript must NEVER be treated as equivalent
    assert not are_skills_equivalent("Java", "JavaScript")
    assert not are_skills_equivalent("C", "C++")
    assert not are_skills_equivalent("C++", "C#")
    assert not are_skills_equivalent("Rust", "Ruby")
    assert not are_skills_equivalent("React", "R")


def test_skill_keyword_matching():
    assert skill_keyword_match("Docker", "Created Dockerfile with multi-stage build.")
    assert skill_keyword_match("FastAPI", "Built REST endpoints with FastAPI router.")
    # Word boundary prevents false match: 'Java' shouldn't match in 'JavaScript'
    assert not skill_keyword_match("Java", "Developed modern frontend using JavaScript and HTML.")


# ─── 2. DETERMINISTIC SCORING TESTS ───

def test_deterministic_scoring_calculation():
    # 3 requirements:
    # 1. Python (Required, weight=1.0) -> demonstrated (score=1.0)
    # 2. Docker (Required, weight=1.0) -> partially_demonstrated (score=0.5)
    # 3. Kubernetes (Preferred, weight=0.5) -> not_demonstrated (score=0.0)
    # Total weight = 1.0 + 1.0 + 0.5 = 2.5
    # Weighted sum = (1.0 * 1.0) + (1.0 * 0.5) + (0.5 * 0.0) = 1.5
    # Match score = 100 * (1.5 / 2.5) = 60.0%
    results = [
        RequirementResultItem(
            skill_name="Python",
            normalized_skill_name="Python",
            category="Programming languages",
            importance="required",
            requirement_weight=1.0,
            status="demonstrated",
            status_score=1.0,
            explanation="Verified",
        ),
        RequirementResultItem(
            skill_name="Docker",
            normalized_skill_name="Docker",
            category="Deployment and DevOps",
            importance="required",
            requirement_weight=1.0,
            status="partially_demonstrated",
            status_score=0.5,
            explanation="Partial",
        ),
        RequirementResultItem(
            skill_name="Kubernetes",
            normalized_skill_name="Kubernetes",
            category="Deployment and DevOps",
            importance="preferred",
            requirement_weight=0.5,
            status="not_demonstrated",
            status_score=0.0,
            explanation="Not found",
        ),
    ]

    score, explanation = calculate_match_score(results)
    assert score == 60.0
    assert explanation.total_requirements == 3
    assert explanation.demonstrated_count == 1
    assert explanation.partially_demonstrated_count == 1
    assert explanation.not_demonstrated_count == 1

    # Verify score contributions
    assert results[0].score_contribution == 40.0  # 1.0 / 2.5 * 100
    assert results[1].score_contribution == 20.0  # 0.5 / 2.5 * 100
    assert results[2].score_contribution == 0.0


def test_scoring_identical_inputs_identical_output():
    results = [
        RequirementResultItem(
            skill_name="FastAPI",
            normalized_skill_name="FastAPI",
            category="Frameworks and libraries",
            importance="required",
            requirement_weight=1.0,
            status="demonstrated",
            status_score=1.0,
            explanation="Verified",
        )
    ]
    score1, exp1 = calculate_match_score(results)
    score2, exp2 = calculate_match_score(results)
    assert score1 == score2 == 100.0


def test_scoring_empty_requirements_returns_none():
    score, explanation = calculate_match_score([])
    assert score is None
    assert explanation.total_requirements == 0


# ─── 3. GAP PRIORITIZATION TESTS ───

def test_prioritize_skill_gaps_order():
    results = [
        RequirementResultItem(
            skill_name="React",
            normalized_skill_name="React",
            category="Frameworks and libraries",
            importance="preferred",
            requirement_weight=0.5,
            status="not_demonstrated",
            status_score=0.0,
            explanation="Not found",
        ),
        RequirementResultItem(
            skill_name="PostgreSQL",
            normalized_skill_name="PostgreSQL",
            category="Databases and data management",
            importance="required",
            requirement_weight=1.0,
            status="not_demonstrated",
            status_score=0.0,
            explanation="Not found",
        ),
        RequirementResultItem(
            skill_name="Docker",
            normalized_skill_name="Docker",
            category="Deployment and DevOps",
            importance="required",
            requirement_weight=1.0,
            status="partially_demonstrated",
            status_score=0.5,
            explanation="Partial",
        ),
    ]

    gaps = prioritize_skill_gaps(results)
    assert len(gaps) == 3
    # 1st: Required + not_demonstrated (PostgreSQL)
    assert gaps[0].skill_name == "PostgreSQL"
    # 2nd: Required + partially_demonstrated (Docker)
    assert gaps[1].skill_name == "Docker"
    # 3rd: Preferred + not_demonstrated (React)
    assert gaps[2].skill_name == "React"


# ─── 4. REQUIREMENT MATCHING ENGINE TESTS ───

def test_match_requirement_strong_evidence():
    req = {
        "id": uuid.uuid4(),
        "skill_name": "Python",
        "category": "Programming languages",
        "importance": "required",
    }
    evidence_pool = [
        {
            "id": uuid.uuid4(),
            "repository_id": uuid.uuid4(),
            "skill_name": "Python",
            "evidence_type": "source_code",
            "status_label": "Strong evidence",
            "evidence_summary": "Extensive Python backend implementation.",
            "file_path": "backend/main.py",
            "confidence": 0.9,
            "commit_sha": "abcdef123456",
        }
    ]

    result = match_requirement_against_evidence_pool(req, evidence_pool, {})
    assert result.status == "demonstrated"
    assert result.status_score == 1.0
    assert len(result.supporting_evidence) == 1


def test_match_requirement_partial_evidence():
    req = {
        "id": uuid.uuid4(),
        "skill_name": "PostgreSQL",
        "category": "Databases and data management",
        "importance": "required",
    }
    evidence_pool = [
        {
            "id": uuid.uuid4(),
            "repository_id": uuid.uuid4(),
            "skill_name": "Postgres",
            "evidence_type": "dependency",
            "status_label": "Some evidence",
            "evidence_summary": "Included psycopg2 dependency in requirements.txt.",
            "file_path": "requirements.txt",
            "confidence": 0.7,
            "commit_sha": "abcdef123456",
        }
    ]

    result = match_requirement_against_evidence_pool(req, evidence_pool, {})
    assert result.status == "partially_demonstrated"
    assert result.status_score == 0.5


def test_match_requirement_no_evidence():
    req = {
        "id": uuid.uuid4(),
        "skill_name": "Kubernetes",
        "category": "Deployment and DevOps",
        "importance": "preferred",
    }
    evidence_pool = []

    result = match_requirement_against_evidence_pool(req, evidence_pool, {})
    assert result.status == "not_demonstrated"
    assert result.status_score == 0.0
    assert len(result.supporting_evidence) == 0
    assert "Absence of evidence" in result.limitations


# ─── 5. RECOMMENDATIONS & ANTI-HALLUCINATION TESTS ───

def test_generate_recommendations_fallback():
    req_id = uuid.uuid4()
    repo_id = uuid.uuid4()
    gaps = [
        PrioritizedGapItem(
            requirement_id=req_id,
            skill_name="Pytest",
            category="Testing and quality assurance",
            importance="required",
            status="not_demonstrated",
            status_score=0.0,
            gap_reason="No tests found.",
            suggested_action="Add unit tests.",
            expected_artifact="tests/test_api.py",
        )
    ]
    repos = [{"id": repo_id, "name": "career-coach", "language": "Python"}]

    recs = generate_recommendations(gaps, repos, "Backend Engineer")
    assert len(recs) >= 1
    # Check that recommendation references actual requirement ID
    assert recs[0].related_requirement_ids == [req_id]
    assert recs[0].related_repository_id == repo_id


# ─── 6. ENDPOINT INTEGRATION & SECURITY TESTS ───

@patch("routes.assessments.get_assessment_options")
def test_get_assessment_options_endpoint(mock_get_options):
    app.dependency_overrides[get_current_user] = override_user_a
    mock_get_options.return_value = {
        "jobs": [
            {
                "id": str(uuid.uuid4()),
                "job_title": "Full Stack Dev",
                "company_name": "Acme",
                "source_url": None,
                "requirement_count": 5,
                "created_at": "2026-10-17T06:00:00Z",
            }
        ],
        "repositories": [
            {
                "id": str(uuid.uuid4()),
                "full_name": "user/repo",
                "name": "repo",
                "language": "Python",
                "latest_analysis_id": str(uuid.uuid4()),
                "last_analyzed_commit_sha": "abc1234",
                "evidence_count": 12,
                "analyzed_at": "2026-10-17T06:00:00Z",
            }
        ],
    }

    res = client.get("/api/v1/assessments/options")
    assert res.status_code == 200
    data = res.json()
    assert len(data["jobs"]) == 1
    assert len(data["repositories"]) == 1
    app.dependency_overrides.clear()


@patch("routes.assessments.get_user_job_by_id")
def test_create_assessment_job_without_requirements_fails(mock_get_job):
    app.dependency_overrides[get_current_user] = override_user_a
    job_id = uuid.uuid4()
    mock_get_job.return_value = {
        "id": str(job_id),
        "job_title": "Empty Job",
        "requirements": [],
    }

    res = client.post(
        "/api/v1/assessments",
        json={"job_id": str(job_id), "repository_ids": [str(uuid.uuid4())]},
    )
    assert res.status_code == 400
    assert "contains no extracted requirements" in res.json()["detail"]
    app.dependency_overrides.clear()


@patch("routes.assessments.get_user_job_by_id")
@patch("routes.assessments.get_user_repository_by_id")
@patch("routes.assessments.get_latest_repository_analysis")
def test_create_assessment_uncompleted_repo_fails(mock_get_analysis, mock_get_repo, mock_get_job):
    app.dependency_overrides[get_current_user] = override_user_a
    job_id = uuid.uuid4()
    repo_id = uuid.uuid4()

    mock_get_job.return_value = {
        "id": str(job_id),
        "job_title": "Dev Job",
        "requirements": [{"id": str(uuid.uuid4()), "skill_name": "Python"}],
    }
    mock_get_repo.return_value = {
        "id": str(repo_id),
        "full_name": "user/repo",
        "name": "repo",
    }
    mock_get_analysis.return_value = None  # No completed analysis

    res = client.post(
        "/api/v1/assessments",
        json={"job_id": str(job_id), "repository_ids": [str(repo_id)]},
    )
    assert res.status_code == 400
    assert "has not been successfully analyzed" in res.json()["detail"]
    app.dependency_overrides.clear()


def test_unauthenticated_assessment_request_rejected():
    res = client.get("/api/v1/assessments/options")
    assert res.status_code in (401, 422)


@patch("routes.assessments.list_user_assessments")
def test_list_assessments_endpoint(mock_list):
    app.dependency_overrides[get_current_user] = override_user_a
    as_id = uuid.uuid4()
    mock_list.return_value = [
        {
            "id": str(as_id),
            "user_id": str(USER_A_ID),
            "job_id": str(uuid.uuid4()),
            "job_title": "AI Engineer",
            "company_name": "Google",
            "selected_repository_ids": [],
            "status": "completed",
            "match_score": 85.0,
            "total_requirements": 10,
            "demonstrated_count": 8,
            "partially_demonstrated_count": 1,
            "not_demonstrated_count": 1,
            "created_at": "2026-10-17T06:00:00Z",
            "completed_at": "2026-10-17T06:01:00Z",
        }
    ]

    res = client.get("/api/v1/assessments")
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 1
    assert items[0]["match_score"] == 85.0
    app.dependency_overrides.clear()


@patch("routes.assessments.get_assessment_by_id")
def test_get_single_assessment_endpoint(mock_get):
    app.dependency_overrides[get_current_user] = override_user_a
    as_id = uuid.uuid4()
    mock_get.return_value = {
        "id": str(as_id),
        "user_id": str(USER_A_ID),
        "job_id": str(uuid.uuid4()),
        "job_title": "Full Stack Dev",
        "company_name": "Stripe",
        "selected_repository_ids": [],
        "repositories_snapshot": [],
        "status": "completed",
        "match_score": 75.0,
        "scoring_method": "weighted_average_v1",
        "total_requirements": 4,
        "demonstrated_count": 3,
        "partially_demonstrated_count": 0,
        "not_demonstrated_count": 1,
        "score_explanation": {
            "method": "weighted_average_v1",
            "match_score": 75.0,
            "total_requirements": 4,
            "demonstrated_count": 3,
            "partially_demonstrated_count": 0,
            "not_demonstrated_count": 1,
            "required_count": 4,
            "preferred_count": 0,
        },
        "created_at": "2026-10-17T06:00:00Z",
        "completed_at": "2026-10-17T06:01:00Z",
        "requirement_results": [],
        "prioritized_gaps": [],
        "recommendations": [],
    }

    res = client.get(f"/api/v1/assessments/{as_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == str(as_id)
    assert data["match_score"] == 75.0
    app.dependency_overrides.clear()


@patch("routes.assessments.delete_assessment")
def test_delete_assessment_endpoint(mock_delete):
    app.dependency_overrides[get_current_user] = override_user_a
    as_id = uuid.uuid4()
    mock_delete.return_value = None

    res = client.delete(f"/api/v1/assessments/{as_id}")
    assert res.status_code == 204
    app.dependency_overrides.clear()


def test_full_pipeline_run_skill_gap_assessment():
    job_id = uuid.uuid4()
    req_py_id = uuid.uuid4()
    req_docker_id = uuid.uuid4()

    job = {
        "id": job_id,
        "job_title": "Senior Python Architect",
        "company_name": "CloudCorp",
        "requirements": [
            {
                "id": req_py_id,
                "skill_name": "Python",
                "category": "Programming languages",
                "importance": "required",
            },
            {
                "id": req_docker_id,
                "skill_name": "Docker",
                "category": "Deployment and DevOps",
                "importance": "preferred",
            },
        ],
    }

    repo_id = uuid.uuid4()
    repos = [
        {
            "id": repo_id,
            "full_name": "octocat/backend-service",
            "name": "backend-service",
            "language": "Python",
            "last_analyzed_commit_sha": "1234567890abcdef",
        }
    ]

    evidence_pool = [
        {
            "id": uuid.uuid4(),
            "repository_id": repo_id,
            "skill_name": "Python",
            "evidence_type": "source_code",
            "status_label": "Strong evidence",
            "evidence_summary": "Core API engine written in Python 3.12.",
            "file_path": "main.py",
            "confidence": 0.95,
            "commit_sha": "1234567890abcdef",
        }
    ]

    assessment = run_skill_gap_assessment(job, repos, evidence_pool, USER_A_ID)
    assert assessment["status"] == "completed"
    assert assessment["total_requirements"] == 2
    assert assessment["demonstrated_count"] == 1
    assert assessment["not_demonstrated_count"] == 1
    # Weight: Python = 1.0 (demo = 1.0), Docker = 0.5 (not demo = 0.0)
    # Total weight = 1.5, score = 100 * (1.0 / 1.5) = 66.7%
    assert assessment["match_score"] == 66.7
    assert len(assessment["prioritized_gaps"]) == 1
    assert assessment["prioritized_gaps"][0].skill_name == "Docker"
    assert len(assessment["recommendations"]) >= 1

