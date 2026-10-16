import pytest
from uuid import uuid4
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException

from main import app
from schemas.job import LLMJobExtractionResult, LLMExtractedRequirement
from services.job_analyzer import normalize_requirements
from services.job_fetcher import is_ip_allowed, validate_url_safety
from services.job_text_extractor import extract_clean_job_text
from services.auth_service import get_current_user, AuthenticatedUser
from services.database_service import get_user_job_by_id

client = TestClient(app)

# Dummy test user
USER_A_ID = uuid4()
USER_B_ID = uuid4()
TOKEN_A = "test-token-a"
TOKEN_B = "test-token-b"

user_a = AuthenticatedUser(user_id=USER_A_ID, email="user_a@example.com", token=TOKEN_A)
user_b = AuthenticatedUser(user_id=USER_B_ID, email="user_b@example.com", token=TOKEN_B)


@pytest.fixture
def override_user_a():
    app.dependency_overrides[get_current_user] = lambda: user_a
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def override_user_b():
    app.dependency_overrides[get_current_user] = lambda: user_b
    yield
    app.dependency_overrides.pop(get_current_user, None)


# 1. URL Safety & SSRF Tests
def test_ssrf_ip_filtering():
    assert is_ip_allowed("127.0.0.1") is False
    assert is_ip_allowed("10.0.0.1") is False
    assert is_ip_allowed("192.168.1.1") is False
    assert is_ip_allowed("172.16.0.1") is False
    assert is_ip_allowed("169.254.169.254") is False
    assert is_ip_allowed("8.8.8.8") is True
    assert is_ip_allowed("1.1.1.1") is True


def test_invalid_url_schemes():
    with pytest.raises(HTTPException) as exc:
        validate_url_safety("ftp://example.com/job")
    assert exc.value.status_code == 400

    with pytest.raises(HTTPException) as exc:
        validate_url_safety("http://localhost:8000/job")
    assert exc.value.status_code == 400


# 2. Text Extractor Tests
def test_extract_clean_job_text_success():
    html = """
    <html>
        <head><title>Job</title><style>.test{color:red}</style></head>
        <body>
            <nav>Nav links</nav>
            <div class="job-description">
                <h1>Backend Engineer</h1>
                <p>We are seeking a Backend Engineer with strong Python and FastAPI experience.</p>
                <p>Must have 2+ years working with PostgreSQL, Docker, and REST APIs.</p>
                <p>Experience with unit testing and CI/CD pipelines is required.</p>
                <p>Strong problem solving and team communication skills are essential.</p>
            </div>
            <footer>Copyright 2026</footer>
        </body>
    </html>
    """
    cleaned = extract_clean_job_text(html)
    assert "Backend Engineer" in cleaned
    assert "FastAPI" in cleaned
    assert "Nav links" not in cleaned
    assert "Copyright" not in cleaned


def test_extract_insufficient_job_text():
    html = "<html><body><p>Short text</p></body></html>"
    with pytest.raises(HTTPException) as exc:
        extract_clean_job_text(html)
    assert exc.value.status_code == 400
    assert "sufficient" in exc.value.detail.lower()


# 3. Requirement Normalization Tests
def test_duplicate_requirement_normalization():
    reqs = [
        LLMExtractedRequirement(
            skill_name="Python",
            category="Programming languages",
            importance="preferred",
            description="Write scripts",
            source_excerpt="Python is nice"
        ),
        LLMExtractedRequirement(
            skill_name="python",
            category="Programming languages",
            importance="required",
            description="Build scalable microservices and asynchronous workers",
            source_excerpt="3+ years production experience with Python required"
        ),
        LLMExtractedRequirement(
            skill_name="PostgreSQL",
            category="Databases and data management",
            importance="required",
            description="Manage relational schemas",
            source_excerpt="PostgreSQL knowledge"
        )
    ]
    normalized = normalize_requirements(reqs)
    assert len(normalized) == 2
    py_req = next(r for r in normalized if r.skill_name.lower() == "python")
    # 'required' should take precedence over 'preferred'
    assert py_req.importance == "required"
    assert "scalable microservices" in py_req.description


