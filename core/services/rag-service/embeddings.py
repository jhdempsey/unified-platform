"""Vertex AI Embeddings Service."""

import os
from typing import List

import vertexai
from vertexai.language_models import TextEmbeddingModel


class VertexAIEmbeddings:
    """Generate embeddings using Vertex AI."""

    def __init__(self, project_id: str = None, location: str = "us-central1"):
        """Initialize Vertex AI client."""
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID")
        self.location = location
        # Use the latest stable model
        self.model_name = "text-embedding-004"

        # Initialize Vertex AI
        vertexai.init(project=self.project_id, location=self.location)

        print(f"✅ Vertex AI initialized: {self.project_id} / {self.location}")

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        return self.embed_texts([text])[0]

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        model = TextEmbeddingModel.from_pretrained(self.model_name)

        # Vertex AI has a limit of ~20K characters per request
        # Truncate if needed
        truncated_texts = [text[:20000] for text in texts]

        embeddings = model.get_embeddings(truncated_texts)

        return [embedding.values for embedding in embeddings]

    def embed_query(self, query: str) -> List[float]:
        """Generate embedding for a query (same as embed_text)."""
        return self.embed_text(query)


if __name__ == "__main__":
    # Test the embeddings
    embedder = VertexAIEmbeddings()

    test_text = "What are the cold chain requirements for seafood?"
    embedding = embedder.embed_text(test_text)

    print(f"✅ Generated embedding with {len(embedding)} dimensions")
    print(f"First 5 values: {embedding[:5]}")
