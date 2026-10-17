import hashlib
import os
import re
from typing import Any, Dict, List, Optional, Tuple

EXTENSION_LANGUAGE_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".cpp": "cpp",
    ".c": "c",
    ".cs": "csharp",
    ".rb": "ruby",
    ".php": "php",
    ".html": "html",
    ".css": "css",
    ".scss": "scss",
    ".sql": "sql",
    ".sh": "bash",
    ".bash": "bash",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
    ".toml": "toml",
    ".md": "markdown",
    ".dockerfile": "dockerfile",
}

DEPENDENCY_MANIFESTS = {
    "package.json", "requirements.txt", "pyproject.toml", "setup.py",
    "pom.xml", "build.gradle", "cargo.toml", "go.mod", "gemfile"
}

CONFIG_FILES = {
    "dockerfile", "docker-compose.yml", "docker-compose.yaml",
    "tsconfig.json", "vite.config.js", "vite.config.ts",
    "webpack.config.js", "tailwind.config.js", "tailwind.config.ts",
    ".eslintrc", ".prettierrc"
}


def detect_file_language(file_path: str) -> str:
    """Detects programming or markup language from file path."""
    lower = file_path.lower().replace("\\", "/")
    filename = lower.split("/")[-1]

    if filename == "dockerfile" or filename.startswith("dockerfile."):
        return "dockerfile"

    for ext, lang in EXTENSION_LANGUAGE_MAP.items():
        if filename.endswith(ext):
            return lang

    return "text"


def determine_chunk_type(file_path: str) -> str:
    """Classifies file role for contextual retrieval weighting."""
    lower = file_path.lower().replace("\\", "/")
    filename = lower.split("/")[-1]

    # Tests
    if any(k in lower for k in ("test_", "_test.", ".test.", ".spec.", "/tests/", "/test/", "/__tests__/")):
        return "test"

    # Dependency manifests
    if filename in DEPENDENCY_MANIFESTS:
        return "dependency"

    # Config & DevOps
    if filename in CONFIG_FILES or any(k in lower for k in (".github/workflows", "k8s/", "helm/", "terraform/")):
        return "config"

    # Documentation
    if filename.endswith(".md") or filename.startswith("readme") or "docs/" in lower:
        return "documentation"

    return "source_code"


def generate_chunk_id(repo_id: str, commit_sha: str, file_path: str, start_line: int, end_line: int) -> str:
    """Generates a stable, unique identifier for a code chunk."""
    path_hash = hashlib.sha256(file_path.encode("utf-8")).hexdigest()[:8]
    clean_sha = (commit_sha or "latest")[:7]
    return f"chk_{repo_id[:8]}_{clean_sha}_{path_hash}_{start_line}_{end_line}"


def chunk_code_file(
    file_path: str,
    content: str,
    repo_id: str,
    repo_name: str,
    commit_sha: str,
    user_id: str,
    chunk_size_lines: int = 40,
    overlap_lines: int = 10
) -> List[Dict[str, Any]]:
    """
    Intelligently splits source code into contextual chunks.
    Preserves exact 1-indexed line numbers for auditability.
    """
    if not content or not content.strip():
        return []

    lines = content.splitlines()
    total_lines = len(lines)
    if total_lines == 0:
        return []

    language = detect_file_language(file_path)
    chunk_type = determine_chunk_type(file_path)
    chunks: List[Dict[str, Any]] = []

    # If the file is small, produce a single chunk
    if total_lines <= chunk_size_lines:
        chunk_lines = lines
        raw_text = "\n".join(chunk_lines)
        header = f"// File: {file_path} | Lines: 1-{total_lines} | Repo: {repo_name} | Language: {language}\n"
        full_text = header + raw_text
        chunk_id = generate_chunk_id(repo_id, commit_sha, file_path, 1, total_lines)

        chunks.append({
            "id": chunk_id,
            "document": full_text,
            "metadata": {
                "user_id": str(user_id),
                "repository_id": str(repo_id),
                "repository_name": repo_name,
                "commit_sha": commit_sha,
                "file_path": file_path,
                "start_line": 1,
                "end_line": total_lines,
                "language": language,
                "chunk_type": chunk_type,
                "total_file_lines": total_lines,
            }
        })
        return chunks

    step = max(1, chunk_size_lines - overlap_lines)
    i = 0
    while i < total_lines:
        start_idx = i
        end_idx = min(total_lines, i + chunk_size_lines)

        # Look forward for a natural line break if near the end of a block
        if end_idx < total_lines:
            lookahead_limit = min(total_lines, end_idx + 5)
            for j in range(end_idx, lookahead_limit):
                line_str = lines[j].strip()
                if not line_str or line_str.startswith(("def ", "class ", "function ", "export ", "const ", "async ", "type ")):
                    end_idx = j
                    break

        chunk_slice = lines[start_idx:end_idx]
        raw_text = "\n".join(chunk_slice)
        start_line = start_idx + 1
        end_line = end_idx

        header = f"// File: {file_path} | Lines: {start_line}-{end_line} | Repo: {repo_name} | Language: {language}\n"
        full_text = header + raw_text
        chunk_id = generate_chunk_id(repo_id, commit_sha, file_path, start_line, end_line)

        chunks.append({
            "id": chunk_id,
            "document": full_text,
            "metadata": {
                "user_id": str(user_id),
                "repository_id": str(repo_id),
                "repository_name": repo_name,
                "commit_sha": commit_sha,
                "file_path": file_path,
                "start_line": start_line,
                "end_line": end_line,
                "language": language,
                "chunk_type": chunk_type,
                "total_file_lines": total_lines,
            }
        })

        if end_idx >= total_lines:
            break
        i += step

    return chunks


def chunk_repository_files(
    files_map: Dict[str, str],
    repo_id: str,
    repo_name: str,
    commit_sha: str,
    user_id: str,
    chunk_size_lines: int = 40,
    overlap_lines: int = 10
) -> List[Dict[str, Any]]:
    """Chunks all selected repository source files into indexing candidates."""
    all_chunks: List[Dict[str, Any]] = []
    for file_path, content in files_map.items():
        file_chunks = chunk_code_file(
            file_path=file_path,
            content=content,
            repo_id=repo_id,
            repo_name=repo_name,
            commit_sha=commit_sha,
            user_id=user_id,
            chunk_size_lines=chunk_size_lines,
            overlap_lines=overlap_lines
        )
        all_chunks.extend(file_chunks)
    return all_chunks
