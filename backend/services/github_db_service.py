from typing import Any, Dict, List, Optional
from uuid import UUID
import httpx
from fastapi import HTTPException, status
from services.database_service import get_user_headers, get_rest_base_url
from schemas.github import RepositoryAddRequest, SkillEvidenceItem, ProjectInsights


def add_or_update_repository(user_id: UUID, token: str, repo: RepositoryAddRequest) -> Dict[str, Any]:
    """Adds a repository to the user's portfolio or updates existing record."""
    base_url = get_rest_base_url()
    headers = get_user_headers(token)

    payload = {
        "user_id": str(user_id),
        "github_id": repo.github_id,
        "full_name": repo.full_name,
        "name": repo.name or repo.full_name.split("/")[-1],
        "owner": repo.owner or repo.full_name.split("/")[0],
        "description": repo.description,
        "html_url": repo.html_url or f"https://github.com/{repo.full_name}",
        "default_branch": repo.default_branch or "main",
        "language": repo.language,
        "stargazers_count": repo.stargazers_count or 0,
        "forks_count": repo.forks_count or 0,
        "open_issues_count": repo.open_issues_count or 0,
        "is_fork": repo.is_fork or False,
        "is_private": repo.is_private or False,
        "latest_commit_sha": repo.latest_commit_sha,
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            # Check if repository already added by this user
            check_url = f"{base_url}/repositories?user_id=eq.{str(user_id)}&full_name=eq.{repo.full_name}&select=*"
            res_check = client.get(check_url, headers=headers)
            if res_check.status_code == 200 and len(res_check.json()) > 0:
                existing = res_check.json()[0]
                # Update existing repo metadata
                update_url = f"{base_url}/repositories?id=eq.{existing['id']}"
                res_up = client.patch(update_url, json=payload, headers=headers)
                if res_up.status_code in (200, 204):
                    # Fetch updated
                    res_get = client.get(f"{base_url}/repositories?id=eq.{existing['id']}&select=*", headers=headers)
                    return res_get.json()[0]

            # Otherwise, insert
            res = client.post(f"{base_url}/repositories", json=payload, headers=headers)
            if res.status_code not in (200, 201):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to add repository: {res.text}"
                )
            created = res.json()
            return created[0]
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection error: {str(e)}"
        )


def list_user_repositories(user_id: UUID, token: str) -> List[Dict[str, Any]]:
    """Lists all repositories in the user's portfolio with latest analysis summary."""
    base_url = get_rest_base_url()
    headers = get_user_headers(token)

    url = f"{base_url}/repositories?user_id=eq.{str(user_id)}&select=*,analysis_runs(id,commit_sha,status,evidence_count,created_at,completed_at)&order=updated_at.desc"

    try:
        with httpx.Client(timeout=10.0) as client:
            res = client.get(url, headers=headers)
            if res.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to list repositories: {res.text}"
                )
            repos = res.json()
            for r in repos:
                runs = r.pop("analysis_runs", [])
                if runs and isinstance(runs, list):
                    # Sort runs newest first
                    runs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
                    r["latest_analysis"] = runs[0]
                else:
                    r["latest_analysis"] = None
            return repos
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection error: {str(e)}"
        )


def get_user_repository_by_id(repo_id: UUID, user_id: UUID, token: str) -> Dict[str, Any]:
    """Retrieves a single repository belonging to the user."""
    base_url = get_rest_base_url()
    headers = get_user_headers(token)

    url = f"{base_url}/repositories?id=eq.{str(repo_id)}&user_id=eq.{str(user_id)}&select=*"

    try:
        with httpx.Client(timeout=10.0) as client:
            res = client.get(url, headers=headers)
            if res.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to load repository: {res.text}"
                )
            items = res.json()
            if not items:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Repository not found or access denied."
                )
            repo = items[0]

            # Fetch latest analysis run if exists
            run_url = f"{base_url}/analysis_runs?repository_id=eq.{str(repo_id)}&order=created_at.desc&limit=1&select=*"
            run_res = client.get(run_url, headers=headers)
            if run_res.status_code == 200 and len(run_res.json()) > 0:
                repo["latest_analysis"] = run_res.json()[0]
            else:
                repo["latest_analysis"] = None

            return repo
    except HTTPException:
        raise
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection error: {str(e)}"
        )


def delete_user_repository(repo_id: UUID, user_id: UUID, token: str) -> None:
    """Deletes a repository and cascades deletion to analysis runs and evidence."""
    # Check ownership
    get_user_repository_by_id(repo_id, user_id, token)

    base_url = get_rest_base_url()
    headers = get_user_headers(token)

    url = f"{base_url}/repositories?id=eq.{str(repo_id)}&user_id=eq.{str(user_id)}"

    try:
        with httpx.Client(timeout=10.0) as client:
            res = client.delete(url, headers=headers)
            if res.status_code not in (200, 204):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to delete repository: {res.text}"
                )
    except HTTPException:
        raise
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection error: {str(e)}"
        )


