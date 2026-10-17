import os
import shutil
import tempfile
import uuid
from unittest.mock import patch, MagicMock

import pytest

from services.rag_chunker import (
    detect_file_language,
    determine_chunk_type,
    chunk_code_file,
    chunk_repository_files,
)
from services.rag_vector_service import (
    index_repository_files,
    retrieve_evidence_for_skill,
    delete_repository_index,
    get_repository_index_stats,
    get_code_collection,
)
from services.rag_assessment_evaluator import (
    evaluate_requirement_with_rag,
)
from schemas.assessment import RequirementResultItem


# ─── 1. CODE CHUNKER TESTS ───

def test_detect_file_language():
    assert detect_file_language("backend/main.py") == "python"
    assert detect_file_language("frontend/src/App.jsx") == "javascript"
    assert detect_file_language("frontend/src/types.ts") == "typescript"
    assert detect_file_language("docker-compose.yml") == "yaml"
    assert detect_file_language("package.json") == "json"
    assert detect_file_language("schema.sql") == "sql"
    assert detect_file_language("Dockerfile") == "dockerfile"
    assert detect_file_language("README.md") == "markdown"
    assert detect_file_language("unknown.xyz") == "text"


def test_determine_chunk_type():
    assert determine_chunk_type("tests/test_api.py") == "test"
    assert determine_chunk_type("requirements.txt") == "dependency"
    assert determine_chunk_type("package.json") == "dependency"
    assert determine_chunk_type("docker-compose.yml") == "config"
    assert determine_chunk_type("docs/api.md") == "documentation"
    assert determine_chunk_type("README.md") == "documentation"
    assert determine_chunk_type("services/engine.py") == "source_code"


def test_chunk_code_file_preserves_lines_and_metadata():
    # Construct a sample python file with 80 lines
    code_lines = [f"def function_{i}():\n    return {i}\n" for i in range(40)]
    content = "".join(code_lines)

    chunks = chunk_code_file(
        file_path="services/calculator.py",
        content=content,
        repo_id=str(uuid.uuid4()),
        repo_name="demo-repo",
        commit_sha="abcdef123456",
        user_id=str(uuid.uuid4()),
        chunk_size_lines=30,
        overlap_lines=10,
    )

    assert len(chunks) > 1
    # Check first chunk structure
    first = chunks[0]
    assert "id" in first
    assert "document" in first
    assert "calculator.py" in first["document"]
    
    meta = first["metadata"]
    assert meta["file_path"] == "services/calculator.py"
    assert meta["language"] == "python"
    assert meta["start_line"] == 1
    assert meta["end_line"] > 1
    assert meta["commit_sha"] == "abcdef123456"
    assert meta["chunk_type"] == "source_code"


def test_chunk_repository_files_generates_all_chunks():
    files_map = {
        "services/user_service.py": "class UserService:\n    pass\n",
        "tests/test_user.py": "def test_user():\n    assert True\n",
        "package.json": '{\n  "dependencies": {\n    "react": "^18.0.0"\n  }\n}\n',
    }

    chunks = chunk_repository_files(
        files_map=files_map,
        repo_id=str(uuid.uuid4()),
        repo_name="org/my-project",
        commit_sha="c123456",
        user_id=str(uuid.uuid4()),
    )

    paths = {c["metadata"]["file_path"] for c in chunks}
    assert "services/user_service.py" in paths
    assert "tests/test_user.py" in paths
    assert "package.json" in paths


# ─── 2. CHROMADB VECTOR SERVICE TESTS ───

def test_chroma_vector_service_indexing_retrieval_and_purge():
    user_id = uuid.uuid4()
    repo_id = uuid.uuid4()

    files_map = {
        "services/auth.py": "def authenticate_jwt_token(token: str):\n    # JWT token authentication implementation\n    payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])\n    return payload\n",
        "services/db.py": "def get_db_connection():\n    # Postgres connection logic\n    return psycopg2.connect(DATABASE_URL)\n",
    }

    # 1. Index files
    res = index_repository_files(
        user_id=user_id,
        repo_id=repo_id,
        repo_name="test-org/auth-repo",
        commit_sha="sha111",
        files_map=files_map,
    )
    assert res["status"] == "completed"
    assert res["chunks_indexed"] >= 2

    # 2. Verify chunk count via stats
    stats = get_repository_index_stats(repo_id)
    assert stats["is_indexed"] is True
    assert stats["total_chunks"] >= 2

    # 3. Retrieve evidence for skill "JWT Authentication"
    matches = retrieve_evidence_for_skill(
        user_id=user_id,
        skill_name="JWT Authentication",
        repository_ids=[repo_id],
        top_k=2,
    )
    assert len(matches) > 0
    top = matches[0]
    assert "services/auth.py" in top["file_path"]
    assert "relevance_score" in top
    assert top["relevance_score"] > 0.0

    # 4. User isolation: Another user cannot retrieve these chunks
    other_user_id = uuid.uuid4()
    other_matches = retrieve_evidence_for_skill(
        user_id=other_user_id,
        skill_name="JWT Authentication",
        repository_ids=[repo_id],
        top_k=2,
    )
    assert len(other_matches) == 0

    # 5. Purge / Delete chunks
    deleted = delete_repository_index(repo_id)
    assert deleted is True
    post_stats = get_repository_index_stats(repo_id)
    assert post_stats["is_indexed"] is False
    assert post_stats["total_chunks"] == 0


