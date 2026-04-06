"""ChromaDB vector store wrapper."""

from typing import Optional, Any
from pathlib import Path

try:
    import chromadb
    from chromadb.config import Settings

    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    chromadb = None
    Settings = None

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings


class ChromaStore:
    """ChromaDB vector store for embeddings."""

    def __init__(
        self,
        persist_directory: str = "./chroma_data",
        collection_name: str = "research",
        embedding_function: Optional[Embeddings] = None,
    ):
        if not CHROMADB_AVAILABLE:
            raise ImportError("ChromaDB is not installed. Run: pip install chromadb")

        self.persist_directory = Path(persist_directory)
        self.collection_name = collection_name
        self.embedding_function = embedding_function
        self._client: Optional[Any] = None
        self._collection: Optional[Any] = None

    @property
    def client(self) -> Any:
        """Get or create the ChromaDB client."""
        if self._client is None:
            self.persist_directory.mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(
                path=str(self.persist_directory),
                settings=Settings(anonymized_telemetry=False),
            )
        return self._client

    @property
    def collection(self) -> Any:
        """Get or create the collection."""
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Research embeddings store"},
            )
        return self._collection

    def add_text(
        self,
        text: str,
        doc_id: str,
        metadata: Optional[dict] = None,
        embedding: Optional[list[float]] = None,
    ) -> str:
        """Add text to the vector store."""
        if metadata is None:
            metadata = {}
        if embedding is None and self.embedding_function:
            embedding = self.embedding_function.embed_query(text)

        self.collection.add(
            ids=[doc_id],
            documents=[text],
            metadatas=[metadata],
            embeddings=[embedding] if embedding else None,
        )
        return doc_id

    def add_texts(
        self,
        texts: list[str],
        doc_ids: list[str],
        metadatas: Optional[list[dict]] = None,
        embeddings: Optional[list[list[float]]] = None,
    ) -> list[str]:
        """Add multiple texts to the vector store."""
        if metadatas is None:
            metadatas = [{}] * len(texts)
        if embeddings is None and self.embedding_function:
            embeddings = self.embedding_function.embed_documents(texts)

        self.collection.add(
            ids=doc_ids,
            documents=texts,
            metadatas=metadatas,
            embeddings=embeddings,
        )
        return doc_ids

    def search(
        self,
        query: str,
        k: int = 5,
        filter_dict: Optional[dict] = None,
        where: Optional[dict] = None,
        where_document: Optional[dict] = None,
    ) -> list[dict]:
        """Search by similarity."""
        if self.embedding_function:
            query_embedding = self.embedding_function.embed_query(query)
        else:
            raise ValueError("Embedding function required for search")

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=where or filter_dict,
            where_document=where_document,
        )

        docs = []
        for i in range(len(results["ids"][0])):
            docs.append(
                {
                    "id": results["ids"][0][i],
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else None,
                }
            )
        return docs

    def get_by_phase(self, phase: str) -> list[dict]:
        """Get all documents for a phase."""
        return self.search("", k=100, filter_dict={"phase": phase})

    def get_by_question(self, question_id: str) -> list[dict]:
        """Get all documents for a question."""
        return self.search("", k=100, filter_dict={"question_id": question_id})

    def get_by_metadata(self, metadata: dict) -> list[dict]:
        """Get documents by metadata."""
        return self.search("", k=100, filter_dict=metadata)

    def delete(self, doc_id: str) -> None:
        """Delete a document by ID."""
        self.collection.delete(ids=[doc_id])

    def delete_collection(self) -> None:
        """Delete the entire collection."""
        self.client.delete_collection(self.collection_name)
        self._collection = None

    def count(self) -> int:
        """Count documents in the collection."""
        return self.collection.count()

    def peek(self, limit: int = 10) -> list[dict]:
        """Peek at documents in the collection."""
        results = self.collection.get(limit=limit)
        return [
            {
                "id": results["ids"][i],
                "content": results["documents"][i],
                "metadata": results["metadatas"][i] if results["metadatas"] else {},
            }
            for i in range(len(results["ids"]))
        ]
