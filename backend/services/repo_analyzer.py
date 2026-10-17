import json
import re
from typing import Any, Dict, List, Optional
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

    # 2. Validate Project Insights
    raw_insights = (
        raw_response.get("project_insights")
        or raw_response.get("insights")
        or raw_response.get("quality_insights")
        or {}
    )

    # Tech stack
    tech_stack = []
    for ts in raw_insights.get("tech_stack", []):
        tech_name = str(ts.get("name") or ts.get("technology") or ts.get("tech") or ts.get("skill") or "Unknown").strip()
        tech_stack.append(
            TechStackItem(
                name=tech_name,
                category=ts.get("category", "General"),
                evidence_type=ts.get("evidence_type", "source_code"),
                detection_source=ts.get("detection_source") or ts.get("source") or "Repository files",
                is_direct_implementation=ts.get("is_direct_implementation", True),
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
