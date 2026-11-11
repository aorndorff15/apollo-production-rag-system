
"""
rag.py — adapter between the Apollo Milestone 2 pipeline
and the FastAPI app.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma


# Locate the main project folder and its src/ directory.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
CHROMA_DIR = PROJECT_ROOT / "chroma_db"
SERVICE_DIR = Path(__file__).resolve().parent

# Allow imports from src/.
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from embeddings import create_embeddings
from generation import create_self_rag_chain
from rag_pipeline import answer_question


class RAGPipeline:
    """Connects the saved Apollo Chroma database to FastAPI."""

    def __init__(self, pipeline_data):
        self.pipeline_data = pipeline_data
        self.rag_chain = pipeline_data["rag_chain"]
        self.chunk_count = pipeline_data["chunk_count"]
        self.top_k = int(os.getenv("RAG_TOP_K", "3"))

    @classmethod
    def load(cls):
        """Load the saved Apollo database without rebuilding embeddings."""

        # Load environment variables without overwriting
        # variables already supplied by Azure.
        load_dotenv(SERVICE_DIR / ".env", override=False)
        load_dotenv(PROJECT_ROOT / ".env", override=False)

        print("Loading saved Apollo Chroma database...")

        if not CHROMA_DIR.exists():
            raise RuntimeError(
                f"Saved Chroma database not found at {CHROMA_DIR}"
            )

        # Create the embedding model for incoming questions.
        embedding_model = create_embeddings()

        # Open the existing database.
        vectorstore = Chroma(
            collection_name="apollo_milestone2",
            embedding_function=embedding_model,
            persist_directory=str(CHROMA_DIR)
        )

        chunk_count = vectorstore._collection.count()

        if chunk_count == 0:
            raise RuntimeError(
                "The saved Apollo Chroma collection is empty."
            )

        print(f"Loaded saved Chroma database with {chunk_count} chunks.")

        # Recreate the secured Self-RAG chain using the saved database.
        api_key = os.getenv("UNC_AI_API_KEY")
        base_url = os.getenv(
            "UNC_AI_BASE_URL",
            "https://azureaiapi.cloud.unc.edu/openai/v1"
        )
        model = os.getenv("UNC_CHAT_MODEL", "gpt-4.1-mini")
        top_k = int(os.getenv("RAG_TOP_K", "3"))

        rag_chain = create_self_rag_chain(
            vectorstore,
            model,
            base_url,
            api_key,
            top_k=top_k
        )

        pipeline_data = {
            "vectorstore": vectorstore,
            "rag_chain": rag_chain,
            "chunk_count": chunk_count
        }

        print("Saved Apollo RAG pipeline is ready.")

        return cls(pipeline_data)

    def size(self):
        """Return the number of chunks in the index."""
        return self.chunk_count

    def answer(self, question, k=5):
        """Answer a question using the secured Milestone 2 pipeline."""

        # Preserve input validation, PII protection,
        # injection defenses, and output filtering.
        result = answer_question(
            question,
            self.rag_chain,
            use_llm_classifier=True,
        )

        answer_text = result.get(
            "result",
            "The pipeline did not return an answer.",
        )

        # Convert retrieved documents into JSON-friendly source records.
        source_documents = result.get("source_documents", [])

        sources = []
        for document in source_documents:
            metadata = getattr(document, "metadata", {}) or {}

            sources.append({
                "source": str(metadata.get("source", "Unknown")),
                "page": metadata.get("page"),
                "snippet": document.page_content[:300],
            })

        return {
            "answer": answer_text,
            "sources": sources,
            "usage": {
                "input_tokens": result.get("usage", {}).get("input_tokens"),
                "output_tokens": result.get("usage", {}).get("output_tokens"),
                "total_tokens": result.get("usage", {}).get("total_tokens"),
                "cost_usd": None,
            },
            "blocked": result.get("blocked", False),
            "defense_layer": result.get("defense_layer"),
        }