# ─── 3. RAG ASSESSMENT EVALUATION TESTS ───

def test_evaluate_requirement_with_rag_deterministic_fallback():
    req = {
        "id": uuid.uuid4(),
        "skill_name": "Docker",
        "category": "DevOps",
        "importance": "required",
    }

    repo_id = uuid.uuid4()
    chunks = [
        {
            "chunk_id": "chk_docker_1",
            "repository_id": str(repo_id),
            "repository_name": "org/api-service",
            "commit_sha": "abc1234",
            "file_path": "Dockerfile",
            "line_start": 1,
            "line_end": 10,
            "code_excerpt": "FROM python:3.12-slim\nWORKDIR /app\nRUN pip install -r requirements.txt",
            "relevance_score": 0.82,
            "distance": 0.18,
            "chunk_type": "config",
            "language": "dockerfile",
        }
    ]

    # Without LLM or on LLM failure, evaluation uses deterministic fallback
    with patch("services.rag_assessment_evaluator.call_llm_api", side_effect=Exception("LLM unavailable")):
        result = evaluate_requirement_with_rag(
            requirement=req,
            retrieved_chunks=chunks,
            repo_map={str(repo_id): "api-service"},
        )

    assert isinstance(result, RequirementResultItem)
    assert result.skill_name == "Docker"
    assert result.status in ["demonstrated", "partially_demonstrated"]
    assert len(result.supporting_evidence) == 1
    assert result.supporting_evidence[0]["file_path"] == "Dockerfile"
    assert result.supporting_evidence[0]["rag_retrieved"] is True
    assert result.supporting_evidence[0]["relevance_score"] == 0.82


def test_evaluate_requirement_with_rag_llm_flow():
    req = {
        "id": uuid.uuid4(),
        "skill_name": "React",
        "category": "Frontend Development",
        "importance": "required",
    }

    repo_id = uuid.uuid4()
    chunks = [
        {
            "chunk_id": "chk_react_1",
            "repository_id": str(repo_id),
            "repository_name": "org/web-app",
            "commit_sha": "def5678",
            "file_path": "src/App.jsx",
            "line_start": 1,
            "line_end": 20,
            "code_excerpt": "import React, { useState, useEffect } from 'react'",
            "relevance_score": 0.91,
            "distance": 0.09,
            "chunk_type": "source_code",
            "language": "javascript",
        }
    ]

    mock_llm_reply = {
        "status": "demonstrated",
        "explanation": "Candidate demonstrates React via standard hooks and component composition in src/App.jsx.",
        "citations": [
            {
                "chunk_id": "chk_react_1",
                "file_path": "src/App.jsx",
                "line_start": 1,
                "line_end": 20,
                "code_excerpt": "import React, { useState, useEffect } from 'react'",
                "evidence_summary": "Active React component with hooks.",
                "evidence_type": "source_code",
                "status_label": "Strong evidence",
            }
        ],
        "limitations": None,
        "suggested_next_step": "Implement custom React hooks for stateful logic.",
    }

    with patch("services.rag_assessment_evaluator.call_llm_api", return_value=mock_llm_reply):
        result = evaluate_requirement_with_rag(
            requirement=req,
            retrieved_chunks=chunks,
            repo_map={str(repo_id): "web-app"},
        )

    assert isinstance(result, RequirementResultItem)
    assert result.skill_name == "React"
    assert result.status == "demonstrated"
    assert result.status_score == 1.0
    assert len(result.supporting_evidence) == 1
    assert result.supporting_evidence[0]["file_path"] == "src/App.jsx"
    assert result.supporting_evidence[0]["rag_retrieved"] is True
    assert result.supporting_evidence[0]["confidence"] == 0.91
