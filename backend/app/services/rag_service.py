"""
RAG (Retrieval-Augmented Generation) Service
Uses ChromaDB + Sentence Transformers for local embedding and retrieval.
"""

import os
import logging
import uuid
from typing import List, Dict, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class RAGService:
    """
    Manages document ingestion, embedding, and retrieval.
    Uses ChromaDB for vector storage and Sentence Transformers for local embeddings.
    """

    COLLECTION_NAME = "fortivex_knowledge"
    CHUNK_SIZE = 500  # characters per chunk
    CHUNK_OVERLAP = 50
    TOP_K = 3  # number of results to retrieve

    def __init__(self, persist_dir: str = "./chroma_db"):
        self.persist_dir = persist_dir
        self.client = None
        self.collection = None
        self.embedding_model = None
        self._initialized = False
        self._setup()

    def _setup(self):
        """Initialize ChromaDB and embedding model."""
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings

            os.makedirs(self.persist_dir, exist_ok=True)
            self.client = chromadb.PersistentClient(path=self.persist_dir)
            self.collection = self.client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(f"ChromaDB initialized at {self.persist_dir}")

            # Load embedding model
            from sentence_transformers import SentenceTransformer
            self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("Sentence transformer model loaded.")
            self._initialized = True

        except ImportError as e:
            logger.error(f"RAG dependencies not installed: {e}")
        except Exception as e:
            logger.error(f"RAG setup error: {e}")

    def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for text chunks."""
        if not self.embedding_model:
            raise RuntimeError("Embedding model not initialized")
        embeddings = self.embedding_model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()

    def add_document(
        self,
        doc_id: str,
        text: str,
        filename: str,
        file_type: str,
    ) -> int:
        """
        Chunk and embed a document, store in ChromaDB.
        Returns number of chunks stored.
        """
        if not self._initialized:
            raise RuntimeError("RAG service not initialized")

        chunks = self._chunk_text(text)
        if not chunks:
            return 0

        embeddings = self.embed(chunks)
        ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "doc_id": doc_id,
                "filename": filename,
                "file_type": file_type,
                "chunk_index": i,
            }
            for i in range(len(chunks))
        ]

        self.collection.add(
            documents=chunks,
            embeddings=embeddings,
            ids=ids,
            metadatas=metadatas,
        )

        logger.info(f"Added {len(chunks)} chunks for document {filename}")
        return len(chunks)

    def query(self, query: str, top_k: int = None) -> Tuple[str, List[str]]:
        """
        Retrieve relevant context for a query.
        Returns (formatted_context, list_of_sources)
        """
        if not self._initialized:
            return "", []

        k = top_k or self.TOP_K

        try:
            query_embedding = self.embed([query])[0]
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=min(k, self.collection.count()),
                include=["documents", "metadatas", "distances"],
            )

            if not results["documents"] or not results["documents"][0]:
                return "", []

            # Filter by relevance threshold
            docs = results["documents"][0]
            metadatas = results["metadatas"][0]
            distances = results["distances"][0]

            context_parts = []
            sources = []

            for doc, meta, dist in zip(docs, metadatas, distances):
                if dist < 0.7:  # Cosine similarity threshold
                    context_parts.append(f"[Source: {meta['filename']}]\n{doc}")
                    src = meta["filename"]
                    if src not in sources:
                        sources.append(src)

            if not context_parts:
                return "", []

            context = "\n\n---\n\n".join(context_parts)
            return context, sources

        except Exception as e:
            logger.error(f"RAG query error: {e}")
            return "", []

    def delete_document(self, doc_id: str) -> bool:
        """Delete all chunks for a document."""
        if not self._initialized:
            return False

        try:
            # Get all IDs for this document
            results = self.collection.get(
                where={"doc_id": doc_id},
                include=["documents"],
            )
            if results["ids"]:
                self.collection.delete(ids=results["ids"])
                logger.info(f"Deleted {len(results['ids'])} chunks for doc {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Delete error: {e}")
            return False

    def get_document_count(self, doc_id: str) -> int:
        """Get number of chunks for a document."""
        if not self._initialized:
            return 0
        try:
            results = self.collection.get(where={"doc_id": doc_id})
            return len(results["ids"])
        except Exception:
            return 0

    def _chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks."""
        text = text.strip()
        if not text:
            return []

        chunks = []
        start = 0

        while start < len(text):
            end = start + self.CHUNK_SIZE
            chunk = text[start:end]

            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk.rfind(". ")
                if last_period > self.CHUNK_SIZE // 2:
                    chunk = chunk[: last_period + 1]
                    end = start + last_period + 1

            if chunk.strip():
                chunks.append(chunk.strip())

            start = end - self.CHUNK_OVERLAP

        return chunks

    @property
    def is_ready(self) -> bool:
        return self._initialized


def extract_text_from_file(file_path: str, file_type: str) -> str:
    """Extract text from PDF or TXT file."""
    if file_type == "txt":
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    elif file_type == "pdf":
        try:
            import pypdf
            text_parts = []
            with open(file_path, "rb") as f:
                reader = pypdf.PdfReader(f)
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
            return "\n\n".join(text_parts)
        except ImportError:
            try:
                import pdfplumber
                text_parts = []
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            text_parts.append(text)
                return "\n\n".join(text_parts)
            except ImportError:
                raise RuntimeError("No PDF library available. Install pypdf: pip install pypdf")

    raise ValueError(f"Unsupported file type: {file_type}")


# Singleton
rag_service = RAGService()
