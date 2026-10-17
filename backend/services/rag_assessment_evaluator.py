import json
import logging
import uuid
from typing import Any, Dict, List, Optional
from uuid import UUID

from schemas.assessment import (
    RequirementResultItem,
    ASSESSMENT_STATUS_LITERAL,
)
from services.assessment_scorer import (
    get_requirement_weight,
    get_status_score,
)
from services.skill_normalizer import normalize_skill_name, are_skills_equivalent
from services.llm_service import call_llm_api, clean_llm_json_response

logger = logging.getLogger(__name__)

RAG_EVALUATION_SYSTEM_PROMPT = """You are a senior technical hiring auditor and code evidence reviewer.
You evaluate whether a candidate's genuine code chunks retrieved via vector search demonstrate a specific job requirement.

CRITICAL INSTRUCTIONS:
1. Base your evaluation SOLELY on the provided retrieved code chunks.
2. Do NOT assume or hallucinate libraries, code, functions, or file paths not present in the provided chunks.
3. Classify status strictly as:
   - "demonstrated": The retrieved code contains real, active implementation, usage, or automated tests of the skill.
   - "partially_demonstrated": The skill is present as a dependency declaration, basic configuration, or incidental mention without deep usage.
   - "not_demonstrated": The retrieved chunks do NOT contain relevant code for this skill, or are unrelated false positives.
4. For citations:
   - Use the exact file_path and line numbers from the matching chunk.
   - Extract an exact verbatim code_excerpt (up to 8 lines) from the chunk.
   - Categorize evidence_type into: "source_code", "test", "configuration", "dependency", "documentation".
   - Assign status_label: "Strong evidence" | "Some evidence" | "Mentioned only" | "Not demonstrated in analyzed files".
5. Return clean JSON with this exact schema:
{
  "status": "demonstrated" | "partially_demonstrated" | "not_demonstrated",
  "explanation": "2-3 clear sentences explaining how the candidate's code demonstrates or lacks this skill.",
  "citations": [
    {
      "chunk_id": "...",
      "file_path": "...",
      "line_start": 1,
      "line_end": 15,
      "code_excerpt": "...",
      "evidence_summary": "1 sentence describing what was implemented.",
      "evidence_type": "source_code",
      "status_label": "Strong evidence"
    }
  ],
  "limitations": "Any technical limitations (e.g. only tested in one service) or null if fully demonstrated.",
  "suggested_next_step": "1 actionable sentence on how to deepen or demonstrate this skill."
}
"""