def create_analysis_run(
    repo_id: UUID,
    user_id: UUID,
    token: str,
    commit_sha: str,
    total_discovered: int,
    files_analyzed_count: int,
    evidence_count: int,
    project_insights: ProjectInsights,
    evidence_items: List[SkillEvidenceItem]
) -> Dict[str, Any]:
    """Persists a completed analysis run and all verified skill evidence."""
    base_url = get_rest_base_url()
    headers = get_user_headers(token)

    from datetime import datetime, timezone
    completed_time = datetime.now(timezone.utc).isoformat()

    run_payload = {
        "repository_id": str(repo_id),
        "user_id": str(user_id),
        "commit_sha": commit_sha,
        "status": "completed",
        "total_files_discovered": total_discovered,
        "files_analyzed_count": files_analyzed_count,
        "evidence_count": evidence_count,
        "project_insights": project_insights.model_dump(),
        "analysis_limitations": project_insights.coverage.limitations if project_insights.coverage else None,
        "completed_at": completed_time,
    }

    try:
        with httpx.Client(timeout=15.0) as client:
            # 1. Insert analysis run
            run_res = client.post(f"{base_url}/analysis_runs", json=run_payload, headers=headers)
            if run_res.status_code not in (200, 201):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to create analysis run: {run_res.text}"
                )
            created_run = run_res.json()[0]
            run_id = created_run["id"]

            # 2. Insert skill evidence in bulk
            if evidence_items:
                evidence_payloads = [
                    {
                        "analysis_run_id": run_id,
                        "repository_id": str(repo_id),
                        "user_id": str(user_id),
                        "skill_name": ev.skill_name,
                        "category": ev.category,
                        "evidence_type": ev.evidence_type,
                        "status_label": ev.status_label,
                        "evidence_summary": ev.evidence_summary,
                        "file_path": ev.file_path,
                        "line_start": ev.line_start,
                        "line_end": ev.line_end,
                        "code_excerpt": ev.code_excerpt,
                        "github_url": ev.github_url,
                        "commit_sha": commit_sha,
                        "confidence": ev.confidence,
                        "limitations": ev.limitations,
                    }
                    for ev in evidence_items
                ]
                ev_res = client.post(f"{base_url}/skill_evidence", json=evidence_payloads, headers=headers)
                if ev_res.status_code not in (200, 201):
                    # Clean up orphaned run
                    client.delete(f"{base_url}/analysis_runs?id=eq.{run_id}", headers=headers)
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Failed to persist skill evidence: {ev_res.text}"
                    )
                saved_evidence = ev_res.json()
            else:
                saved_evidence = []

            # 3. Update repository's last_analyzed_commit_sha
            client.patch(
                f"{base_url}/repositories?id=eq.{str(repo_id)}",
                json={"last_analyzed_commit_sha": commit_sha, "latest_commit_sha": commit_sha},
                headers=headers
            )

            created_run["evidence"] = saved_evidence
            return created_run
    except HTTPException:
        raise
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection error: {str(e)}"
        )


def get_latest_repository_analysis(repo_id: UUID, user_id: UUID, token: str) -> Optional[Dict[str, Any]]:
    """Retrieves the latest completed analysis run for a repository, including all evidence."""
    # Verify repo ownership
    get_user_repository_by_id(repo_id, user_id, token)

    base_url = get_rest_base_url()
    headers = get_user_headers(token)

    url = f"{base_url}/analysis_runs?repository_id=eq.{str(repo_id)}&user_id=eq.{str(user_id)}&order=created_at.desc&limit=1&select=*,skill_evidence(*)"

    try:
        with httpx.Client(timeout=10.0) as client:
            res = client.get(url, headers=headers)
            if res.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to retrieve analysis: {res.text}"
                )
            runs = res.json()
            if not runs:
                return None
            run = runs[0]
            run["evidence"] = run.pop("skill_evidence", [])
            return run
    except HTTPException:
        raise
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection error: {str(e)}"
        )


def get_portfolio_summary(user_id: UUID, token: str) -> Dict[str, Any]:
    """Computes high-level portfolio metrics for the user."""
    base_url = get_rest_base_url()
    headers = get_user_headers(token)

    try:
        with httpx.Client(timeout=10.0) as client:
            repos_res = client.get(f"{base_url}/repositories?user_id=eq.{str(user_id)}&select=id,last_analyzed_commit_sha", headers=headers)
            ev_res = client.get(f"{base_url}/skill_evidence?user_id=eq.{str(user_id)}&select=skill_name,created_at&order=created_at.desc", headers=headers)

            total_repos = len(repos_res.json()) if repos_res.status_code == 200 else 0
            analyzed_repos = sum(1 for r in (repos_res.json() if repos_res.status_code == 200 else []) if r.get("last_analyzed_commit_sha"))

            evidence_items = ev_res.json() if ev_res.status_code == 200 else []
            # Count distinct skills detected
            distinct_skills = len(set(e.get("skill_name", "").lower() for e in evidence_items if e.get("skill_name")))
            latest_date = evidence_items[0].get("created_at") if evidence_items else None

            return {
                "total_repositories": total_repos,
                "analyzed_repositories": analyzed_repos,
                "total_skills_detected": distinct_skills,
                "latest_analyzed_at": latest_date,
            }
    except Exception:
        return {
            "total_repositories": 0,
            "analyzed_repositories": 0,
            "total_skills_detected": 0,
            "latest_analyzed_at": None,
        }
