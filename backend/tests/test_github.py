import pytest
from uuid import uuid4
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException

from main import app
from schemas.github import SkillEvidenceItem, ProjectInsights, ArchitectureInsight
from services.github_service import parse_github_query
from services.repo_processor import (
    should_exclude_path,
    score_file_priority,
    filter_and_rank_tree,
    sanitize_source_content,
)
from services.auth_service import get_current_user, AuthenticatedUser

client = TestClient(app)

USER_A_ID = uuid4()
USER_B_ID = uuid4()
TOKEN_A = "test-token-a"

user_a = AuthenticatedUser(user_id=USER_A_ID, email="user_a@example.com", token=TOKEN_A)


@pytest.fixture
def override_user_a():
    app.dependency_overrides[get_current_user] = lambda: user_a
    yield
    app.dependency_overrides.pop(get_current_user, None)


# 1. Query Parsing Tests
def test_parse_github_query():
    mode, identifier = parse_github_query("octocat")
    assert mode == "user"
    assert identifier == "octocat"

    mode, identifier = parse_github_query("octocat/Hello-World")
    assert mode == "repo"
    assert identifier == "octocat/Hello-World"

    mode, identifier = parse_github_query("https://github.com/facebook/react")
    assert mode == "repo"
    assert identifier == "facebook/react"

    mode, identifier = parse_github_query("https://github.com/torvalds")
    assert mode == "user"
    assert identifier == "torvalds"

    with pytest.raises(HTTPException):
        parse_github_query("https://malicious.com/fake/repo")


# 2. File Filtering & Boundary Tests
def test_should_exclude_path():
    assert should_exclude_path("node_modules/express/index.js")[0] is True
    assert should_exclude_path(".git/HEAD")[0] is True
    assert should_exclude_path("dist/bundle.min.js")[0] is True
    assert should_exclude_path("assets/hero.png")[0] is True
    assert should_exclude_path("src/components/Header.jsx")[0] is False
    assert should_exclude_path("backend/main.py")[0] is False
    assert should_exclude_path("package.json")[0] is False


def test_score_file_priority():
    assert score_file_priority("package.json") == 10
    assert score_file_priority("requirements.txt") == 10
    assert score_file_priority("src/routes/api.py") == 9
    assert score_file_priority("backend/models.py") == 8
    assert score_file_priority("tests/test_api.py") == 7
    assert score_file_priority("Dockerfile") == 6
    assert score_file_priority("src/utils.js") == 4


def test_filter_and_rank_tree():
    tree = [
        {"path": "package.json", "type": "blob", "size": 1000},
        {"path": "node_modules/lodash/index.js", "type": "blob", "size": 5000},
        {"path": "src/App.jsx", "type": "blob", "size": 2500},
        {"path": "image.png", "type": "blob", "size": 150000},
        {"path": "tests/app.test.js", "type": "blob", "size": 1200},
    ]
    selected, skipped = filter_and_rank_tree(tree)
    selected_paths = [s["path"] for s in selected]
    assert "package.json" in selected_paths
    assert "src/App.jsx" in selected_paths
    assert "tests/app.test.js" in selected_paths
    assert "node_modules/lodash/index.js" not in selected_paths
    assert "image.png" not in selected_paths


# 3. Secret Detection and Redaction
def test_sanitize_source_content():
    content = "const API_KEY = 'ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890';\nconst secret = 'sk-123456789012345678901234567890123456789012345678';"
    sanitized = sanitize_source_content(content)
    assert "ghp_" not in sanitized
    assert "sk-" not in sanitized
    assert "[REDACTED_SECRET]" in sanitized


# 4. Endpoints: Resolve
@patch("routes.github.fetch_github_user_repos")
def test_resolve_endpoint_user(mock_fetch, override_user_a):
    mock_fetch.return_value = [
        {"full_name": "octocat/Hello-World", "name": "Hello-World", "stargazers_count": 42}
    ]
    res = client.post(
        "/api/v1/github/repositories/resolve",
        headers={"Authorization": f"Bearer {TOKEN_A}"},
        json={"query": "octocat"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["type"] == "user"
    assert len(data["repositories"]) == 1
    assert data["repositories"][0]["full_name"] == "octocat/Hello-World"


# 5. Endpoints: Add Repository
@patch("routes.github.add_or_update_repository")
@patch("routes.github.fetch_latest_commit_sha")
def test_add_repository(mock_sha, mock_add, override_user_a):
    mock_sha.return_value = "abc12345"
    repo_id = uuid4()
    mock_add.return_value = {
        "id": repo_id,
        "user_id": USER_A_ID,
        "full_name": "octocat/Hello-World",
        "name": "Hello-World",
        "owner": "octocat",
        "html_url": "https://github.com/octocat/Hello-World",
        "default_branch": "main",
        "language": "Python",
        "stargazers_count": 10,
        "forks_count": 2,
        "open_issues_count": 0,
        "is_fork": False,
        "is_private": False,
        "latest_commit_sha": "abc12345",
        "created_at": "2026-10-17T00:00:00Z",
        "updated_at": "2026-10-17T00:00:00Z",
    }
    res = client.post(
        "/api/v1/github/repositories",
        headers={"Authorization": f"Bearer {TOKEN_A}"},
        json={"full_name": "octocat/Hello-World", "language": "Python"}
    )
    assert res.status_code == 201
    assert res.json()["full_name"] == "octocat/Hello-World"


# 6. Endpoints: Cross-User Protection
@patch("routes.github.get_user_repository_by_id")
def test_cross_user_protection(mock_get, override_user_a):
    repo_id = uuid4()
    mock_get.side_effect = HTTPException(status_code=403, detail="Access denied")

    res = client.get(
        f"/api/v1/github/repositories/{repo_id}",
        headers={"Authorization": f"Bearer {TOKEN_A}"}
    )
    assert res.status_code == 403
    assert "access denied" in res.json()["detail"].lower()


# 7. Unauthenticated Access Protection
def test_unauthenticated_github_request():
    res = client.get("/api/v1/github/repositories")
    assert res.status_code in (401, 422)
