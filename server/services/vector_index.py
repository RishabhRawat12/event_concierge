"""
Vector index and situational search engine for O(1) event retrieval.
Implements multi-token intersection and deterministic registry filtering.
"""
import json
import logging
from typing import Any, Dict, List, Set, Optional
import aiofiles

logger = logging.getLogger(__name__)

class VectorIndexService:
    """Manages high-performance in-memory search indices for event data."""

    def __init__(self) -> None:
        self.mock_events: List[Dict[str, Any]] = []
        self._exact_index: Dict[str, List[Dict[str, Any]]] = {}
        self._token_index: Dict[str, List[int]] = {}

    async def load_events(self, file_path: str = "mock_events.json") -> List[Dict[str, Any]]:
        """Loads and indexes event data for situational awareness."""
        try:
            async with aiofiles.open(file_path, mode="r") as f:
                content = await f.read()
                self.mock_events = json.loads(content)
            
            self._exact_index = {}
            self._token_index = {}
            
            for i, event in enumerate(self.mock_events):
                name_key = event["name"].lower()
                topic_key = event["topic"].lower()
                self._exact_index.setdefault(name_key, []).append(event)
                self._exact_index.setdefault(topic_key, []).append(event)

                # Tokenized Fuzzy Index
                tokens = set(name_key.split()) | set(topic_key.split())
                for token in tokens:
                    if len(token) > 2:
                        self._token_index.setdefault(token, []).append(i)

            logger.info(f"Vector Index synchronized with {len(self.mock_events)} events.")
            return self.mock_events
        except Exception as e:
            logger.error(f"Vector Index failure: {e}")
            self.mock_events = []
            return []

    def search_events(self, query: str) -> List[Dict[str, Any]]:
        """Executes situational filtering via exact and tokenized indices."""
        q = query.lower().strip()
        if not q:
            return []

        # 1. Exact Match O(1)
        if q in self._exact_index:
            return self._exact_index[q][:5]

        # 2. Token Intersection
        tokens = [t for t in q.split() if len(t) > 2] or q.split()
        matches: Set[int] = set()
        
        for i, token in enumerate(tokens):
            token_hits = set(self._token_index.get(token, []))
            if i == 0:
                matches = token_hits
            else:
                matches &= token_hits
            if not matches:
                break

        return [self.mock_events[idx] for idx in list(matches)[:5]]

vector_index = VectorIndexService()
