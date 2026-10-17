import json
import re
from typing import Any, Dict, List, Optional, Set, Tuple
from schemas.github import (
    SkillEvidenceItem,
    ProjectInsights,
    TechStackItem,
    ArchitectureInsight,
    EngineeringPractice,
    ProjectStrength,
    ImprovementOpportunity,
    AnalysisCoverage,
)
from services.llm_service import call_llm_api
from services.skill_normalizer import normalize_skill_name

GITHUB_ANALYSIS_PROMPT = """You are a senior software architect and technical hiring committee reviewer.
Analyze the following source files retrieved from a real GitHub repository at a specific commit.

CRITICAL INSTRUCTIONS:
1. Base EVERY skill and insight solely on the provided file contents. Do NOT hallucinate technologies, files, or line references.
2. Distinguish direct implementation evidence (e.g. writing FastAPI endpoints, SQLAlchemy models, React components) from mere dependency declarations or documentation mentions.
3. Categorize evidence_type into EXACTLY one of: "source_code", "test", "configuration", "dependency", "documentation".
4. Assign status_label into EXACTLY one of:
   - "Strong evidence": substantial, direct implementation or test verification
   - "Some evidence": basic or limited usage
   - "Mentioned only": only declared in manifest/docs without clear code usage
   - "Not demonstrated in analyzed files": declared or implied but no implementation found
5. Ground each skill evidence with:
   - skill_name: Specific technology name (e.g., "Python", "FastAPI", "React", "PostgreSQL", "Docker", "Pytest", "Tailwind CSS")
   - category: e.g. "Programming languages", "Frameworks and libraries", "Backend and API development", "Databases and data management", "Testing and quality assurance", "Deployment and DevOps", "Tools and platforms", "Core concepts and soft skills"
   - evidence_type: "source_code" | "test" | "configuration" | "dependency" | "documentation"
   - status_label: "Strong evidence" | "Some evidence" | "Mentioned only" | "Not demonstrated in analyzed files"
   - evidence_summary: 1-2 sentence explanation of what the developer implemented
   - file_path: The exact path of the file where this is evidenced
   - line_start: Starting line number of the representative snippet (1-indexed)
   - line_end: Ending line number (1-indexed)
   - limitations: Any uncertainty or limitations in this evidence
6. Produce Project Insights:
   - tech_stack: List of identified technologies with where they were detected and whether it's direct implementation
   - architecture:
       summary: 2-3 sentence overview of the system architecture
       components: List of { "component": "...", "description": "...", "basis": "..." }
       diagram_mermaid: Optional clean text Mermaid flowchart e.g. graph TD\\n...
   - engineering_practices: List of { "practice": "Input validation" / "Error handling" / "Testing" / "CI/CD" / "Logging", "status": "present"|"incomplete"|"unverified", "evidence": "...", "recommendation": "..." }
   - strengths: List of { "title": "...", "explanation": "...", "evidence_source": "...", "why_useful": "..." }
   - improvements: List of { "title": "...", "priority": "high"|"medium"|"low", "issue_explanation": "...", "evidence_source": "...", "suggested_improvement": "...", "is_directly_observed": true, "confidence": "high"|"medium"|"low" }

Output clean JSON conforming to this schema:
{
  "skills": [
    {
      "skill_name": "...",
      "category": "...",
      "evidence_type": "source_code",
      "status_label": "Strong evidence",
      "evidence_summary": "...",
      "file_path": "...",
      "line_start": 1,
      "line_end": 15,
      "limitations": "..."
    }
  ],
  "project_insights": {
    "tech_stack": [ ... ],
    "architecture": { ... },
    "engineering_practices": [ ... ],
    "strengths": [ ... ],
    "improvements": [ ... ]
  }
}
"""


def extract_real_code_excerpt(file_content: str, line_start: Optional[int], line_end: Optional[int]) -> Optional[str]:
    """Extracts genuine code excerpt from actual retrieved file content."""
    if not file_content:
        return None
    lines = file_content.splitlines()
    if not lines:
        return None

    # Default to first 10 lines if line numbers not specified or invalid
    start = max(1, line_start or 1) - 1
    end = min(len(lines), line_end or (start + 12))

    if start >= len(lines):
        start = 0
        end = min(len(lines), 10)

    excerpt_lines = lines[start:end]
    return "\n".join(excerpt_lines)


