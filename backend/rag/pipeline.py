"""
rag/pipeline.py — Retrieval-Augmented Generation over financial documents.

Pipeline:
  PDF Upload → Text Extraction → Chunking → Embedding → ChromaDB storage
  Query     → Embed query → ChromaDB similarity search → Inject context → LLM answer

Supports: SEC 10-K/10-Q filings, annual reports, earnings transcripts.
"""

import asyncio
import uuid
from datetime import datetime
from typing import Optional

from config import settings
from core.logging import logger
from schemas.schemas import DocumentUploadResponse, RAGQueryResponse


class RAGPipeline:
    """End-to-end RAG pipeline for financial document Q&A."""

    CHUNK_SIZE = 1000       # characters per chunk
    CHUNK_OVERLAP = 200     # overlap between consecutive chunks for continuity

    def __init__(self):
        self._chroma_client = None
        self._collection = None
        self._embedder = None
        self._llm = None

    # ─── Infrastructure ───────────────────────────────────────────────────────

    def _get_collection(self):
        if self._collection is not None:
            return self._collection
        try:
            import chromadb
            client = chromadb.HttpClient(host=settings.CHROMA_HOST, port=settings.CHROMA_PORT)
            self._collection = client.get_or_create_collection(
                name=settings.CHROMA_COLLECTION_FINANCIAL_DOCS,
                metadata={"hnsw:space": "cosine"},
            )
            return self._collection
        except Exception as e:
            logger.warning("ChromaDB unavailable for RAG", error=str(e))
            return None

    def _get_embedder(self):
        if self._embedder is not None:
            return self._embedder
        try:
            from sentence_transformers import SentenceTransformer
            self._embedder = SentenceTransformer("all-MiniLM-L6-v2")
            return self._embedder
        except Exception as e:
            logger.warning("Sentence transformer unavailable", error=str(e))
            return None

    def _get_llm(self):
        if self._llm is not None:
            return self._llm

        try:
            from langchain_groq import ChatGroq

            self._llm = ChatGroq(
                model=settings.GROQ_MODEL,
                temperature=0.1,
                api_key=settings.GROQ_API_KEY,
            )

            return self._llm

        except Exception as e:
            logger.warning("LLM unavailable for RAG", error=str(e))
            return None

    # ─── Ingestion ────────────────────────────────────────────────────────────

    async def ingest_document(
        self, content: bytes, filename: str, metadata: dict
    ) -> DocumentUploadResponse:
        """
        Ingest a PDF document into the vector store.
        Steps: extract text → chunk → embed → store.
        """
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, self._ingest_sync, content, filename, metadata
        )
        return result

    def _ingest_sync(
        self, content: bytes, filename: str, metadata: dict
    ) -> DocumentUploadResponse:
        doc_id = str(uuid.uuid4())

        # 1. Extract text from PDF
        text = self._extract_pdf_text(content)
        if not text:
            return DocumentUploadResponse(
                document_id=doc_id,
                filename=filename,
                chunks_created=0,
                status="failed: no text extracted",
            )

        # 2. Chunk the text
        chunks = self._chunk_text(text)
        if not chunks:
            return DocumentUploadResponse(
                document_id=doc_id, filename=filename, chunks_created=0, status="failed: no chunks"
            )

        # 3. Embed and store in ChromaDB
        collection = self._get_collection()
        embedder = self._get_embedder()
        if collection is None or embedder is None:
            logger.warning("Storing document metadata only — ChromaDB/embedder unavailable")
            return DocumentUploadResponse(
                document_id=doc_id, filename=filename,
                chunks_created=len(chunks), status="stored_metadata_only",
            )

        # Embed in batches of 50 for memory efficiency
        batch_size = 50
        stored = 0
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            embeddings = embedder.encode(batch).tolist()
            ids = [f"{doc_id}_chunk_{i + j}" for j in range(len(batch))]
            metas = [
                {
                    **metadata,
                    "doc_id": doc_id,
                    "filename": filename,
                    "chunk_index": i + j,
                    "total_chunks": len(chunks),
                    "ingested_at": datetime.utcnow().isoformat(),
                }
                for j in range(len(batch))
            ]
            try:
                collection.add(ids=ids, embeddings=embeddings, documents=batch, metadatas=metas)
                stored += len(batch)
            except Exception as e:
                logger.error("Chunk storage failed", batch_start=i, error=str(e))

        logger.info("Document ingested", doc_id=doc_id, filename=filename, chunks=stored)
        return DocumentUploadResponse(
            document_id=doc_id,
            filename=filename,
            chunks_created=stored,
            status="success",
        )

    def _extract_pdf_text(self, content: bytes) -> str:
        """Extract plain text from PDF bytes using pypdf."""
        try:
            import io
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(content))
            pages = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
            return "\n\n".join(pages)
        except Exception as e:
            logger.error("PDF text extraction failed", error=str(e))
            return ""

    def _chunk_text(self, text: str) -> list[str]:
        """
        Split text into overlapping chunks.
        Uses sentence-aware splitting: tries to break at paragraph/sentence boundaries
        to preserve semantic coherence.
        """
        # Prefer paragraph splits
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        chunks = []
        current_chunk = ""

        for para in paragraphs:
            if len(current_chunk) + len(para) <= self.CHUNK_SIZE:
                current_chunk += ("\n\n" if current_chunk else "") + para
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                # Handle paragraphs longer than chunk size
                if len(para) > self.CHUNK_SIZE:
                    # Split by sentences
                    sentences = para.replace(". ", ".\n").split("\n")
                    for sent in sentences:
                        if len(current_chunk) + len(sent) <= self.CHUNK_SIZE:
                            current_chunk = (current_chunk + " " + sent).strip()
                        else:
                            if current_chunk:
                                chunks.append(current_chunk)
                            current_chunk = sent
                else:
                    # Start new chunk with overlap from end of previous
                    overlap_start = max(0, len(current_chunk) - self.CHUNK_OVERLAP)
                    overlap = current_chunk[overlap_start:]
                    current_chunk = (overlap + "\n\n" + para).strip()

        if current_chunk:
            chunks.append(current_chunk)

        return [c for c in chunks if len(c) > 50]  # Filter tiny chunks

    # ─── Querying ─────────────────────────────────────────────────────────────

    async def query(
        self,
        query: str,
        top_k: int = 5,
        user_id: Optional[str] = None,
        document_ids: Optional[list[str]] = None,
    ) -> RAGQueryResponse:
        """Retrieve relevant chunks and generate an LLM answer."""
        loop = asyncio.get_event_loop()
        chunks = await loop.run_in_executor(
            None, self._retrieve_chunks, query, top_k, user_id, document_ids
        )

        if not chunks:
            return RAGQueryResponse(
                answer="No relevant documents found for your query. Please upload financial documents first.",
                sources=[],
                confidence=0.0,
                query=query,
            )

        # Build context from retrieved chunks
        context = "\n\n---\n\n".join(
            f"[Source: {c['metadata'].get('filename', 'unknown')}, "
            f"Page chunk {c['metadata'].get('chunk_index', '?')}]\n{c['document']}"
            for c in chunks
        )

        # Generate answer with LLM
        answer, confidence = await self._generate_answer(query, context)

        sources = [
            {
                "filename": c["metadata"].get("filename"),
                "doc_id": c["metadata"].get("doc_id"),
                "chunk_index": c["metadata"].get("chunk_index"),
                "company": c["metadata"].get("company"),
                "document_type": c["metadata"].get("document_type"),
                "relevance_score": round(c.get("relevance", 0), 4),
            }
            for c in chunks
        ]

        return RAGQueryResponse(
            answer=answer,
            sources=sources,
            confidence=confidence,
            query=query,
        )

    def _retrieve_chunks(
        self,
        query: str,
        top_k: int,
        user_id: Optional[str],
        document_ids: Optional[list[str]],
    ) -> list[dict]:
        collection = self._get_collection()
        embedder = self._get_embedder()
        if collection is None or embedder is None:
            return []

        try:
            query_embedding = embedder.encode(query).tolist()

            where = {}
            if user_id:
                where["user_id"] = user_id
            if document_ids:
                where["doc_id"] = {"$in": document_ids}

            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where if where else None,
                include=["documents", "metadatas", "distances"],
            )

            chunks = []
            if results and results["documents"]:
                for doc, meta, dist in zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0],
                ):
                    chunks.append({
                        "document": doc,
                        "metadata": meta,
                        "relevance": 1.0 - dist,
                    })
            return chunks
        except Exception as e:
            logger.error("RAG retrieval failed", error=str(e))
            return []

    async def _generate_answer(self, query: str, context: str) -> tuple[str, float]:
        """Generate an LLM answer grounded in the retrieved context."""
        llm = self._get_llm()
        if llm is None:
            return f"Based on the retrieved documents: {context[:500]}...", 0.5

        try:
            from langchain_core.messages import HumanMessage, SystemMessage
            system_prompt = """You are a financial analyst AI assistant. Answer the user's question 
based ONLY on the provided document context. Be precise, cite specific figures and dates.
If the context doesn't contain enough information, say so clearly.
Format numbers clearly (e.g., $1.2B revenue, 15% YoY growth)."""

            prompt = f"""Context from financial documents:
{context}

Question: {query}

Answer based on the above context:"""

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: llm.invoke([
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=prompt),
                ])
            )
            answer = response.content if hasattr(response, "content") else str(response)
            confidence = 0.8  # Fixed confidence when answer is LLM-generated from context
            return answer, confidence
        except Exception as e:
            logger.error("LLM answer generation failed", error=str(e))
            return f"Error generating answer: {str(e)}", 0.0

    async def list_documents(self, user_id: str) -> list[dict]:
        """List all documents ingested by a user."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._list_docs_sync, user_id)

    def _list_docs_sync(self, user_id: str) -> list[dict]:
        collection = self._get_collection()
        if collection is None:
            return []
        try:
            results = collection.get(where={"user_id": user_id}, include=["metadatas"])
            seen_doc_ids = set()
            docs = []
            for meta in results.get("metadatas", []):
                doc_id = meta.get("doc_id")
                if doc_id and doc_id not in seen_doc_ids:
                    seen_doc_ids.add(doc_id)
                    docs.append({
                        "doc_id": doc_id,
                        "filename": meta.get("filename"),
                        "document_type": meta.get("document_type"),
                        "company": meta.get("company"),
                        "ingested_at": meta.get("ingested_at"),
                        "total_chunks": meta.get("total_chunks"),
                    })
            return docs
        except Exception as e:
            logger.error("Document list failed", error=str(e))
            return []
