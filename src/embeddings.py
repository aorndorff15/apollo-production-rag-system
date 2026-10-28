import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings


def create_embeddings(model="text-embedding-3-small"):
    """Create an embedding model using UNC AI Gateway"""
    load_dotenv()

    api_key = os.getenv("UNC_AI_API_KEY")
    base_url = os.getenv(
        "UNC_AI_BASE_URL",
        "https://azureaiapi.cloud.unc.edu/openai/v1"
    )

    if not api_key:
        raise ValueError("UNC_AI_API_KEY was not found. Check your .env file.")

    return OpenAIEmbeddings(
        model=model,
        api_key=api_key,
        base_url=base_url,)


def embed_chunks(chunks, embedding_model, batch_size=200):
    """Create embeddings for document chunks in smaller batches"""

    texts = [chunk.page_content for chunk in chunks]

    embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch_embeddings = embedding_model.embed_documents(batch, chunk_size=500)       
        embeddings.extend(batch_embeddings)

    return embeddings