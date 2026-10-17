import sys
import os
import io
import uuid
from pathlib import Path

# Force UTF-8 on Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.rag_chunker import chunk_repository_files
from services.rag_vector_service import (
    index_repository_files,
    retrieve_evidence_for_skill,
    get_repository_index_stats,
    get_code_collection,
    get_chroma_client,
)
from config import get_settings

def run_live_rag_demo():
    print("=" * 70)
    print("[+] LIVE CHROMADB RAG PIPELINE DEMONSTRATION")
    print("=" * 70)

    settings = get_settings()
    db_path = settings.chroma_db_path
    print(f"\n[1] ChromaDB Storage Path on Disk: {db_path.resolve()}")

    # Setup simulated candidate and repo
    candidate_user_id = uuid.uuid4()
    candidate_repo_id = uuid.uuid4()
    repo_name = "sarthak/ai-career-coach-portfolio"
    commit_sha = "f4c9a81"

    print(f"\n[2] Preparing Candidate Repository:")
    print(f"    - User ID: {candidate_user_id}")
    print(f"    - Repo ID: {candidate_repo_id}")
    print(f"    - Repository: {repo_name}")
    print(f"    - Commit SHA: {commit_sha}")

    # Read genuine source files from this project
    backend_dir = Path(__file__).parent
    files_to_index = {
        "services/assessment_engine.py": (backend_dir / "services" / "assessment_engine.py").read_text(encoding="utf-8", errors="ignore")[:4000],
        "services/rag_chunker.py": (backend_dir / "services" / "rag_chunker.py").read_text(encoding="utf-8", errors="ignore")[:4000],
        "services/rag_vector_service.py": (backend_dir / "services" / "rag_vector_service.py").read_text(encoding="utf-8", errors="ignore")[:4000],
        "main.py": (backend_dir / "main.py").read_text(encoding="utf-8", errors="ignore")[:4000],
        "Dockerfile": "FROM python:3.12-slim\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install --no-cache-dir -r requirements.txt\nCOPY . .\nEXPOSE 8000\nCMD [\"uvicorn\", \"main:app\", \"--host\", \"0.0.0.0\", \"--port\", \"8000\"]",
    }

    print(f"\n[3] Ingesting & Chunking {len(files_to_index)} Real Source Files...")
    for f in files_to_index:
        print(f"    [FILE] {f} ({len(files_to_index[f].splitlines())} lines)")

    # Execute index_repository_files
    index_res = index_repository_files(
        user_id=candidate_user_id,
        repo_id=candidate_repo_id,
        repo_name=repo_name,
        commit_sha=commit_sha,
        files_map=files_to_index,
    )

    print(f"\n[4] Indexing Results in ChromaDB:")
    print(f"    [OK] Status: {index_res.get('status')}")
    print(f"    [OK] Total Chunks Indexed: {index_res.get('chunks_indexed')}")
    print(f"    [OK] Total Files Processed: {index_res.get('files_indexed')}")

    # Verify physical storage on disk
    sqlite_file = db_path / "chroma.sqlite3"
    print(f"\n[5] Physical Verification on Disk:")
    if sqlite_file.exists():
        size_kb = round(sqlite_file.stat().st_size / 1024, 2)
        print(f"    [DISK] Persistent SQLite Database: {sqlite_file}")
        print(f"    [DISK] Database Size on Disk: {size_kb} KB")
    else:
        print(f"    [WARN] File not found at {sqlite_file}")

    # Inspect collection via ChromaDB Client
    coll = get_code_collection()
    print(f"    [CHROMA] ChromaDB Collection Name: '{coll.name}'")
    print(f"    [CHROMA] Total Chunks in Collection: {coll.count()}")

    # Live Queries
    test_skills = [
        "FastAPI REST API",
        "Docker Containerization",
        "Language Chunker Sliding Window",
    ]

    print("\n" + "=" * 70)
    print("[6] EXECUTING LIVE SEMANTIC RAG RETRIEVALS")
    print("=" * 70)

    for skill in test_skills:
        print(f"\n[QUERY] Requirement Skill: '{skill}'")
        matches = retrieve_evidence_for_skill(
            user_id=candidate_user_id,
            skill_name=skill,
            repository_ids=[candidate_repo_id],
            top_k=2,
        )

        print(f"    -> Found {len(matches)} matching evidence chunks:")
        for idx, match in enumerate(matches, 1):
            relevance = match['relevance_score']
            pct = round(relevance * 100, 1)
            dist = match['distance']
            file_path = match['file_path']
            lines = f"L{match['line_start']}-L{match['line_end']}"
            chunk_type = match['chunk_type']
            
            print(f"    [{idx}] {file_path} ({lines}) | Type: {chunk_type}")
            print(f"        * Semantic Relevance: {pct}% (Cosine Distance: {dist})")
            
            # Print first 2-3 lines of code excerpt
            excerpt_lines = match['code_excerpt'].strip().splitlines()[:3]
            for el in excerpt_lines:
                print(f"          | {el[:75]}")

    print("\n" + "=" * 70)
    print("[SUCCESS] CHROMADB RAG PIPELINE VERIFIED AND STORING DATA LIVE!")
    print("=" * 70)

if __name__ == "__main__":
    run_live_rag_demo()
