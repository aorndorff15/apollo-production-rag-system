FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

# Install both the main project and API dependencies.
COPY requirements.txt /app/requirements.txt
COPY rag_service/requirements.txt /app/rag_service-requirements.txt

RUN pip install -r /app/requirements.txt -r /app/rag_service-requirements.txt

# Copy the API, RAG source code, and saved Apollo database.
COPY rag_service/ /app/rag_service/
COPY src/ /app/src/
COPY chroma_db/ /app/chroma_db/

WORKDIR /app/rag_service

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]