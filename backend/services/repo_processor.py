import re
from typing import Dict, List, Optional, Set, Tuple

# Configuration bounds
MAX_FILES_TO_ANALYZE = 25
MAX_FILE_SIZE_BYTES = 80 * 1024  # 80 KB
MAX_TOTAL_ANALYZED_BYTES = 500 * 1024  # 500 KB

# Excluded directory segments
EXCLUDED_DIRS = {
    ".git", "node_modules", "venv", ".venv", "env", "__pycache__",
    "dist", "build", "target", "out", ".next", ".nuxt", "coverage",
    ".idea", ".vscode", "vendor", "bin", "obj", ".cache"
}

# Excluded extensions (binaries, media, lockfiles, minified files)
EXCLUDED_EXTENSIONS = {
    # Binaries & Archives
    ".exe", ".dll", ".so", ".dylib", ".bin", ".zip", ".tar", ".gz", ".7z", ".rar",
    # Images & Media
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".webp", ".mp4", ".mov", ".mp3",
    # Fonts
    ".woff", ".woff2", ".ttf", ".eot",
    # Documents
    ".pdf", ".docx", ".xlsx",
    # Large or compiled data
    ".min.js", ".min.css", ".map", ".pyc", ".class", ".wasm"
}

# Regex to detect probable API keys, JWTs, and secrets to redact
SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|secret|password|auth[_-]?token|private[_-]?key|bearer)\s*[:=]\s*['\"]([^'\"]{8,})['\"]"),
    re.compile(r"ghp_[A-Za-z0-9_]{36}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{82}"),
    re.compile(r"AIza[0-9A-Za-z-_]{35}"),
    re.compile(r"sk-[a-zA-Z0-9]{48}"),
    re.compile(r"eyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}"),
]

# Priority categories for selection ranking
MANIFEST_PATTERNS = [
    "package.json", "requirements.txt", "pyproject.toml", "setup.py",
    "pom.xml", "build.gradle", "cargo.toml", "go.mod", "gemfile"
]

CONFIG_PATTERNS = [
    "dockerfile", "docker-compose.yml", "docker-compose.yaml",
    ".github/workflows", "tsconfig.json", "vite.config", "webpack.config",
    ".eslintrc", "tailwind.config"
]


def should_exclude_path(path: str) -> Tuple[bool, Optional[str]]:
    """Checks whether a file path should be excluded based on dir or extension."""
    parts = path.replace("\\", "/").split("/")
    for part in parts[:-1]:
        if part.lower() in EXCLUDED_DIRS or part.startswith("."):
            if part.lower() != ".github":
                return True, f"Excluded directory: {part}"

    filename = parts[-1].lower()
    for ext in EXCLUDED_EXTENSIONS:
        if filename.endswith(ext):
            return True, f"Excluded file format: {ext}"

    # Lockfiles can be huge, skip them in favor of package.json / requirements.txt
    if filename in ("package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock"):
        return True, "Lockfile excluded to conserve token bounds"

    return False, None


def score_file_priority(path: str) -> int:
    """
    Ranks file priority:
    10: Manifests (package.json, requirements.txt, pyproject.toml)
    9: Architecture & routes (main.py, app.py, router, routes, server.js)
    8: Database & schema (models.py, schema.sql, migrations, prisma)
    7: Tests (test_*, *.test.js, *.spec.ts)
    6: Deployment & config (Dockerfile, workflows)
    5: Core application source files (*.py, *.js, *.jsx, *.ts, *.tsx, *.go, *.java)
    4: Documentation (README.md, ARCHITECTURE.md)
    1: Miscellaneous
    """
    lower = path.lower()
    base = lower.split("/")[-1]

    # Manifests
    if any(base == m or base.endswith(m) for m in MANIFEST_PATTERNS):
        return 10

    # API routes / Main entrypoints
    if any(k in lower for k in ("main.py", "app.py", "server.js", "server.ts", "index.js", "index.ts", "routes/", "controllers/", "api/")):
        return 9

    # Database & Schema
    if any(k in lower for k in ("models.py", "schema", "database.py", "db.ts", "migrations", "prisma")):
        return 8

    # Tests
    if any(k in lower for k in ("test_", "_test.", ".test.", ".spec.", "tests/", "__tests__/")):
        return 7

    # Deployment / Infra
    if any(k in lower for k in ("dockerfile", "docker-compose", ".github/workflows", "k8s", "terraform")):
        return 6

    # README / Docs
    if base.startswith("readme"):
        return 5

    # General source files
    if any(base.endswith(ext) for ext in (".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java", ".cpp", ".cs")):
        return 4

    return 1


def filter_and_rank_tree(tree: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Filters repository tree down to high-signal files, sorted by priority.
    Returns (selected_file_items, skipped_reasons).
    """
    skipped_reasons = []
    candidates = []

    for item in tree:
        if item.get("type") != "blob":
            continue

        path = item.get("path", "")
        size = item.get("size", 0)

        is_excluded, reason = should_exclude_path(path)
        if is_excluded:
            skipped_reasons.append(f"{path} ({reason})")
            continue

        if size > MAX_FILE_SIZE_BYTES:
            skipped_reasons.append(f"{path} (Exceeds size limit {MAX_FILE_SIZE_BYTES // 1024}KB)")
            continue

        priority = score_file_priority(path)
        candidates.append((priority, size, item))

    # Sort candidates by priority descending, then smaller size first
    candidates.sort(key=lambda x: (-x[0], x[1]))

    selected = []
    total_bytes = 0
    for priority, size, item in candidates:
        if len(selected) >= MAX_FILES_TO_ANALYZE:
            skipped_reasons.append(f"{item.get('path')} (Exceeded max files count {MAX_FILES_TO_ANALYZE})")
            continue
        if total_bytes + size > MAX_TOTAL_ANALYZED_BYTES:
            skipped_reasons.append(f"{item.get('path')} (Exceeded total content limit {MAX_TOTAL_ANALYZED_BYTES // 1024}KB)")
            continue

        selected.append(item)
        total_bytes += size

    return selected, skipped_reasons


def sanitize_source_content(content: str) -> str:
    """Detects and redacts secrets/credentials from source code before passing to LLM."""
    sanitized = content
    # First redact key-value assignments
    sanitized = SECRET_PATTERNS[0].sub(r"\1: '[REDACTED_SECRET]'", sanitized)
    # Then redact standalone token matches
    for pattern in SECRET_PATTERNS[1:]:
        sanitized = pattern.sub("[REDACTED_SECRET]", sanitized)
    return sanitized
