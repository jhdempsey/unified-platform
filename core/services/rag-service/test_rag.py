"""Test RAG retrieval."""

import os

from embeddings import VertexAIEmbeddings
from vectorstore import PineconeVectorStore

# Set project ID
os.environ["GCP_PROJECT_ID"] = "gen-lang-client-0282248851"

# Initialize
embedder = VertexAIEmbeddings()
vectorstore = PineconeVectorStore()

# Test queries
test_queries = [
    "What are the cold chain requirements for seafood?",
    "Which supplier has the highest reliability score?",
    "What are the recall procedures?",
]

print("\n🧪 Testing RAG Retrieval\n" + "=" * 60 + "\n")

for query in test_queries:
    print(f"❓ Query: {query}\n")

    # Generate query embedding
    query_vector = embedder.embed_query(query)

    # Search vector store
    results = vectorstore.query(query_vector, top_k=3)

    print(f"📊 Found {len(results)} relevant chunks:\n")

    for i, result in enumerate(results, 1):
        print(f"{i}. Score: {result['score']:.4f}")
        print(f"   Source: {result['metadata']['filename']}")
        print(f"   Text preview: {result['metadata']['text'][:150]}...")
        print()

    print("-" * 60 + "\n")