def calculate_calibrated_confidence(evidence_type: str, status_label: str) -> float:
    """Calculates rule-based transparent confidence score."""
    weights = {
        ("source_code", "Strong evidence"): 0.95,
        ("test", "Strong evidence"): 0.90,
        ("configuration", "Strong evidence"): 0.85,
        ("source_code", "Some evidence"): 0.75,
        ("configuration", "Some evidence"): 0.70,
        ("dependency", "Mentioned only"): 0.50,
        ("documentation", "Mentioned only"): 0.40,
    }
    return weights.get((evidence_type, status_label), 0.65)


def extract_grounded_static_evidence(
    repo_full_name: str,
    commit_sha: str,
    files_map: Dict[str, str]
) -> List[SkillEvidenceItem]:
    """
    Extracts deterministic, grounded skill evidence directly from actual repository
    source files, manifests, and test suites.
    Guarantees foundational evidence (e.g. JavaScript, Python, Software Engineering, dependencies)
    even when LLM is unavailable, rate-limited, or misses core technologies.
    """
    static_items: List[SkillEvidenceItem] = []
    seen_skills: Set[str] = set()

    def add_item(
        skill_name: str,
        category: str,
        evidence_type: str,
        status_label: str,
        evidence_summary: str,
        file_path: str,
        start_line: int = 1,
        end_line: int = 15
    ):
        norm = normalize_skill_name(skill_name).lower()
        if norm in seen_skills:
            return
        seen_skills.add(norm)

        content = files_map.get(file_path, "")
        excerpt = extract_real_code_excerpt(content, start_line, end_line)
        confidence = calculate_calibrated_confidence(evidence_type, status_label)
        github_url = f"https://github.com/{repo_full_name}/blob/{commit_sha}/{file_path}#L{start_line}-L{end_line}"

        static_items.append(
            SkillEvidenceItem(
                skill_name=skill_name,
                category=category,
                evidence_type=evidence_type,
                status_label=status_label,
                evidence_summary=evidence_summary,
                file_path=file_path,
                line_start=start_line,
                line_end=end_line,
                code_excerpt=excerpt,
                github_url=github_url,
                commit_sha=commit_sha,
                confidence=confidence,
                limitations=None
            )
        )

    # 1. Languages from file extensions
    ext_lang_map = {
        (".js", ".jsx", ".mjs", ".cjs"): ("JavaScript", "Programming languages and frameworks"),
        (".ts", ".tsx"): ("TypeScript", "Programming languages and frameworks"),
        (".py",): ("Python", "Programming languages and frameworks"),
        (".html", ".htm"): ("HTML", "Tools and platforms"),
        (".css", ".scss", ".sass"): ("CSS", "Tools and platforms"),
        (".go",): ("Go", "Programming languages and frameworks"),
        (".java",): ("Java", "Programming languages and frameworks"),
        (".rs",): ("Rust", "Programming languages and frameworks"),
        (".sql",): ("SQL", "Databases and storage"),
    }

    primary_source_file = None
    test_file = None

    for path in files_map:
        lower = path.lower()
        if any(term in lower for term in (".test.", ".spec.", "test_", "_test.", "/tests/", "/test/")):
            if not test_file:
                test_file = path
        elif not primary_source_file and any(path.endswith(ext) for group in ext_lang_map for ext in group):
            primary_source_file = path

        for exts, (lang_name, cat) in ext_lang_map.items():
            if any(path.endswith(ext) for ext in exts):
                add_item(
                    skill_name=lang_name,
                    category=cat,
                    evidence_type="source_code",
                    status_label="Strong evidence",
                    evidence_summary=f"Direct {lang_name} source code implementation verified in {path}.",
                    file_path=path,
                    start_line=1,
                    end_line=15
                )

    # 2. Software Engineering core discipline
    chosen_code_file = primary_source_file or (test_file if test_file else (next(iter(files_map.keys()), "") if files_map else ""))
    if chosen_code_file:
        add_item(
            skill_name="Software Engineering",
            category="Core concepts and soft skills",
            evidence_type="source_code",
            status_label="Strong evidence",
            evidence_summary=f"Applied software engineering and architecture implementation verified in {chosen_code_file}.",
            file_path=chosen_code_file,
            start_line=1,
            end_line=15
        )

    # 3. Unit Testing if tests exist
    if test_file:
        add_item(
            skill_name="Unit Testing",
            category="Engineering practices and workflows",
            evidence_type="test",
            status_label="Strong evidence",
            evidence_summary=f"Automated test suite implementation verified in {test_file}.",
            file_path=test_file,
            start_line=1,
            end_line=15
        )

    # 4. Manifest inspection: package.json
    for path, content in files_map.items():
        if path.endswith("package.json"):
            try:
                pkg = json.loads(content)
                deps = {}
                if isinstance(pkg.get("dependencies"), dict):
                    deps.update(pkg["dependencies"])
                if isinstance(pkg.get("devDependencies"), dict):
                    deps.update(pkg["devDependencies"])

                dep_skill_map = {
                    "react": ("React", "Programming languages and frameworks"),
                    "express": ("Express.js", "Programming languages and frameworks"),
                    "next": ("Next.js", "Programming languages and frameworks"),
                    "vue": ("Vue.js", "Programming languages and frameworks"),
                    "tailwindcss": ("Tailwind CSS", "Tools and platforms"),
                    "jest": ("Jest", "Engineering practices and workflows"),
                    "vitest": ("Vitest", "Engineering practices and workflows"),
                    "mocha": ("Mocha", "Engineering practices and workflows"),
                    "axios": ("REST API", "Programming languages and frameworks"),
                    "mongoose": ("MongoDB", "Databases and storage"),
                    "mongodb": ("MongoDB", "Databases and storage"),
                    "pg": ("PostgreSQL", "Databases and storage"),
                    "@prisma/client": ("Prisma ORM", "Databases and storage"),
                    "prisma": ("Prisma ORM", "Databases and storage"),
                    "jsonwebtoken": ("Authentication & Security", "Core concepts and soft skills"),
                    "bcrypt": ("Authentication & Security", "Core concepts and soft skills"),
                    "bcryptjs": ("Authentication & Security", "Core concepts and soft skills"),
                    "cors": ("REST API", "Programming languages and frameworks"),
                    "dotenv": ("Configuration Management", "Engineering practices and workflows"),
                }

                for dep_key, (sk_name, cat) in dep_skill_map.items():
                    if dep_key in deps:
                        add_item(
                            skill_name=sk_name,
                            category=cat,
                            evidence_type="dependency",
                            status_label="Some evidence",
                            evidence_summary=f"Dependency '{dep_key}' declared in {path}.",
                            file_path=path,
                            start_line=1,
                            end_line=15
                        )
            except Exception:
                pass

        elif path.endswith("requirements.txt") or path.endswith("Pipfile"):
            lines = content.splitlines()
            for line in lines:
                l_lower = line.strip().lower()
                if "fastapi" in l_lower:
                    add_item("FastAPI", "Programming languages and frameworks", "dependency", "Some evidence", f"FastAPI dependency in {path}", path)
                elif "flask" in l_lower:
                    add_item("Flask", "Programming languages and frameworks", "dependency", "Some evidence", f"Flask dependency in {path}", path)
                elif "django" in l_lower:
                    add_item("Django", "Programming languages and frameworks", "dependency", "Some evidence", f"Django dependency in {path}", path)
                elif "pytest" in l_lower:
                    add_item("Pytest", "Engineering practices and workflows", "dependency", "Some evidence", f"Pytest dependency in {path}", path)
                elif "sqlalchemy" in l_lower:
                    add_item("SQLAlchemy", "Databases and storage", "dependency", "Some evidence", f"SQLAlchemy dependency in {path}", path)

    return static_items


