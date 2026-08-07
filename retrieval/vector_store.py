import json
from pathlib import Path
from typing import Dict, List, Optional

import faiss
import numpy as np

from retrieval.embeddings import embed

_CHUNKS_PATH = Path(__file__).resolve().parent / "knowledge" / "sop_chunks.json"

_chunks: Optional[List[dict]] = None
_vectors: Optional[np.ndarray] = None


def _ensure_loaded() -> None:
    global _chunks, _vectors
    if _chunks is not None:
        return
    with open(_CHUNKS_PATH) as f:
        chunks = json.load(f)
    vectors = np.array([embed(c["text"]) for c in chunks], dtype="float32")
    faiss.normalize_L2(vectors)
    _chunks = chunks
    _vectors = vectors


def _matches_filter(metadata: dict, metadata_filter: Dict[str, str]) -> bool:
    return all(metadata.get(key) == value for key, value in metadata_filter.items())


def search(query: str, top_k: int = 3, metadata_filter: Optional[Dict[str, str]] = None) -> List[dict]:
    _ensure_loaded()

    if metadata_filter:
        candidate_positions = [
            i for i, chunk in enumerate(_chunks) if _matches_filter(chunk["metadata"], metadata_filter)
        ]
    else:
        candidate_positions = list(range(len(_chunks)))

    if not candidate_positions:
        return []

    candidate_vectors = _vectors[candidate_positions]
    index = faiss.IndexFlatIP(candidate_vectors.shape[1])
    index.add(candidate_vectors)

    query_vector = np.array([embed(query)], dtype="float32")
    faiss.normalize_L2(query_vector)

    k = min(top_k, len(candidate_positions))
    scores, local_ids = index.search(query_vector, k)

    results = []
    for score, local_id in zip(scores[0], local_ids[0]):
        chunk = _chunks[candidate_positions[local_id]]
        results.append(
            {
                "id": chunk["id"],
                "text": chunk["text"],
                "metadata": chunk["metadata"],
                "score": float(score),
            }
        )
    return results
