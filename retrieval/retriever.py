from typing import Dict, List, Optional

from retrieval.vector_store import search


def retrieve(query: str, metadata_filter: Optional[Dict[str, str]] = None, top_k: int = 3) -> List[dict]:
    return search(query, top_k=top_k, metadata_filter=metadata_filter)