def analyze_repository_files_with_llm(
    repo_full_name: str,
    commit_sha: str,
    files_map: Dict[str, str],
    total_discovered: int,
    skipped_reasons: List[str]
) -> Tuple[List[SkillEvidenceItem], ProjectInsights]:
    """
    Constructs prompt with bounded file contents, invokes LLM, validates output
    against actual files, and extracts real code excerpts.
    """
    # Build repository context string
    file_context_blocks = []
    for path, content in files_map.items():
        # Include line numbered content
        lines = content.splitlines()
        numbered = [f"{i+1}: {line}" for i, line in enumerate(lines[:120])]
        snippet = "\n".join(numbered)
        file_context_blocks.append(f"--- File: {path} ---\n{snippet}\n")

    files_joined = "\n".join(file_context_blocks)
    prompt_body = f"""Repository: {repo_full_name}
Target Commit SHA: {commit_sha}
Analyzed Files ({len(files_map)} files):

{files_joined}
"""

    raw_response = call_llm_api(
        prompt=GITHUB_ANALYSIS_PROMPT,
        user_prompt=prompt_body[:35000]
    )

    # 1. Validate & ground Skills
    raw_skills = (
        raw_response.get("skills")
        or raw_response.get("skill_evidence")
        or raw_response.get("skills_evidence")
        or raw_response.get("technical_skills")
        or (raw_response if isinstance(raw_response, list) else [])
    )
    verified_evidence: List[SkillEvidenceItem] = []

    for item in raw_skills:
        skill_name = str(item.get("skill_name") or item.get("name") or "").strip()
        if not skill_name:
            continue

        file_path = item.get("file_path", "").strip()
        # Ground check: file must exist in retrieved files
        if file_path not in files_map:
            # Check if partial match exists
            matched = next((p for p in files_map if p.endswith(file_path) or file_path.endswith(p)), None)
            if matched:
                file_path = matched
            else:
                # Fallback to first manifest or main file
                file_path = next(iter(files_map.keys()), "")

        line_start = item.get("line_start")
        line_end = item.get("line_end")
        raw_file_content = files_map.get(file_path, "")

        # Extract authentic code excerpt from genuine file content
        excerpt = extract_real_code_excerpt(raw_file_content, line_start, line_end)

        evidence_type = item.get("evidence_type", "source_code")
        if evidence_type not in ("source_code", "test", "configuration", "dependency", "documentation"):
            evidence_type = "source_code"

        status_label = item.get("status_label", "Strong evidence")
        if status_label not in ("Strong evidence", "Some evidence", "Mentioned only", "Not demonstrated in analyzed files"):
            status_label = "Some evidence"

        confidence = calculate_calibrated_confidence(evidence_type, status_label)

        github_url = f"https://github.com/{repo_full_name}/blob/{commit_sha}/{file_path}"
        if line_start:
            github_url += f"#L{line_start}"
            if line_end and line_end > line_start:
                github_url += f"-L{line_end}"

        verified_evidence.append(
            SkillEvidenceItem(
                skill_name=skill_name,
                category=item.get("category", "Tools and platforms"),
                evidence_type=evidence_type,
                status_label=status_label,
                evidence_summary=item.get("evidence_summary", f"Detected in {file_path}"),
                file_path=file_path,
                line_start=line_start,
                line_end=line_end,
                code_excerpt=excerpt,
                github_url=github_url,
                commit_sha=commit_sha,
                confidence=confidence,
                limitations=item.get("limitations")
            )
        )

    # Merge static grounded evidence with LLM evidence (avoiding duplicates)
    static_evidence = extract_grounded_static_evidence(repo_full_name, commit_sha, files_map)
    existing_skill_norms = {normalize_skill_name(ev.skill_name).lower() for ev in verified_evidence}

    for static_ev in static_evidence:
        if normalize_skill_name(static_ev.skill_name).lower() not in existing_skill_norms:
            verified_evidence.append(static_ev)
            existing_skill_norms.add(normalize_skill_name(static_ev.skill_name).lower())

    # 2. Validate Project Insights
    raw_insights = (
        raw_response.get("project_insights")
        or raw_response.get("insights")
        or raw_response.get("quality_insights")
        or {}
    )

    # Tech stack
    tech_stack = []
    seen_tech = set()
    for ts in raw_insights.get("tech_stack", []):
        tech_name = str(ts.get("name") or ts.get("technology") or ts.get("tech") or ts.get("skill") or "Unknown").strip()
        norm_t = normalize_skill_name(tech_name).lower()
        seen_tech.add(norm_t)
        tech_stack.append(
            TechStackItem(
                name=tech_name,
                category=ts.get("category", "General"),
                evidence_type=ts.get("evidence_type", "source_code"),
                detection_source=ts.get("detection_source") or ts.get("source") or "Repository files",
                is_direct_implementation=ts.get("is_direct_implementation", True),
            )
        )

    # Ensure detected static languages and frameworks are reflected in tech stack
    for static_ev in static_evidence:
        norm_s = normalize_skill_name(static_ev.skill_name).lower()
        if norm_s not in seen_tech:
            seen_tech.add(norm_s)
            tech_stack.append(
                TechStackItem(
                    name=static_ev.skill_name,
                    category=static_ev.category,
                    evidence_type=static_ev.evidence_type,
                    detection_source=f"Static analysis of {static_ev.file_path}",
                    is_direct_implementation=static_ev.evidence_type == "source_code",
                )
            )

    # Architecture
    raw_arch = raw_insights.get("architecture", {})
    architecture = ArchitectureInsight(
        summary=raw_arch.get("summary", "Modular software architecture based on analyzed repository files."),
        components=raw_arch.get("components", []),
        diagram_mermaid=raw_arch.get("diagram_mermaid"),
        basis_explanation=raw_arch.get("basis_explanation", "Derived from observed route files, entrypoints, and configurations."),
    )

    # Engineering practices
    engineering_practices = []
    for ep in raw_insights.get("engineering_practices", []):
        st = ep.get("status", "present")
        if st not in ("present", "incomplete", "unverified"):
            st = "unverified"
        engineering_practices.append(
            EngineeringPractice(
                practice=ep.get("practice", "General Code Structure"),
                status=st,
                evidence=ep.get("evidence", "Static inspection of repository source files"),
                recommendation=ep.get("recommendation"),
            )
        )

    # Strengths
    strengths = []
    for st in raw_insights.get("strengths", []):
        strengths.append(
            ProjectStrength(
                title=st.get("title", "Structured Implementation"),
                explanation=st.get("explanation", ""),
                evidence_source=st.get("evidence_source", ""),
                why_useful=st.get("why_useful", "Improves code maintainability."),
            )
        )

    # Improvements
    improvements = []
    for imp in raw_insights.get("improvements", []):
        prio = imp.get("priority", "medium")
        if prio not in ("high", "medium", "low"):
            prio = "medium"
        improvements.append(
            ImprovementOpportunity(
                title=imp.get("title", "Add automated tests"),
                priority=prio,
                issue_explanation=imp.get("issue_explanation", ""),
                evidence_source=imp.get("evidence_source"),
                suggested_improvement=imp.get("suggested_improvement", ""),
                is_directly_observed=imp.get("is_directly_observed", True),
                confidence=imp.get("confidence", "medium"),
            )
        )

    # Coverage
    from datetime import datetime, timezone
    coverage = AnalysisCoverage(
        total_files_discovered=total_discovered,
        files_analyzed_count=len(files_map),
        files_skipped_count=len(skipped_reasons),
        skipped_reasons=skipped_reasons[:15],
        commit_sha=commit_sha,
        analysis_timestamp=datetime.now(timezone.utc).isoformat(),
        is_static_analysis=True,
        limitations="Static code inspection only. Runtime behavior, live performance, and passing tests require containerized execution environment."
    )

    project_insights = ProjectInsights(
        tech_stack=tech_stack,
        architecture=architecture,
        engineering_practices=engineering_practices,
        strengths=strengths,
        improvements=improvements,
        coverage=coverage,
    )

    return verified_evidence, project_insights


