import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

import chromadb
from chromadb.config import Settings as ChromaSettings
from config import get_settings
from services.rag_chunker import chunk_repository_files

logger = logging.getLogger(__name__)

COLLECTION_NAME = "github_code_chunks"
_client: Optional[chromadb.PersistentClient] = None


def get_chroma_client() -> chromadb.PersistentClient:
    """Returns singleton persistent ChromaDB client."""
    global _client
    if _client is None:
        settings = get_settings()
        db_path = str(settings.chroma_db_path)
        logger.info(f"Initializing persistent ChromaDB client at: {db_path}")
        _client = chromadb.PersistentClient(
            path=db_path,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True,
            )
        )
    return _client


def get_code_collection() -> chromadb.Collection:
    """Retrieves or creates the primary code chunks collection configured with cosine space."""
    client = get_chroma_client()
    try:
        collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
        return collection
    except Exception as e:
        logger.error(f"Error accessing ChromaDB collection '{COLLECTION_NAME}': {e}")
        raise


def index_repository_files(
    user_id: UUID,
    repo_id: UUID,
    repo_name: str,
    commit_sha: str,
    files_map: Dict[str, str],
    batch_size: int = 50
) -> Dict[str, Any]:
    """
    Chunks and indexes repository source files into ChromaDB.
    Replaces any previous chunks for this repository to ensure atomic freshness.
    """
    if not files_map:
        return {
            "repository_id": str(repo_id),
            "chunks_indexed": 0,
            "files_indexed": 0,
            "status": "empty",
            "message": "No files provided for indexing"
        }

    collection = get_code_collection()
    repo_id_str = str(repo_id)
    user_id_str = str(user_id)

    # 1. Clean up stale chunks for this repository
    try:
        collection.delete(where={"repository_id": repo_id_str})
        logger.info(f"Purged previous vector chunks for repo {repo_name} ({repo_id_str})")
    except Exception as e:
        logger.debug(f"Previous chunk deletion notice (may be new repo): {e}")

    # 2. Chunk source files
    chunks = chunk_repository_files(
        files_map=files_map,
        repo_id=repo_id_str,
        repo_name=repo_name,
        commit_sha=commit_sha or "latest",
        user_id=user_id_str
    )

    if not chunks:
        return {
            "repository_id": repo_id_str,
            "chunks_indexed": 0,
            "files_indexed": len(files_map),
            "status": "zero_chunks",
            "message": "No valid chunkable code found"
        }

    # 3. Add chunks in batches
    total_added = 0
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        ids = [c["id"] for c in batch]
        documents = [c["document"] for c in batch]
        metadatas = [c["metadata"] for c in batch]

        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        total_added += len(batch)

    logger.info(f"Indexed {total_added} code chunks for repo {repo_name} across {len(files_map)} files at commit {commit_sha[:7]}")

    return {
        "repository_id": repo_id_str,
        "repository_name": repo_name,
        "commit_sha": commit_sha,
        "chunks_indexed": total_added,
        "files_indexed": len(files_map),
        "status": "completed"
    }