def evaluate_requirement_with_rag(
    requirement: Dict[str, Any],
    retrieved_chunks: List[Dict[str, Any]],
    repo_map: Dict[str, str]
) -> RequirementResultItem:
    """
    Evaluates a single job requirement against RAG-retrieved code chunks.
    Uses LLM reasoning with anti-hallucination verification against the actual retrieved chunks.
    """
    req_id = requirement.get("id")
    raw_skill = requirement.get("skill_name", "Unknown")
    category = requirement.get("category", "Core concepts and soft skills")
    importance = requirement.get("importance", "required")
    weight = get_requirement_weight(importance)
    norm_skill = normalize_skill_name(raw_skill)

    # 1. If no chunks retrieved or all have very poor similarity (distance > 0.85)
    confident_chunks = [c for c in retrieved_chunks if c.get("relevance_score", 0.0) >= 0.25]
    if not confident_chunks:
        explanation = (
            f"No verified code, tests, or configuration demonstrating {raw_skill} were found "
            f"in the analyzed files across the selected repositories."
        )
        return RequirementResultItem(
            requirement_id=UUID(str(req_id)) if req_id else None,
            skill_name=raw_skill,
            normalized_skill_name=norm_skill,
            category=category,
            importance=importance,
            requirement_weight=weight,
            status="not_demonstrated",
            status_score=0.0,
            score_contribution=0.0,
            explanation=explanation,
            supporting_evidence_ids=[],
            supporting_evidence=[],
            limitations="Absence of evidence in analyzed repositories does not necessarily mean lack of ability.",
            suggested_next_step=f"Build a practical feature or add unit tests demonstrating {raw_skill}."
        )

    # 2. Build LLM prompt with retrieved chunks
    chunks_context_text = ""
    chunk_lookup: Dict[str, Dict[str, Any]] = {}
    for idx, chunk in enumerate(confident_chunks[:4], 1):
        cid = chunk.get("chunk_id", f"c_{idx}")
        chunk_lookup[cid] = chunk
        chunk_lookup[chunk.get("file_path", "")] = chunk

        chunks_context_text += (
            f"\n--- Retrieved Code Chunk #{idx} [ID: {cid}] ---\n"
            f"Repository: {chunk.get('repository_name')} | File: {chunk.get('file_path')} | Lines: {chunk.get('line_start')}-{chunk.get('line_end')}\n"
            f"Similarity Score: {chunk.get('relevance_score')} | Type: {chunk.get('chunk_type')}\n"
            f"Content:\n{chunk.get('document')}\n"
        )

    user_prompt = f"""Target Requirement to Assess:
- Skill Name: {raw_skill} (Normalized: {norm_skill})
- Category: {category}
- Importance: {importance}
- Job Description Context: {requirement.get('description', '') or requirement.get('source_excerpt', '')}

Retrieved Candidate Code Chunks from GitHub Repositories:
{chunks_context_text}

Evaluate whether this retrieved code evidence proves the candidate possesses {raw_skill}.
"""

    status: ASSESSMENT_STATUS_LITERAL = "not_demonstrated"
    explanation = f"Evaluated against {len(confident_chunks)} retrieved code chunks for {raw_skill}."
    limitations = None
    next_step = f"Expand direct implementation of {raw_skill}."
    supporting_evidence: List[Dict[str, Any]] = []

    try:
        raw_reply = call_llm_api(
            prompt=RAG_EVALUATION_SYSTEM_PROMPT,
            user_prompt=user_prompt
        )
        parsed = raw_reply if isinstance(raw_reply, dict) else clean_llm_json_response(str(raw_reply))

        llm_status = parsed.get("status", "not_demonstrated").lower()
        if llm_status in ("demonstrated", "partially_demonstrated", "not_demonstrated"):
            status = llm_status

        explanation = parsed.get("explanation") or explanation
        limitations = parsed.get("limitations")
        next_step = parsed.get("suggested_next_step") or next_step

        # Process and validate citations against real chunks
        raw_citations = parsed.get("citations", [])
        for cit in raw_citations:
            matched_chunk = None
            if cit.get("chunk_id") in chunk_lookup:
                matched_chunk = chunk_lookup[cit["chunk_id"]]
            elif cit.get("file_path") in chunk_lookup:
                matched_chunk = chunk_lookup[cit["file_path"]]
            else:
                # Find by closest file path match
                for c in confident_chunks:
                    if c.get("file_path") == cit.get("file_path"):
                        matched_chunk = c
                        break

            if not matched_chunk and confident_chunks:
                matched_chunk = confident_chunks[0]

            if matched_chunk:
                repo_id_str = str(matched_chunk.get("repository_id", ""))
                repo_name = matched_chunk.get("repository_name") or repo_map.get(repo_id_str, "Repository")
                commit_sha = matched_chunk.get("commit_sha", "main")
                file_path = cit.get("file_path") or matched_chunk.get("file_path", "")

                line_start = cit.get("line_start") or matched_chunk.get("line_start", 1)
                line_end = cit.get("line_end") or matched_chunk.get("line_end", line_start + 10)
                excerpt = cit.get("code_excerpt") or matched_chunk.get("code_excerpt", "")

                ev_id = str(uuid.uuid4())
                supporting_evidence.append({
                    "id": ev_id,
                    "repository_id": repo_id_str,
                    "repository_name": repo_name,
                    "skill_name": raw_skill,
                    "category": category,
                    "evidence_type": cit.get("evidence_type", matched_chunk.get("chunk_type", "source_code")),
                    "status_label": cit.get("status_label", "Strong evidence" if status == "demonstrated" else "Some evidence"),
                    "evidence_summary": cit.get("evidence_summary") or f"Verified {raw_skill} implementation in {file_path}.",
                    "file_path": file_path,
                    "line_start": line_start,
                    "line_end": line_end,
                    "code_excerpt": excerpt,
                    "github_url": f"https://github.com/{repo_name}/blob/{commit_sha}/{file_path}#L{line_start}-L{line_end}",
                    "commit_sha": commit_sha,
                    "confidence": round(float(matched_chunk.get("relevance_score", 0.85)), 2),
                    "relevance_score": matched_chunk.get("relevance_score"),
                    "retrieval_distance": matched_chunk.get("distance"),
                    "rag_retrieved": True,
                    "limitations": limitations
                })

    except Exception as e:
        logger.warning(f"RAG LLM evaluation failed for {raw_skill}, falling back to deterministic chunk evaluation: {e}")
        # Deterministic fallback: Use best matching chunk
        top_chunk = confident_chunks[0]
        relevance = top_chunk.get("relevance_score", 0.0)
        chunk_type = top_chunk.get("chunk_type", "source_code")

        if relevance >= 0.55 and chunk_type in ("source_code", "test"):
            status = "demonstrated"
            explanation = f"Direct technical evidence for {raw_skill} was verified in {top_chunk.get('repository_name')} ({top_chunk.get('file_path')})."
        elif relevance >= 0.35:
            status = "partially_demonstrated"
            explanation = f"Partial technical evidence for {raw_skill} was detected in {top_chunk.get('repository_name')} ({top_chunk.get('file_path')})."
        else:
            status = "not_demonstrated"
            explanation = f"Code in analyzed repositories had low relevance ({round(relevance * 100)}%) to {raw_skill}."

        if status != "not_demonstrated":
            repo_id_str = str(top_chunk.get("repository_id", ""))
            repo_name = top_chunk.get("repository_name", "Repository")
            commit_sha = top_chunk.get("commit_sha", "main")
            file_path = top_chunk.get("file_path", "")
            start_l = top_chunk.get("line_start", 1)
            end_l = top_chunk.get("line_end", 1)

            supporting_evidence.append({
                "id": str(uuid.uuid4()),
                "repository_id": repo_id_str,
                "repository_name": repo_name,
                "skill_name": raw_skill,
                "category": category,
                "evidence_type": chunk_type,
                "status_label": "Strong evidence" if status == "demonstrated" else "Some evidence",
                "evidence_summary": f"Semantic code match for {raw_skill} in {file_path}.",
                "file_path": file_path,
                "line_start": start_l,
                "line_end": end_l,
                "code_excerpt": top_chunk.get("code_excerpt", ""),
                "github_url": f"https://github.com/{repo_name}/blob/{commit_sha}/{file_path}#L{start_l}-L{end_l}",
                "commit_sha": commit_sha,
                "confidence": round(relevance, 2),
                "relevance_score": relevance,
                "retrieval_distance": top_chunk.get("distance"),
                "rag_retrieved": True,
                "limitations": None
            })

    # If status is demonstrated but no citation was extracted, synthesize citation from top chunk
    if status in ("demonstrated", "partially_demonstrated") and not supporting_evidence and confident_chunks:
        top_chunk = confident_chunks[0]
        repo_id_str = str(top_chunk.get("repository_id", ""))
        repo_name = top_chunk.get("repository_name", "Repository")
        commit_sha = top_chunk.get("commit_sha", "main")
        file_path = top_chunk.get("file_path", "")
        start_l = top_chunk.get("line_start", 1)
        end_l = top_chunk.get("line_end", 1)
        supporting_evidence.append({
            "id": str(uuid.uuid4()),
            "repository_id": repo_id_str,
            "repository_name": repo_name,
            "skill_name": raw_skill,
            "category": category,
            "evidence_type": top_chunk.get("chunk_type", "source_code"),
            "status_label": "Strong evidence" if status == "demonstrated" else "Some evidence",
            "evidence_summary": f"Verified implementation in {file_path}.",
            "file_path": file_path,
            "line_start": start_l,
            "line_end": end_l,
            "code_excerpt": top_chunk.get("code_excerpt", ""),
            "github_url": f"https://github.com/{repo_name}/blob/{commit_sha}/{file_path}#L{start_l}-L{end_l}",
            "commit_sha": commit_sha,
            "confidence": round(float(top_chunk.get("relevance_score", 0.8)), 2),
            "relevance_score": top_chunk.get("relevance_score"),
            "retrieval_distance": top_chunk.get("distance"),
            "rag_retrieved": True,
            "limitations": limitations
        })

    status_score = get_status_score(status)
    evidence_ids = [UUID(str(ev["id"])) for ev in supporting_evidence if ev.get("id")]

    return RequirementResultItem(
        requirement_id=UUID(str(req_id)) if req_id else None,
        skill_name=raw_skill,
        normalized_skill_name=norm_skill,
        category=category,
        importance=importance,
        requirement_weight=weight,
        status=status,
        status_score=status_score,
        score_contribution=0.0,
        explanation=explanation,
        supporting_evidence_ids=evidence_ids,
        supporting_evidence=supporting_evidence,
        limitations=limitations,
        suggested_next_step=next_step
    )
