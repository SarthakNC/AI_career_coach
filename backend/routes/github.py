from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from schemas.github import (
    GitHubResolveRequest,
    GitHubResolvedItem,
    RepositoryAddRequest,
    RepositoryResponse,
    AnalysisRunResponse,
    PortfolioSummaryResponse,
)
from services.auth_service import AuthenticatedUser, get_current_user
from services.github_service import (
    parse_github_query,
    fetch_github_user_repos,
    fetch_github_repository,
    fetch_repo_git_tree,
    fetch_raw_file_content,
    fetch_latest_commit_sha,
)
from services.repo_processor import filter_and_rank_tree, sanitize_source_content
from services.repo_analyzer import analyze_repository_files_with_llm
from services.github_db_service import (
    add_or_update_repository,
    list_user_repositories,
    get_user_repository_by_id,
    delete_user_repository,
    create_analysis_run,
    get_latest_repository_analysis,
    get_portfolio_summary,
)

router = APIRouter(prefix="/api/v1/github", tags=["GitHub Portfolio"])


@router.post("/repositories/resolve", response_model=GitHubResolvedItem, status_code=status.HTTP_200_OK)
def resolve_github_identifier(
    request: GitHubResolveRequest,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Validates and resolves a GitHub username or repository URL.
    Returns either a user profile with repository list or single repository details.
    """
    mode, identifier = parse_github_query(request.query)

    if mode == "user":
        repos = fetch_github_user_repos(identifier)
        return GitHubResolvedItem(
            type="user",
            username=identifier,
            repositories=repos
        )
    else:
        repo = fetch_github_repository(identifier)
        return GitHubResolvedItem(
            type="repo",
            repository=repo
        )


@router.get("/repositories", response_model=List[RepositoryResponse], status_code=status.HTTP_200_OK)
def get_user_repositories(
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """Lists all repositories in the user's portfolio."""
    return list_user_repositories(current_user.user_id, current_user.token)


@router.post("/repositories", response_model=RepositoryResponse, status_code=status.HTTP_201_CREATED)
def add_repository_to_portfolio(
    repo_data: RepositoryAddRequest,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """Adds or updates a repository in the user's portfolio."""
    # If latest_commit_sha is missing, fetch it
    if not repo_data.latest_commit_sha:
        branch = repo_data.default_branch or "main"
        sha = fetch_latest_commit_sha(repo_data.full_name, branch)
        repo_data.latest_commit_sha = sha

    return add_or_update_repository(current_user.user_id, current_user.token, repo_data)


@router.get("/repositories/{repository_id}", response_model=RepositoryResponse, status_code=status.HTTP_200_OK)
def get_repository(
    repository_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """Retrieves repository details by ID."""
    return get_user_repository_by_id(repository_id, current_user.user_id, current_user.token)


@router.delete("/repositories/{repository_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_repository(
    repository_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """Deletes a repository and associated analysis data."""
    delete_user_repository(repository_id, current_user.user_id, current_user.token)
    return None


@router.post("/repositories/{repository_id}/analyze", response_model=AnalysisRunResponse, status_code=status.HTTP_200_OK)
def analyze_repository(
    repository_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Executes an intelligent, bounded analysis of the repository at its latest commit SHA:
    1. Fetches repository and tree.
    2. Ranks and selects high-signal files within safety and token bounds.
    3. Fetches raw file contents at the exact target commit.
    4. Redacts secrets and extracts candidate evidence.
    5. Analyzes with LLM for verified skills and project architecture insights.
    6. Persists analysis run and skill evidence to Supabase.
    """
    repo = get_user_repository_by_id(repository_id, current_user.user_id, current_user.token)
    full_name = repo["full_name"]
    default_branch = repo.get("default_branch", "main")

    # Ensure commit SHA is known
    commit_sha = repo.get("latest_commit_sha")
    if not commit_sha:
        commit_sha = fetch_latest_commit_sha(full_name, default_branch)
    if not commit_sha:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not resolve latest commit SHA for {full_name} on branch {default_branch}."
        )

    # 1. Fetch recursive git tree
    tree = fetch_repo_git_tree(full_name, commit_sha)
    if not tree:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Repository {full_name} is empty or contains no readable files."
        )

    # 2. Filter & rank files
    selected_items, skipped_reasons = filter_and_rank_tree(tree)
    if not selected_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No qualifying source or configuration files were found to analyze within safety bounds."
        )

    # 3. Retrieve content of selected files
    files_map = {}
    for item in selected_items:
        path = item.get("path")
        blob_sha = item.get("sha")
        content = fetch_raw_file_content(full_name, commit_sha, path, blob_sha=blob_sha)
        if content:
            files_map[path] = sanitize_source_content(content)

    if not files_map:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to retrieve file contents from GitHub API. Please check repository accessibility or configure GITHUB_TOKEN in backend/.env."
        )

    # 4. Run LLM Analysis & Extract Insights
    evidence_items, project_insights = analyze_repository_files_with_llm(
        repo_full_name=full_name,
        commit_sha=commit_sha,
        files_map=files_map,
        total_discovered=len(tree),
        skipped_reasons=skipped_reasons
    )

    # 5. Persist to Supabase
    created_run = create_analysis_run(
        repo_id=repository_id,
        user_id=current_user.user_id,
        token=current_user.token,
        commit_sha=commit_sha,
        total_discovered=len(tree),
        files_analyzed_count=len(files_map),
        evidence_count=len(evidence_items),
        project_insights=project_insights,
        evidence_items=evidence_items
    )

    return created_run


@router.get("/repositories/{repository_id}/analysis", response_model=Optional[AnalysisRunResponse], status_code=status.HTTP_200_OK)
def get_repository_analysis(
    repository_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """Retrieves the latest completed analysis run with verified skill evidence."""
    analysis = get_latest_repository_analysis(repository_id, current_user.user_id, current_user.token)
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No completed analysis found for this repository."
        )
    return analysis


@router.get("/portfolio-summary", response_model=PortfolioSummaryResponse, status_code=status.HTTP_200_OK)
def get_portfolio_metrics(
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """Retrieves high-level portfolio metrics: total repos, analyzed repos, skills detected."""
    return get_portfolio_summary(current_user.user_id, current_user.token)