def retrieve_evidence_for_skill(
    user_id: UUID,
    repository_ids: List[UUID],
    skill_name: str,
    category: str = "",
    query_context: str = "",
    top_k: int = 4
) -> List[Dict[str, Any]]:
    """
    Executes semantic vector similarity retrieval for a required skill across selected repositories.
    Returns sorted list of matching code chunks with metadata and relevance scores.
    """
    collection = get_code_collection()
    if not repository_ids:
        return []

    user_id_str = str(user_id)
    repo_id_strs = [str(r) for r in repository_ids]

    # Enriched domain-aware query construction
    query_parts = [
        f"{skill_name} implementation, usage, architecture, and syntax.",
        f"Functions, classes, modules, and API calls using {skill_name} in {category or 'software development'}.",
    ]
    if query_context and query_context.strip():
        query_parts.append(query_context.strip())

    enriched_query = " ".join(query_parts)

    # Build metadata filter
    if len(repo_id_strs) == 1:
        where_filter = {
            "$and": [
                {"user_id": user_id_str},
                {"repository_id": repo_id_strs[0]}
            ]
        }
    else:
        where_filter = {
            "$and": [
                {"user_id": user_id_str},
                {"repository_id": {"$in": repo_id_strs}}
            ]
        }

    try:
        results = collection.query(
            query_texts=[enriched_query],
            n_results=min(top_k, 10),
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )
    except Exception as e:
        logger.warning(f"Vector search query error for skill '{skill_name}': {e}")
        # Try fallback query without where filter if single user / multi-filter issue
        try:
            results = collection.query(
                query_texts=[enriched_query],
                n_results=min(top_k, 10),
                where={"repository_id": {"$in": repo_id_strs}} if len(repo_id_strs) > 1 else {"repository_id": repo_id_strs[0]},
                include=["documents", "metadatas", "distances"]
            )
        except Exception as fallback_err:
            logger.error(f"Fallback vector search failed for '{skill_name}': {fallback_err}")
            return []

    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]
    ids = results.get("ids", [[]])[0]

    matching_chunks: List[Dict[str, Any]] = []
    settings = get_settings()
    threshold = settings.rag_distance_threshold

    for doc, meta, dist, chunk_id in zip(docs, metas, distances, ids):
        # In cosine distance: 0 is identical, 2 is opposite.
        # Relevance: 1.0 - distance
        relevance = round(max(0.0, 1.0 - dist), 3)

        # Extract genuine lines from document text
        doc_lines = doc.splitlines()
        code_body = "\n".join(doc_lines[1:]) if len(doc_lines) > 1 and doc_lines[0].startswith("// File:") else doc

        matching_chunks.append({
            "chunk_id": chunk_id,
            "document": doc,
            "code_excerpt": code_body[:1200],  # Bounded excerpt
            "file_path": meta.get("file_path", "unknown"),
            "line_start": meta.get("start_line", 1),
            "line_end": meta.get("end_line", 1),
            "repository_id": meta.get("repository_id"),
            "repository_name": meta.get("repository_name", "Repository"),
            "commit_sha": meta.get("commit_sha", "main"),
            "language": meta.get("language", "text"),
            "chunk_type": meta.get("chunk_type", "source_code"),
            "distance": round(dist, 4),
            "relevance_score": relevance,
            "is_confident_match": dist <= threshold,
        })

    # Sort by relevance descending
    matching_chunks.sort(key=lambda x: x["relevance_score"], reverse=True)
    return matching_chunks


def get_repository_index_stats(repo_id: UUID) -> Dict[str, Any]:
    """Returns indexing statistics for a repository."""
    collection = get_code_collection()
    repo_id_str = str(repo_id)
    try:
        result = collection.get(
            where={"repository_id": repo_id_str},
            include=["metadatas"]
        )
        metas = result.get("metadatas", [])
        unique_files = {m.get("file_path") for m in metas if m.get("file_path")}
        commit_sha = metas[0].get("commit_sha") if metas else None

        return {
            "repository_id": repo_id_str,
            "is_indexed": len(metas) > 0,
            "total_chunks": len(metas),
            "unique_files_count": len(unique_files),
            "indexed_commit_sha": commit_sha,
        }
    except Exception as e:
        logger.warning(f"Error querying index stats for repo {repo_id}: {e}")
        return {
            "repository_id": repo_id_str,
            "is_indexed": False,
            "total_chunks": 0,
            "unique_files_count": 0,
            "indexed_commit_sha": None,
        }


def delete_repository_index(repo_id: UUID) -> bool:
    """Removes all indexed chunks for a repository from ChromaDB."""
    collection = get_code_collection()
    repo_id_str = str(repo_id)
    try:
        collection.delete(where={"repository_id": repo_id_str})
        return True
    except Exception as e:
        logger.warning(f"Error deleting chunks for repo {repo_id}: {e}")
        return False
