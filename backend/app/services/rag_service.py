"""RAG service for handling PDFs and vector search."""
import os
from pathlib import Path

import chromadb
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from pypdf import PdfReader

from app.core.config import settings


class RAGService:
    """Service for PDF ingestion and vector search using ChromaDB."""

    def __init__(self):
        """Initialize ChromaDB client and embeddings."""
        self.chroma_client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR
        )
        self.embeddings = OpenAIEmbeddings(
            model=settings.LITELLM_EMBEDDING_MODEL,
            base_url=settings.LITELLM_PROXY_URL,
            api_key=settings.LITELLM_API_KEY,
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1024,
            chunk_overlap=256,
            separators=["\n\n", "\n", " ", ""],
        )

    def _get_collection_name(self, user_id: str) -> str:
        """Generate per-user collection name."""
        return f"user_{user_id}".replace("-", "_")

    async def ingest_pdf(
        self,
        pdf_path: str,
        user_id: str,
        user_email: str,
        filename: str,
    ) -> dict:
        """
        Extract text from PDF and ingest into ChromaDB.

        Args:
            pdf_path: Path to PDF file
            user_id: UUID of the user
            user_email: Email for tracking/metadata
            filename: Original PDF filename

        Returns:
            Dictionary with:
            - document_id: ID of the ingested document
            - chunks_count: Number of text chunks created
            - characters_processed: Total characters extracted
        """
        try:
            # Extract text from PDF
            pdf_reader = PdfReader(pdf_path)
            text = ""
            metadata = {"source": filename, "page_count": len(pdf_reader.pages)}

            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                text += f"\n--- Page {page_num + 1} ---\n{page_text}"

            if not text.strip():
                raise ValueError("PDF extraction failed - no text found")

            # Split text into chunks
            chunks = self.text_splitter.split_text(text)
            if not chunks:
                raise ValueError("Text splitting produced no chunks")

            # Create documents with metadata
            documents = [
                Document(
                    page_content=chunk,
                    metadata={
                        **metadata,
                        "chunk_index": i,
                        "user_email": user_email,
                    },
                )
                for i, chunk in enumerate(chunks)
            ]

            # Get or create collection for user
            collection_name = self._get_collection_name(user_id)
            collection = self.chroma_client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"},
            )

            # Generate IDs for documents
            doc_ids = [f"{filename}_chunk_{i}" for i in range(len(chunks))]

            # Add to ChromaDB with embeddings
            texts = [doc.page_content for doc in documents]
            metadatas = [doc.metadata for doc in documents]

            collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=doc_ids,
            )

            return {
                "document_id": filename,
                "chunks_count": len(chunks),
                "characters_processed": len(text),
            }

        except Exception as e:
            raise Exception(f"PDF ingestion failed: {str(e)}")

    async def retrieve_context(
        self,
        user_id: str,
        query: str,
        top_k: int = 5,
    ) -> list[str]:
        """
        Retrieve relevant chunks from ChromaDB for a query.

        Args:
            user_id: UUID of the user
            query: Search query
            top_k: Number of results to return

        Returns:
            List of relevant text chunks
        """
        try:
            collection_name = self._get_collection_name(user_id)
            collection = self.chroma_client.get_collection(name=collection_name)

            # Query the collection
            results = collection.query(
                query_texts=[query],
                n_results=top_k,
            )

            # Extract documents from results
            if results and results.get("documents"):
                return results["documents"][0]  # First query's results

            return []

        except Exception as e:
            # Collection might not exist yet
            if "not found" in str(e).lower():
                return []
            raise Exception(f"Retrieval failed: {str(e)}")

    async def delete_user_documents(self, user_id: str) -> None:
        """Delete all documents for a user."""
        try:
            collection_name = self._get_collection_name(user_id)
            self.chroma_client.delete_collection(name=collection_name)
        except Exception as e:
            if "not found" not in str(e).lower():
                raise Exception(f"Delete failed: {str(e)}")


# Singleton instance
_rag_service = None


def get_rag_service() -> RAGService:
    """Get or create RAGService singleton."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