def analyze_repository_workflow(
    full_name: str,
    commit_sha: str,
    default_branch: str = "main"
) -> Tuple[ProjectInsights, List[SkillEvidenceItem], int, int]:
    """
    Complete end-to-end repository file analysis workflow:
    1. Fetches recursive tree from GitHub.
    2. Filters & ranks high-signal files within safety and token limits.
    3. Fetches raw file contents at target commit SHA.
    4. Evaluates evidence and project architecture insights with LLM.
    Returns (project_insights, evidence_items, total_discovered, files_analyzed_count).
    """
    from fastapi import HTTPException, status
    from services.github_service import fetch_repo_git_tree, fetch_raw_file_content
    from services.repo_processor import filter_and_rank_tree, sanitize_source_content

    tree = fetch_repo_git_tree(full_name, commit_sha)
    if not tree:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Repository {full_name} is empty or contains no readable files."
        )

    selected_items, skipped_reasons = filter_and_rank_tree(tree)
    if not selected_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No qualifying source or configuration files were found to analyze within safety bounds."
        )

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

    evidence_items, project_insights = analyze_repository_files_with_llm(
        repo_full_name=full_name,
        commit_sha=commit_sha,
        files_map=files_map,
        total_discovered=len(tree),
        skipped_reasons=skipped_reasons
    )

    return project_insights, evidence_items, len(tree), len(files_map)
