
import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

# Locate the project folders
PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
DATA_DIR = PROJECT_ROOT / "data"
CHROMA_DIR = PROJECT_ROOT / "chroma_db"

# Make the existing source files importable
sys.path.insert(0, str(SRC_DIR))

from document_loading import load_documents
from chunking import create_chunks
from embeddings import create_embeddings, embed_chunks
from vector_store import create_vector_store


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--build",
        action="store_true",
        help="Generate embeddings and save the Chroma database."
    )
    args = parser.parse_args()

    # Load credentials using the same order as the API service
    load_dotenv(PROJECT_ROOT / "rag_service" / ".env", override=False)
    load_dotenv(PROJECT_ROOT / ".env", override=False)

    # Prevent accidentally overwriting an existing database
    if any(CHROMA_DIR.iterdir()):
        raise RuntimeError(
            f"{CHROMA_DIR} is not empty. "
            "Stopping to protect the existing database."
        )

    print("Loading Apollo documents...")
    documents = load_documents(str(DATA_DIR))

    if not documents:
        raise RuntimeError("No Apollo documents were found.")

    print("Creating Apollo chunks...")
    chunks = create_chunks(
        documents,
        chunk_size=1000,
        chunk_overlap=100
    )

    print(f"Prepared {len(chunks)} chunks.")

    # Default behavior: inspect the workload without embedding
    if not args.build:
        print("\nDRY RUN COMPLETE.")
        print("No embeddings were generated and no API calls were made.")
        print("Use --build only when you are ready to generate embeddings.")
        return

    print("\nGenerating document embeddings...")
    embedding_model = create_embeddings()
    chunk_embeddings = embed_chunks(chunks, embedding_model)

    print("\nSaving the Apollo Chroma database...")
    create_vector_store(
        chunks,
        chunk_embeddings,
        embedding_model,
        collection_name="apollo_milestone2",
        persist_directory=str(CHROMA_DIR)
    )

    print("\nApollo Chroma database saved successfully.")


if __name__ == "__main__":
    main()
