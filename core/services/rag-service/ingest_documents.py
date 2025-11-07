"""Ingest documents into vector store."""

from pathlib import Path
from typing import List

from embeddings import VertexAIEmbeddings
from vectorstore import PineconeVectorStore


def load_markdown_files(directory: str) -> List[dict]:
    """Load all markdown files from directory."""
    docs = []
    doc_dir = Path(directory)

    # Ensure absolute path
    if not doc_dir.is_absolute():
        doc_dir = Path(__file__).parent / directory

    print(f"Looking for documents in: {doc_dir.absolute()}")

    markdown_files = list(doc_dir.glob("*.md"))
    print(f"Found {len(markdown_files)} markdown files")

    for file_path in markdown_files:
        with open(file_path, "r") as f:
            content = f.read()

        docs.append(
            {
                "id": file_path.stem,
                "content": content,
                "filename": file_path.name,
                "source": str(file_path),
            }
        )
        print(f"  ✅ Loaded: {file_path.name} ({len(content)} chars)")

    return docs


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Split text into overlapping chunks."""
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap

    return chunks


def ingest_documents(docs_directory: str = "documents"):
    """Ingest all documents into vector store."""
    print("🚀 Starting document ingestion...\n")

    # Initialize services
    embedder = VertexAIEmbeddings()
    vectorstore = PineconeVectorStore()

    # Load documents
    docs = load_markdown_files(docs_directory)

    if len(docs) == 0:
        print("❌ No documents found! Check the directory path.")
        return

    print(f"\n✅ Loaded {len(docs)} documents\n")

    # Process each document
    all_ids = []
    all_vectors = []
    all_metadata = []

    for doc in docs:
        print(f"📄 Processing: {doc['filename']}")

        # Chunk the document
        chunks = chunk_text(doc["content"], chunk_size=1000, overlap=200)
        print(f"   Split into {len(chunks)} chunks")

        # Generate embeddings
        vectors = embedder.embed_texts(chunks)
        print(f"   Generated {len(vectors)} embeddings")

        # Create IDs and metadata
        for i, (chunk, vector) in enumerate(zip(chunks, vectors, strict=True)):
            chunk_id = f"{doc['id']}_chunk_{i}"
            metadata = {
                "document_id": doc["id"],
                "filename": doc["filename"],
                "chunk_index": i,
                "text": chunk[:1000],  # Store first 1000 chars in metadata
                "source": doc["source"],
            }

            all_ids.append(chunk_id)
            all_vectors.append(vector)
            all_metadata.append(metadata)

    # Upsert to Pinecone
    print(f"\n📤 Upserting {len(all_vectors)} vectors to Pinecone...")
    vectorstore.upsert(
        vectors=all_vectors,
        ids=all_ids,
        metadata=all_metadata,
    )

    print("\n✅ Document ingestion complete!")
    print(f"   Total chunks: {len(all_vectors)}")
    print(f"   Total documents: {len(docs)}")


if __name__ == "__main__":
    ingest_documents()
