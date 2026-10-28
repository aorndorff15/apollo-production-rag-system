from langchain_community.vectorstores import Chroma


def create_vector_store(
    chunks,
    embeddings,
    embedding_model,
    collection_name="apollo_rag"):
    """Create a Chroma vector store using precomputed embeddings."""

    texts = [chunk.page_content for chunk in chunks]
    metadatas = [chunk.metadata for chunk in chunks]
    ids = [f"chunk_{i}" for i in range(len(chunks))]

    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=embedding_model)

    batch_size = 5000

    for start in range(0, len(chunks), batch_size):
        end = start + batch_size

        vectorstore._collection.upsert(
            ids=ids[start:end],
            documents=texts[start:end],
            metadatas=metadatas[start:end],
            embeddings=embeddings[start:end],
        )

        print(f"Stored chunks {start + 1}–{min(end, len(chunks))} of {len(chunks)}")

    return vectorstore


    