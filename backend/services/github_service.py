import base64
import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse
import httpx
from fastapi import HTTPException, status
from config import get_current_github_token, get_settings

GITHUB_API_BASE = "https://api.github.com"


def get_github_headers() -> Dict[str, str]:
    """Prepares headers for GitHub API, dynamically injecting GITHUB_TOKEN if configured."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "CareerProof-AI/1.0",
    }
    token = get_current_github_token()
    if token:
        token = token.strip()
        if token.startswith("ghp_") or token.startswith("gho_") or token.startswith("ghu_"):
            # GitHub classic personal access tokens use 'token <TOKEN>'
            headers["Authorization"] = f"token {token}"
        elif token.startswith("github_pat_"):
            # Fine-grained personal access tokens use 'Bearer <TOKEN>'
            headers["Authorization"] = f"Bearer {token}"
        elif token.lower().startswith("bearer ") or token.lower().startswith("token "):
            headers["Authorization"] = token
        else:
            headers["Authorization"] = f"token {token}"
    return headers


def check_github_response_status(res: httpx.Response, action_description: str = "GitHub API request"):
    """Validates GitHub API response status, providing precise guidance for 401 and 429."""
    if res.status_code == 401:
        token = get_current_github_token() or ""
        hint = ""
        if token.startswith("ghp_") and len(token) != 40:
            hint = f" The GITHUB_TOKEN in backend/.env has {len(token)} characters, but GitHub classic tokens ('ghp_...') must be exactly 40 characters (it appears truncated by {40 - len(token)} characters)."
        elif not token:
            hint = " No GITHUB_TOKEN was found in backend/.env."
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"GitHub returned 'Bad credentials' (HTTP 401).{hint} Please verify your GITHUB_TOKEN in backend/.env or generate a new personal access token."
        )
    if res.status_code == 403 and "rate limit" in res.text.lower():
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="GitHub API rate limit exceeded. Please configure GITHUB_TOKEN in backend/.env to get 5,000 requests/hour."
        )


def parse_github_query(query: str) -> Tuple[str, Optional[str]]:
    """
    Parses a query into either ('user', username) or ('repo', 'owner/repo').
    Supports:
      - 'octocat' -> ('user', 'octocat')
      - 'octocat/Hello-World' -> ('repo', 'octocat/Hello-World')
      - 'https://github.com/octocat/Hello-World' -> ('repo', 'octocat/Hello-World')
      - 'https://github.com/octocat' -> ('user', 'octocat')
    """
    q = query.strip()
    if q.startswith("http://") or q.startswith("https://"):
        parsed = urlparse(q)
        if "github.com" not in parsed.netloc.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only GitHub URLs (https://github.com/...) are supported."
            )
        parts = [p for p in parsed.path.strip("/").split("/") if p]
        if len(parts) == 1:
            return "user", parts[0]
        elif len(parts) >= 2:
            return "repo", f"{parts[0]}/{parts[1]}"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid GitHub URL path."
            )

    # Check if format is owner/repo
    if "/" in q:
        parts = [p.strip() for p in q.split("/") if p.strip()]
        if len(parts) == 2:
            return "repo", f"{parts[0]}/{parts[1]}"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid repository format. Expected 'owner/repo'."
            )

    # Plain username
    if re.match(r"^[a-zA-Z0-9](?:[a-zA-Z0-9]|-(?=[a-zA-Z0-9])){0,38}$", q):
        return "user", q

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid GitHub username or repository name format."
    )


def fetch_github_user_repos(username: str) -> List[Dict[str, Any]]:
    """Fetches public repositories for a given user, sorted by updated date."""
    headers = get_github_headers()
    url = f"{GITHUB_API_BASE}/users/{username}/repos?sort=updated&per_page=30&type=owner"

    try:
        with httpx.Client(timeout=15.0) as client:
            res = client.get(url, headers=headers)
            check_github_response_status(res, "fetch user repositories")
            if res.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"GitHub user '{username}' was not found."
                )
            if res.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"GitHub API returned error HTTP {res.status_code}: {res.text[:200]}"
                )

            repos = res.json()
            return [
                {
                    "github_id": r.get("id"),
                    "full_name": r.get("full_name"),
                    "name": r.get("name"),
                    "owner": r.get("owner", {}).get("login"),
                    "description": r.get("description"),
                    "html_url": r.get("html_url"),
                    "default_branch": r.get("default_branch", "main"),
                    "language": r.get("language"),
                    "stargazers_count": r.get("stargazers_count", 0),
                    "forks_count": r.get("forks_count", 0),
                    "open_issues_count": r.get("open_issues_count", 0),
                    "is_fork": r.get("fork", False),
                    "is_private": r.get("private", False),
                    "updated_at": r.get("updated_at"),
                }
                for r in repos
            ]
    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="GitHub API request timed out."
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Network error contacting GitHub API: {str(e)}"
        )


def fetch_github_repository(full_name: str) -> Dict[str, Any]:
    """Fetches details for a single public repository."""
    headers = get_github_headers()
    url = f"{GITHUB_API_BASE}/repos/{full_name}"

    try:
        with httpx.Client(timeout=15.0) as client:
            res = client.get(url, headers=headers)
            check_github_response_status(res, "fetch repository metadata")
            if res.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"GitHub repository '{full_name}' was not found or is private."
                )
            if res.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"GitHub API returned error HTTP {res.status_code}: {res.text[:200]}"
                )

            r = res.json()

            # Also fetch latest commit SHA on default branch
            default_branch = r.get("default_branch", "main")
            commit_sha = fetch_latest_commit_sha(full_name, default_branch)

            # Also fetch languages breakdown
            languages = fetch_repo_languages(full_name)

            return {
                "github_id": r.get("id"),
                "full_name": r.get("full_name"),
                "name": r.get("name"),
                "owner": r.get("owner", {}).get("login"),
                "description": r.get("description"),
                "html_url": r.get("html_url"),
                "default_branch": default_branch,
                "language": r.get("language"),
                "languages_breakdown": languages,
                "stargazers_count": r.get("stargazers_count", 0),
                "forks_count": r.get("forks_count", 0),
                "open_issues_count": r.get("open_issues_count", 0),
                "is_fork": r.get("fork", False),
                "is_private": r.get("private", False),
                "latest_commit_sha": commit_sha,
                "updated_at": r.get("updated_at"),
            }
    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="GitHub API request timed out."
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Network error contacting GitHub API: {str(e)}"
        )


def fetch_latest_commit_sha(full_name: str, branch: str) -> Optional[str]:
    """Fetches the latest commit SHA for a branch."""
    headers = get_github_headers()
    url = f"{GITHUB_API_BASE}/repos/{full_name}/commits/{branch}"
    try:
        with httpx.Client(timeout=10.0) as client:
            res = client.get(url, headers=headers)
            check_github_response_status(res, "fetch latest commit")
            if res.status_code == 200:
                return res.json().get("sha")
            return None
    except HTTPException:
        raise
    except Exception:
        return None


def fetch_repo_languages(full_name: str) -> Dict[str, int]:
    """Fetches the language bytes distribution."""
    headers = get_github_headers()
    url = f"{GITHUB_API_BASE}/repos/{full_name}/languages"
    try:
        with httpx.Client(timeout=10.0) as client:
            res = client.get(url, headers=headers)
            if res.status_code == 200:
                return res.json()
            return {}
    except Exception:
        return {}


def fetch_repo_git_tree(full_name: str, commit_sha: str) -> List[Dict[str, Any]]:
    """
    Fetches the recursive git tree for a specific commit SHA.
    Returns list of items: [{path, mode, type: 'blob'|'tree', sha, size}, ...]
    """
    headers = get_github_headers()
    url = f"{GITHUB_API_BASE}/repos/{full_name}/git/trees/{commit_sha}?recursive=1"

    try:
        with httpx.Client(timeout=15.0) as client:
            res = client.get(url, headers=headers)
            check_github_response_status(res, "fetch git tree")
            if res.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Commit tree for '{full_name}' at commit {commit_sha[:8]} not found."
                )
            if res.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Failed to fetch git tree (HTTP {res.status_code}): {res.text[:200]}"
                )

            data = res.json()
            return data.get("tree", [])
    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Git tree request timed out."
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Network error fetching git tree: {str(e)}"
        )


def fetch_raw_file_content(
    full_name: str,
    commit_sha: str,
    path: str,
    blob_sha: Optional[str] = None
) -> Optional[str]:
    """
    Retrieves the raw text content of a file at a specific commit SHA.
    Prefers the GitHub Git Blobs API (using blob_sha) to stay entirely within
    api.github.com, avoiding base64 truncation and external raw CDN timeouts.
    Falls back to /contents/{path} with raw Accept header.
    """
    headers = get_github_headers()

    # 1. Use Git Blobs API if blob_sha is available (fastest, direct, reliable)
    if blob_sha:
        blob_url = f"{GITHUB_API_BASE}/repos/{full_name}/git/blobs/{blob_sha}"
        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.get(blob_url, headers=headers)
                check_github_response_status(res, "fetch blob content")
                if res.status_code == 200:
                    data = res.json()
                    if isinstance(data, dict) and data.get("encoding") == "base64" and data.get("content"):
                        raw_bytes = base64.b64decode(data["content"])
                        return raw_bytes.decode("utf-8", errors="replace")
        except HTTPException:
            raise
        except Exception:
            pass

    # 2. Try Contents API with base64 response or raw stream
    url = f"{GITHUB_API_BASE}/repos/{full_name}/contents/{path}?ref={commit_sha}"
    try:
        with httpx.Client(timeout=10.0) as client:
            res = client.get(url, headers=headers)
            check_github_response_status(res, "fetch file content")
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, dict) and data.get("encoding") == "base64" and data.get("content"):
                    raw_bytes = base64.b64decode(data["content"])
                    return raw_bytes.decode("utf-8", errors="replace")

            # 3. Fallback: try raw accept header on contents endpoint
            raw_headers = dict(headers)
            raw_headers["Accept"] = "application/vnd.github.v3.raw"
            raw_res = client.get(url, headers=raw_headers)
            check_github_response_status(raw_res, "fetch raw content")
            if raw_res.status_code == 200 and raw_res.text:
                return raw_res.text

            return None
    except HTTPException:
        raise
    except Exception:
        return None