# 4. Analyze Endpoint with Pasted Description
@patch("routes.jobs.analyze_job_workflow")
@patch("routes.jobs.save_job_and_requirements")
def test_analyze_job_success(mock_save, mock_workflow, override_user_a):
    job_id = uuid4()
    mock_workflow.return_value = (
        "We need a Python engineer with Docker experience.",
        LLMJobExtractionResult(
            job_title="Software Engineer",
            company_name="Acme Corp",
            summary="Exciting opportunity for a software engineer.",
            requirements=[
                LLMExtractedRequirement(
                    skill_name="Python",
                    category="Programming languages",
                    importance="required",
                    description="Core backend language",
                    source_excerpt="Python experience required"
                )
            ]
        )
    )

    mock_save.return_value = {
        "id": job_id,
        "user_id": USER_A_ID,
        "job_title": "Software Engineer",
        "company_name": "Acme Corp",
        "source_url": None,
        "description": "We need a Python engineer with Docker experience.",
        "summary": "Exciting opportunity for a software engineer.",
        "created_at": "2026-10-16T20:00:00Z",
        "updated_at": "2026-10-16T20:00:00Z",
        "requirements": [
            {
                "id": uuid4(),
                "job_id": job_id,
                "skill_name": "Python",
                "category": "Programming languages",
                "importance": "required",
                "description": "Core backend language",
                "source_excerpt": "Python experience required",
                "created_at": "2026-10-16T20:00:00Z"
            }
        ]
    }

    res = client.post(
        "/api/v1/jobs/analyze",
        headers={"Authorization": f"Bearer {TOKEN_A}"},
        json={
            "pasted_description": "We need a Python engineer with Docker experience to develop backend APIs.",
            "job_title": "Software Engineer",
            "company_name": "Acme Corp"
        }
    )
    assert res.status_code == 201
    data = res.json()
    assert data["job_title"] == "Software Engineer"
    assert len(data["requirements"]) == 1
    assert data["requirements"][0]["skill_name"] == "Python"


# 5. Missing / Empty Description Error
def test_analyze_job_insufficient_description(override_user_a):
    res = client.post(
        "/api/v1/jobs/analyze",
        headers={"Authorization": f"Bearer {TOKEN_A}"},
        json={
            "pasted_description": "too short"
        }
    )
    assert res.status_code == 400


# 6. Unauthenticated Access
def test_unauthenticated_request():
    res = client.get("/api/v1/jobs")
    assert res.status_code == 401 or res.status_code == 422


# 7. User Isolation: User A accessing User B's Job
def test_user_a_cannot_access_user_b_job_direct():
    job_id = uuid4()
    with patch("services.database_service.get_rest_base_url", return_value="https://test.supabase.co/rest/v1"), \
         patch("httpx.Client.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{
            "id": str(job_id),
            "user_id": str(USER_B_ID),
            "job_title": "Secret Job",
            "company_name": "Secret Inc",
            "source_url": None,
            "description": "Secret description",
            "summary": "Secret",
            "created_at": "2026-10-16T20:00:00Z",
            "updated_at": "2026-10-16T20:00:00Z",
            "job_requirements": []
        }]
        mock_get.return_value = mock_response

        with pytest.raises(HTTPException) as exc:
            get_user_job_by_id(job_id=job_id, user_id=USER_A_ID, token=TOKEN_A)
        assert exc.value.status_code == 403
        assert "permission" in exc.value.detail.lower()


@patch("routes.jobs.get_user_job_by_id")
def test_user_a_cannot_access_user_b_job_endpoint(mock_get_job, override_user_a):
    job_id = uuid4()
    mock_get_job.side_effect = HTTPException(
        status_code=403,
        detail="You do not have permission to access this job analysis."
    )
    res = client.get(
        f"/api/v1/jobs/{job_id}",
        headers={"Authorization": f"Bearer {TOKEN_A}"}
    )
    assert res.status_code == 403
    assert "permission" in res.json()["detail"].lower()


# 8. User Isolation: User A deleting User B's Job
@patch("routes.jobs.delete_user_job")
def test_user_a_cannot_delete_user_b_job(mock_delete, override_user_a):
    job_id = uuid4()
    mock_delete.side_effect = HTTPException(
        status_code=403,
        detail="You do not have permission to access this job analysis."
    )
    res = client.delete(
        f"/api/v1/jobs/{job_id}",
        headers={"Authorization": f"Bearer {TOKEN_A}"}
    )
    assert res.status_code == 403


# 9. Missing LLM configuration error
@patch("services.llm_service.get_settings")
def test_missing_llm_key(mock_settings):
    mock_cfg = MagicMock()
    mock_cfg.llm_api_key = None
    mock_settings.return_value = mock_cfg

    with pytest.raises(HTTPException) as exc:
        from services.llm_service import call_llm_api
        call_llm_api(prompt="test", job_text="test text")
    assert exc.value.status_code == 503
    assert "LLM API key is not configured" in exc.value.detail
