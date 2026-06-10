"""
memory/memory_manager.py — Short-term + long-term memory system.

Short-term memory: Recent conversation messages stored in PostgreSQL (last N turns).
Long-term memory: User preferences, past analyses, and insights stored as
                  embeddings in ChromaDB, retrieved by semantic similarity.

This dual-memory approach mirrors how human financial advisors work:
they remember the last few things you said (short-term) and your
investment history and goals (long-term).
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Optional

from config import settings
from core.logging import logger


class MemoryManager:
    """
    Manages both short-term (PostgreSQL) and long-term (ChromaDB) memory
    for a specific user.
    """

    def __init__(self, user_id: str):
        self.user_id = user_id
        self._chroma_client = None
        self._collection = None

    # ─── ChromaDB Setup ───────────────────────────────────────────────────────

    def _get_chroma_collection(self):
        """Lazy-load ChromaDB collection for user memory."""
        if self._collection is not None:
            return self._collection
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings

            client = chromadb.HttpClient(
                host=settings.CHROMA_HOST,
                port=settings.CHROMA_PORT,
            )
            self._collection = client.get_or_create_collection(
                name=settings.CHROMA_COLLECTION_USER_MEMORY,
                metadata={"hnsw:space": "cosine"},
            )
            return self._collection
        except Exception as e:
            logger.warning("ChromaDB unavailable for memory", error=str(e))
            return None

    def _get_embedder(self):
        """Get sentence transformer for local embeddings."""
        try:
            from sentence_transformers import SentenceTransformer
            return SentenceTransformer("all-MiniLM-L6-v2")
        except Exception:
            return None

    # ─── Short-Term Memory (DB-backed) ────────────────────────────────────────

    async def get_recent_messages(
        self, session_id: str, limit: int = 10, db=None
    ) -> list[dict]:
        """Load the last N messages from DB for a session."""
        if db is None:
            return []
        try:
            from database.repositories.chat_repository import ChatRepository
            repo = ChatRepository(db)
            messages = await repo.get_session_history(self.user_id, session_id, limit)
            return [
                {"role": m.role, "content": m.content, "timestamp": m.created_at.isoformat()}
                for m in messages
            ]
        except Exception as e:
            logger.error("Failed to load short-term memory", error=str(e))
            return []

    async def save_message(
        self, session_id: str, role: str, content: str,
        metadata: Optional[dict] = None, db=None
    ) -> None:
        """Persist a message to short-term memory (DB)."""
        if db is None:
            return
        try:
            from database.models.models import ChatHistory
            msg = ChatHistory(
                user_id=self.user_id,
                session_id=session_id,
                role=role,
                content=content,
                message_metadata=metadata or {},
            )
            db.add(msg)
            await db.flush()

            # Also store important assistant responses in long-term memory
            if role == "assistant" and len(content) > 100:
                asyncio.create_task(
                    self.store_long_term(
                        content=content,
                        memory_type="conversation",
                        metadata={"session_id": session_id, "timestamp": datetime.utcnow().isoformat()},
                    )
                )
        except Exception as e:
            logger.error("Failed to save message", error=str(e))

    # ─── Long-Term Memory (ChromaDB-backed) ───────────────────────────────────

    async def store_long_term(
        self, content: str, memory_type: str, metadata: Optional[dict] = None
    ) -> None:
        """
        Embed and store a piece of information in ChromaDB long-term memory.
        Memory types: 'preference', 'analysis', 'conversation', 'insight'
        """
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, self._store_long_term_sync, content, memory_type, metadata or {}
        )

    def _store_long_term_sync(
        self, content: str, memory_type: str, metadata: dict
    ) -> None:
        collection = self._get_chroma_collection()
        if collection is None:
            return

        embedder = self._get_embedder()
        if embedder is None:
            return

        try:
            embedding = embedder.encode(content).tolist()
            doc_id = f"{self.user_id}_{memory_type}_{uuid.uuid4().hex[:8]}"
            metadata["user_id"] = self.user_id
            metadata["memory_type"] = memory_type
            metadata["stored_at"] = datetime.utcnow().isoformat()

            collection.add(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[content],
                metadatas=[metadata],
            )
        except Exception as e:
            logger.warning("Long-term memory store failed", error=str(e))

    async def retrieve_relevant_memory(
        self, query: str, n_results: int = 5, memory_type: Optional[str] = None
    ) -> list[dict]:
        """
        Retrieve semantically relevant memories for a given query.
        Used to inject user context into LLM prompts.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._retrieve_sync, query, n_results, memory_type
        )

    def _retrieve_sync(
        self, query: str, n_results: int, memory_type: Optional[str]
    ) -> list[dict]:
        collection = self._get_chroma_collection()
        if collection is None:
            return []

        embedder = self._get_embedder()
        if embedder is None:
            return []

        try:
            query_embedding = embedder.encode(query).tolist()
            where = {"user_id": self.user_id}
            if memory_type:
                where["memory_type"] = memory_type

            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=min(n_results, 10),
                where=where,
                include=["documents", "metadatas", "distances"],
            )

            memories = []
            if results and results["documents"]:
                for doc, meta, dist in zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0],
                ):
                    memories.append({
                        "content": doc,
                        "metadata": meta,
                        "relevance": round(1.0 - dist, 4),
                    })
            return memories
        except Exception as e:
            logger.warning("Long-term memory retrieval failed", error=str(e))
            return []

    async def store_user_preference(self, preference_key: str, value: str) -> None:
        """Persist a user preference to long-term memory."""
        content = f"User preference: {preference_key} = {value}"
        await self.store_long_term(
            content=content,
            memory_type="preference",
            metadata={"key": preference_key, "value": value},
        )

    async def get_user_context_summary(self, query: str) -> str:
        """
        Build a context string from relevant memories to inject into LLM.
        Returns a formatted string summarizing what we know about this user
        that's relevant to the current query.
        """
        memories = await self.retrieve_relevant_memory(query, n_results=5)
        if not memories:
            return ""

        context_parts = ["[User Context from Memory]"]
        for m in memories:
            if m["relevance"] > 0.5:  # Only include highly relevant memories
                context_parts.append(f"- {m['content']}")

        return "\n".join(context_parts) if len(context_parts) > 1 else ""
