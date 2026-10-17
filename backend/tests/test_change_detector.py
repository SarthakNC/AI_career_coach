import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List
from unittest.mock import patch, MagicMock
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from main import app
from schemas.change_detection import ChangedFileItem, EvidenceChangeSummary
from services.auth_service import AuthenticatedUser, get_current_user
from services.change_detector_service import (
    fetch_commit_diff_and_metadata,
    get_or_create_change_event,
    reconcile_and_reassess_repository,
    check_and_sync_single_repository,
    get_assessment_version_history,
)
from workers.change_detector_worker import run_monitoring_cycle, process_single_repository

client = TestClient(app)

USER_A_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
USER_B_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
REPO_A_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
REPO_B_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
EVENT_ID = uuid.UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee")
ASSESSMENT_V1_ID = uuid.UUID("12345678-1234-1234-1234-123456789012")

TOKEN_A = "mock_token_user_a"
TOKEN_B = "mock_token_user_b"


def override_user_a():
    return AuthenticatedUser(user_id=USER_A_ID, token=TOKEN_A, email="usera@test.com")


def override_user_b():
    return AuthenticatedUser(user_id=USER_B_ID, token=TOKEN_B, email="userb@test.com")


# ─── 1. COMMIT DIFF & RATE LIMIT TESTS ───

