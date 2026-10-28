import os
from dotenv import load_dotenv
from document_loading import load_documents
from chunking import create_chunks
from embeddings import create_embeddings, embed_chunks
from vector_store import create_vector_store
from generation import create_self_rag_chain
from security import validate_input

def build_pipeline(
    documents,
    model="gpt-4.1-mini",
    chunk_size=1000,
    chunk_overlap=100,
    top_k=3,
    collection_name="apollo_milestone2",):
    """Build the expanded-corpus Self-RAG pipeline."""

    load_dotenv()

    api_key = os.getenv("UNC_AI_API_KEY")
    base_url = os.getenv(
        "UNC_AI_BASE_URL",
        "https://azureaiapi.cloud.unc.edu/openai/v1",
    )

    if not api_key:
        raise ValueError(
            "UNC_AI_API_KEY was not found. Check your .env file."
        )

    chunks = create_chunks(
        documents,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,)

    embedding_model = create_embeddings()
    chunk_embeddings = embed_chunks(chunks, embedding_model)

    vectorstore = create_vector_store(
        chunks,
        chunk_embeddings,
        embedding_model,
        collection_name=collection_name,)

    rag_chain = create_self_rag_chain(
        vectorstore,
        model,
        base_url,
        api_key,
        top_k=top_k,)

    return {
        "chunks": chunks,
        "embedding_model": embedding_model,
        "vectorstore": vectorstore,
        "rag_chain": rag_chain,}




def answer_question(question, rag_chain, max_chars=4000, use_llm_classifier=True):
    """Validate the question, run RAG, and filter the generated answer."""
    from security import validate_input, classify_input_with_llm, filter_output

    if not isinstance(question, str) or not question.strip():
        return {
            "result": "Please enter a question.",
            "blocked": True,
            "defense_layer": "input_validation"}

    if len(question) > max_chars:
        return {
            "result": "Question exceeds the maximum allowed length.",
            "blocked": True,
            "defense_layer": "input_validation"}

    is_valid, message = validate_input(question)
    if not is_valid:
        return {
            "result": "I can't process that request.",
            "blocked": True,
            "defense_layer": "pattern_matching"}

    if use_llm_classifier:
        is_safe, confidence, reason = classify_input_with_llm(question)
        if not is_safe and confidence >= 0.7:
            return {
                "result": "I can't help with that request.",
                "blocked": True,
                "defense_layer": "llm_classifier",
                "classifier_confidence": confidence,
                "classifier_reason": reason}

    result = rag_chain(question)

    # Inspect the output before returning it.
    answer = result.get("result", "")
    passed, filter_reason = filter_output(answer)

    if not passed:
        result["result"] = ("The answer was withheld because it triggered a security check.")
        result["blocked"] = True
        result["defense_layer"] = "output_filter"
        result["filter_reason"] = filter_reason
        return result

    result["blocked"] = False
    result["defense_layer"] = "none"
    return result



    