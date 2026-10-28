from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from security import sanitize_retrieved_text


def create_rag_chain(
    vectorstore,
    model,
    base_url,
    api_key,
    top_k=3):
    """Create a RAG chain with a Chroma vector store"""

    llm = ChatOpenAI(
        model=model,
        base_url=base_url,
        api_key=api_key,
        temperature=0,)

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(search_kwargs={"k": top_k}),
        return_source_documents=True)

    return qa_chain

from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA


def create_rag_chain(
    vectorstore,
    model,
    base_url,
    api_key,
    top_k=3):
    """Create a RAG chain with a Chroma vector store"""

    llm = ChatOpenAI(
        model=model,
        base_url=base_url,
        api_key=api_key,
        temperature=0,)

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(search_kwargs={"k": top_k}),
        return_source_documents=True)

    return qa_chain


def create_self_rag_chain(
    vectorstore,
    model,
    base_url,
    api_key,
    top_k=3):
    """Create a simple Self-RAG pipeline."""

    llm = ChatOpenAI(
        model=model,
        base_url=base_url,
        api_key=api_key,
        temperature=0,)

    retriever = vectorstore.as_retriever(
        search_kwargs={"k": top_k})

    
    def self_rag(question):
        # Retrieve documents
        documents = retriever.invoke(question)

        # Sanitize each retrieved chunk before it reaches LLM
        sanitized_documents = []
        for doc in documents:
            cleaned_text, was_modified = sanitize_retrieved_text(
                doc.page_content)

            # Keep original document metadata and replace its text
            cleaned_doc = doc.model_copy(
                update={"page_content": cleaned_text})
            sanitized_documents.append(cleaned_doc)

        documents = sanitized_documents

        # Build context from sanitized chunks only
        context = "\n\n".join(
            doc.page_content for doc in documents)

        # Check whether retrieved documents are relevant
        relevance_prompt = f"""
You are evaluating retrieved documents for a RAG system.

Question:
{question}

Retrieved documents:
{context}

Are these documents relevant to answering the question?

Respond with only:
YES
or
NO
"""

        relevance_response = llm.invoke(relevance_prompt)
        relevance = relevance_response.content.strip().upper()

        # Generate an answer if the documents are relevant
        if relevance == "YES":

            answer_prompt = f"""
Answer the question using ONLY the retrieved documents below.

Question:
{question}

Retrieved documents:
{context}

If the documents do not contain enough information to answer,
say that the information is not available in the retrieved documents.
"""

            answer_response = llm.invoke(answer_prompt)
            answer = answer_response.content

            # Check whether the answer is supported by the documents
            support_prompt = f"""
You are evaluating a RAG answer.

Question:
{question}

Retrieved documents:
{context}

Answer:
{answer}

Is the answer fully supported by the retrieved documents?

Respond with only:
YES
or
NO
"""

            support_response = llm.invoke(support_prompt)
            supported = support_response.content.strip().upper()

        else:
            answer = "The retrieved documents were not sufficiently relevant to answer this question."
            supported = "N/A"

        return {
            "result": answer,
            "source_documents": documents,
            "retrieval_relevant": relevance,
            "answer_supported": supported,}

    return self_rag