def test_fetch_commit_diff_compare_api():
    """Verify GitHub compare API fetches changed files, author, and commit message."""
    mock_compare_data = {
        "commits": [
            {
                "commit": {
                    "message": "feat: add user authentication endpoints",
                    "author": {"name": "Alice Developer", "date": "2026-10-17T08:00:00Z"},
                }
            }
        ],
        "files": [
            {
                "filename": "backend/auth.py",
                "status": "added",
                "additions": 45,
                "deletions": 0,
                "patch": "@@ -0,0 +1,45 @@\n+def login(): pass",
            },
            {
                "filename": "old_auth.py",
                "status": "removed",
                "additions": 0,
                "deletions": 20,
            },
        ],
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_compare_data

    with patch("httpx.Client.get", return_value=mock_resp):
        res = fetch_commit_diff_and_metadata("user/repo", "sha_old", "sha_new")
        assert res["commit_message"] == "feat: add user authentication endpoints"
        assert res["commit_author"] == "Alice Developer"
        assert res["changed_files_count"] == 2
        assert res["changed_files"][0]["filename"] == "backend/auth.py"
        assert res["changed_files"][1]["status"] == "removed"


def test_fetch_commit_fallback_on_single_commit():
    """When compare API is unavailable or first commit, fallback to single commit endpoint."""
    mock_commit_data = {
        "commit": {
            "message": "Initial commit",
            "author": {"name": "Alice Developer", "date": "2026-10-17T08:00:00Z"},
        },
        "files": [
            {
                "filename": "main.py",
                "status": "added",
                "additions": 30,
                "deletions": 0,
            }
        ],
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_commit_data

    with patch("httpx.Client.get", return_value=mock_resp):
        res = fetch_commit_diff_and_metadata("user/repo", None, "sha_init")
        assert res["commit_message"] == "Initial commit"
        assert len(res["changed_files"]) == 1


# ─── 2. UNCHANGED COMMIT SHA SKIPS EXPENSIVE REANALYSIS ───

def test_unchanged_sha_skips_reanalysis():
    """When repository's last_analyzed_commit_sha matches latest_commit_sha, skip analysis."""
    app.dependency_overrides[get_current_user] = override_user_a
    try:
        mock_repo = {
            "id": str(REPO_A_ID),
            "user_id": str(USER_A_ID),
            "name": "career-coach",
            "full_name": "user/career-coach",
            "default_branch": "main",
            "last_analyzed_commit_sha": "abc1234567890",
        }

        with patch("services.change_detector_service.get_user_repository_by_id", return_value=mock_repo), \
             patch("services.change_detector_service.fetch_latest_commit_sha", return_value="abc1234567890"), \
             patch("services.change_detector_service.analyze_repository_workflow") as mock_analyze:

            res = check_and_sync_single_repository(REPO_A_ID, USER_A_ID, TOKEN_A)

            assert res["has_changes"] is False
            assert res["status"] == "unchanged"
            assert res["detected_commit_sha"] == "abc1234567890"
            assert "is up to date" in res["message"]
            # Verify expensive LLM analysis was NOT called
            mock_analyze.assert_not_called()
    finally:
        app.dependency_overrides.pop(get_current_user, None)


# ─── 3. NEW COMMIT CREATES CHANGE EVENT & TRIGGERS REASSESSMENT ───

def test_new_commit_detection_creates_event_and_reassesses():
    """When SHA changes, an atomic change event is persisted and assessment is recalculated."""
    app.dependency_overrides[get_current_user] = override_user_a
    try:
        mock_repo = {
            "id": str(REPO_A_ID),
            "user_id": str(USER_A_ID),
            "name": "career-coach",
            "full_name": "user/career-coach",
            "default_branch": "main",
            "last_analyzed_commit_sha": "old_sha_123",
        }

        mock_event = {
            "id": str(EVENT_ID),
            "user_id": str(USER_A_ID),
            "repository_id": str(REPO_A_ID),
            "repository_name": "user/career-coach",
            "idempotency_key": f"{REPO_A_ID}:new_sha_456",
            "previous_commit_sha": "old_sha_123",
            "detected_commit_sha": "new_sha_456",
            "commit_message": "feat: add redis cache and pytest tests",
            "commit_author": "Alice",
            "status": "pending",
            "changed_files": [
                {"filename": "cache.py", "status": "added", "additions": 15, "deletions": 0},
                {"filename": "deprecated.py", "status": "removed", "additions": 0, "deletions": 50},
            ],
            "changed_files_count": 2,
            "evidence_updated": False,
            "processing_attempts": 0,
            "detected_at": "2026-10-17T08:00:00Z",
        }

        # Mock parent assessment (v1)
        mock_parent_assessment = {
            "id": str(ASSESSMENT_V1_ID),
            "user_id": str(USER_A_ID),
            "job_id": str(uuid.uuid4()),
            "job_title": "Senior Backend Engineer",
            "selected_repository_ids": [str(REPO_A_ID)],
            "match_score": 60.0,
            "version": 1,
        }

        mock_job = {
            "id": mock_parent_assessment["job_id"],
            "job_title": "Senior Backend Engineer",
            "company_name": "Tech Corp",
            "requirements": [{"requirement_text": "Experience with Redis and testing", "skill_name": "Redis"}],
        }

        # Mock newly extracted skill evidence
        mock_evidence_item = MagicMock()
        mock_evidence_item.skill_name = "Redis"
        mock_evidence_item.evidence_type = "source_code"
        mock_evidence_item.status_label = "Strong evidence"
        mock_evidence_item.confidence = 0.95

        with patch("services.change_detector_service.get_user_repository_by_id", return_value=mock_repo), \
             patch("services.change_detector_service.fetch_latest_commit_sha", return_value="new_sha_456"), \
             patch("services.change_detector_service.get_or_create_change_event", return_value=(mock_event, True)), \
             patch("services.change_detector_service.analyze_repository_workflow", return_value=(MagicMock(), [mock_evidence_item], 10, 5)), \
             patch("services.change_detector_service.create_analysis_run", return_value={"id": str(uuid.uuid4())}), \
             patch("services.change_detector_service.get_user_job_by_id", return_value=mock_job), \
             patch("services.change_detector_service.list_user_repositories", return_value=[mock_repo]), \
             patch("services.change_detector_service.get_latest_repository_analysis", return_value={"evidence": [mock_evidence_item]}), \
             patch("services.change_detector_service.run_skill_gap_assessment", return_value={
                 "job_id": UUID(mock_job["id"]),
                 "match_score": 75.0,
                 "requirement_results": [],
                 "prioritized_gaps": [],
                 "recommendations": [],
             }), \
             patch("services.change_detector_service.create_assessment_record", return_value={"id": str(uuid.uuid4()), "version": 2}), \
             patch("httpx.Client.get") as mock_get, \
             patch("httpx.Client.patch") as mock_patch:

            # Mock GET query returning parent assessment
            mock_as_resp = MagicMock()
            mock_as_resp.status_code = 200
            mock_as_resp.json.return_value = [mock_parent_assessment]
            mock_get.return_value = mock_as_resp

            mock_patch_resp = MagicMock()
            mock_patch_resp.status_code = 200
            mock_patch.return_value = mock_patch_resp

            res = check_and_sync_single_repository(REPO_A_ID, USER_A_ID, TOKEN_A)

            assert res["has_changes"] is True
            assert res["status"] == "updated"
            assert res["detected_commit_sha"] == "new_sha_456"
            assert res["change_event"]["status"] == "completed"
            assert res["change_event"]["evidence_updated"] is True
            # Verified that removed file caused invalidation count = 1
            assert res["change_event"]["evidence_change_summary"]["invalidated_count"] == 1
            # Verified assessment updates list
            assert len(res["change_event"]["assessment_updates"]) == 1
            as_update = res["change_event"]["assessment_updates"][0]
            assert as_update["new_version"] == 2
            assert as_update["previous_score"] == 60.0
            assert as_update["new_score"] == 75.0
            assert as_update["score_delta"] == 15.0
    finally:
        app.dependency_overrides.pop(get_current_user, None)


# ─── 4. IDEMPOTENCY PREVENTS DUPLICATE EVENTS ───

def test_idempotency_prevents_duplicate_change_events():
    """Verify get_or_create_change_event returns existing event when idempotency_key already exists."""
    mock_existing_event = {
        "id": str(EVENT_ID),
        "idempotency_key": f"{REPO_A_ID}:sha_test_123",
        "status": "completed",
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [mock_existing_event]

    with patch("httpx.Client.get", return_value=mock_resp):
        event, is_new = get_or_create_change_event(
            repo={"id": str(REPO_A_ID), "full_name": "user/repo"},
            detected_sha="sha_test_123",
            previous_sha="sha_old",
            user_id=USER_A_ID,
            token=TOKEN_A
        )
        assert is_new is False
        assert event["id"] == str(EVENT_ID)


# ─── 5. API ENDPOINTS & OWNERSHIP VERIFICATION ───

def test_get_monitoring_status_endpoint():
    """GET /api/v1/github/monitoring/status returns configured settings and repositories."""
    app.dependency_overrides[get_current_user] = override_user_a
    try:
        mock_repos = [
            {
                "id": str(REPO_A_ID),
                "name": "portfolio",
                "full_name": "user/portfolio",
                "default_branch": "main",
                "last_analyzed_commit_sha": "sha_111",
                "latest_commit_sha": "sha_111",
                "last_polled_at": "2026-10-17T08:00:00Z",
                "last_poll_status": "ok",
            }
        ]

        with patch("services.change_detector_service.list_user_repositories", return_value=mock_repos), \
             patch("services.change_detector_service.list_user_change_events", return_value=[]):

            response = client.get(
                "/api/v1/github/monitoring/status",
                headers={"Authorization": f"Bearer {TOKEN_A}"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["monitoring_enabled"] is True
            assert data["total_monitored_repositories"] == 1
            assert len(data["repositories"]) == 1
            assert data["repositories"][0]["full_name"] == "user/portfolio"
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_list_change_events_endpoint():
    """GET /api/v1/github/changes returns persisted change events for user."""
    app.dependency_overrides[get_current_user] = override_user_a
    try:
        mock_events = [
            {
                "id": str(EVENT_ID),
                "user_id": str(USER_A_ID),
                "repository_id": str(REPO_A_ID),
                "repository_name": "user/repo",
                "idempotency_key": f"{REPO_A_ID}:sha_123",
                "detected_commit_sha": "sha_123",
                "status": "completed",
                "changed_files": [],
                "changed_files_count": 0,
                "evidence_updated": True,
                "assessments_recalculated_count": 1,
                "processing_attempts": 1,
                "detected_at": "2026-10-17T08:00:00Z",
                "created_at": "2026-10-17T08:00:00Z",
            }
        ]

        with patch("routes.github_changes.list_user_change_events", return_value=mock_events):
            response = client.get(
                "/api/v1/github/changes",
                headers={"Authorization": f"Bearer {TOKEN_A}"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 1
            assert data["events"][0]["id"] == str(EVENT_ID)
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_unauthenticated_request_rejected():
    """Accessing monitoring or change events without token returns 401 or 422."""
    res_status = client.get("/api/v1/github/monitoring/status")
    assert res_status.status_code in (401, 403, 422)

    res_changes = client.get("/api/v1/github/changes")
    assert res_changes.status_code in (401, 403, 422)


def test_cross_user_isolation_for_change_event():
    """User B cannot fetch User A's change event."""
    from fastapi import HTTPException
    app.dependency_overrides[get_current_user] = override_user_b
    try:
        def mock_denied(*args, **kwargs):
            raise HTTPException(status_code=404, detail="Change event not found or access denied.")

        with patch("routes.github_changes.get_change_event_by_id", side_effect=mock_denied):
            response = client.get(
                f"/api/v1/github/changes/{EVENT_ID}",
                headers={"Authorization": f"Bearer {TOKEN_B}"}
            )
            assert response.status_code == 404
            assert "not found or access denied" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_assessment_version_history_endpoint():
    """GET /api/v1/assessments/{id}/history returns version timeline (v1, v2)."""
    app.dependency_overrides[get_current_user] = override_user_a
    try:
        mock_v1 = {
            "id": str(ASSESSMENT_V1_ID),
            "version": 1,
            "match_score": 60.0,
            "score_delta": 0.0,
            "created_at": "2026-10-17T07:00:00Z",
        }
        mock_v2 = {
            "id": str(uuid.uuid4()),
            "parent_assessment_id": str(ASSESSMENT_V1_ID),
            "trigger_commit_sha": "abc999",
            "version": 2,
            "match_score": 75.0,
            "score_delta": 15.0,
            "created_at": "2026-10-17T08:00:00Z",
        }

        mock_history = {
            "assessment_id": str(ASSESSMENT_V1_ID),
            "job_title": "Full Stack Engineer",
            "company_name": "CareerProof AI",
            "current_version": 2,
            "versions": [mock_v1, mock_v2],
        }

        with patch("routes.assessments.get_assessment_version_history", return_value=mock_history):
            response = client.get(
                f"/api/v1/assessments/{ASSESSMENT_V1_ID}/history",
                headers={"Authorization": f"Bearer {TOKEN_A}"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["current_version"] == 2
            assert len(data["versions"]) == 2
            assert data["versions"][0]["version"] == 1
            assert data["versions"][1]["score_delta"] == 15.0
    finally:
        app.dependency_overrides.pop(get_current_user, None)


# ─── 6. WORKER POLLING CYCLE TEST ───

def test_worker_polling_cycle_skips_unchanged_and_processes_new():
    """Worker polling cycle checks eligible repos, skips unchanged SHAs, and processes new commits."""
    mock_repos = [
        {
            "id": str(REPO_A_ID),
            "user_id": str(USER_A_ID),
            "full_name": "user/repo-a",
            "default_branch": "main",
            "last_analyzed_commit_sha": "sha_same",
            "monitoring_enabled": True,
        },
        {
            "id": str(REPO_B_ID),
            "user_id": str(USER_A_ID),
            "full_name": "user/repo-b",
            "default_branch": "main",
            "last_analyzed_commit_sha": "sha_old",
            "monitoring_enabled": True,
        },
    ]

    def mock_fetch_sha(full_name, branch):
        if full_name == "user/repo-a":
            return "sha_same"
        return "sha_new"

    mock_event = {
        "id": str(EVENT_ID),
        "detected_commit_sha": "sha_new",
        "status": "pending",
        "changed_files_count": 1,
    }

    with patch("workers.change_detector_worker.fetch_all_monitored_repositories", return_value=mock_repos), \
         patch("workers.change_detector_worker.fetch_latest_commit_sha", side_effect=mock_fetch_sha), \
         patch("workers.change_detector_worker.update_repository_poll_status"), \
         patch("workers.change_detector_worker.get_or_create_change_event", return_value=(mock_event, True)), \
         patch("workers.change_detector_worker.reconcile_and_reassess_repository", return_value={"assessments_recalculated_count": 1}):

        updated_count = run_monitoring_cycle()
        # Repo A was unchanged (skipped), Repo B had new commit (processed)
        assert updated_count == 1
