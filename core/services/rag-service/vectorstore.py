"""Pinecone Vector Store."""

import os
from typing import Dict, List, Optional

from google.cloud import secretmanager
from pinecone import Pinecone, ServerlessSpec

class PineconeVectorStore:
    """Manage vectors in Pinecone."""

    def __init__(
        self,
        index_name: str = "supply-chain-docs",
        dimension: int = 768,
        metric: str = "cosine",
        project_id: str = None,
    ):
        """Initialize Pinecone client."""
        self.index_name = index_name
        self.dimension = dimension
        self.metric = metric
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID")

        # Get API key from Secret Manager
        api_key = self._get_api_key()

        # Initialize Pinecone
        self.pc = Pinecone(api_key=api_key)

        # Create or get index
        self._ensure_index_exists()
        self.index = self.pc.Index(self.index_name)

        print(f"✅ Pinecone connected: {self.index_name}")

    def _get_api_key(self) -> str:
        """Get Pinecone API key from environment or Secret Manager."""
        
        # First, try environment variable (for local development)
        api_key = os.getenv('PINECONE_API_KEY')
        if api_key:
            return api_key
        
        # Fall back to GCP Secret Manager (for production deployment)
        # Lazy import - only load if needed
        try:
            from google.cloud import secretmanager
            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{self.project_id}/secrets/pinecone-api-key/versions/latest"
            response = client.access_secret_version(request={"name": name})
            return response.payload.data.decode('UTF-8')
        except ImportError:
            raise ValueError(
                "PINECONE_API_KEY not found in environment and "
                "google-cloud-secret-manager not installed. "
                "For local dev: set PINECONE_API_KEY in .env"
            )
        except Exception as e:
            raise ValueError(f"Could not retrieve Pinecone API key: {e}")

    def _ensure_index_exists(self):
        """Create index if it doesn't exist."""
        existing_indexes = [index.name for index in self.pc.list_indexes()]

        if self.index_name not in existing_indexes:
            print(f"Creating index: {self.index_name}")
            self.pc.create_index(
                name=self.index_name,
                dimension=self.dimension,
                metric=self.metric,
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )
            print(f"✅ Index created: {self.index_name}")
        else:
            print(f"✅ Index exists: {self.index_name}")

    def upsert(
        self,
        vectors: List[List[float]],
        ids: List[str],
        metadata: List[Dict],
    ):
        """Insert or update vectors."""
        records = [
            (id_, vector, meta)
            for id_, vector, meta in zip(ids, vectors, metadata, strict=True)
        ]

        self.index.upsert(vectors=records)
        print(f"✅ Upserted {len(records)} vectors")

    def query(
        self,
        vector: List[float],
        top_k: int = 5,
        filter: Optional[Dict] = None,
    ) -> List[Dict]:
        """Query similar vectors."""
        results = self.index.query(
            vector=vector,
            top_k=top_k,
            filter=filter,
            include_metadata=True,
        )

        return [
            {
                "id": match.id,
                "score": match.score,
                "metadata": match.metadata,
            }
            for match in results.matches
        ]

    def delete_all(self):
        """Delete all vectors from index."""
        self.index.delete(delete_all=True)
        print(f"✅ Deleted all vectors from {self.index_name}")


if __name__ == "__main__":
    # Test the vector store
    store = PineconeVectorStore()

    # Test query (with random vector)
    import random

    test_vector = [random.random() for _ in range(768)]
    results = store.query(test_vector, top_k=3)

    print(f"✅ Query returned {len(results)} results")
