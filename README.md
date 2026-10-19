# Milestone 1: Production RAG System
Data 790 Fall 2026
Addison Orndorff

## Components
- Documents: NASA Apollo mission documents
- Vector Database: Chroma
- Embedding Model: text-embedding-3-small
- LLM: gpt-4.1-mini through UNC AI Gateway
- RAG Pipeline: Retrieval and answer generation
- Self-RAG: Relevance and answer-support checks
- Security: Input validation and prompt-injection detection
- Cost Tracking: Lab 3 CostTracker for cost projection

## System Architecture
![RAG Architecture](docs/m1_architecture.svg)

## Setup
1. Clone repository
2. Install dependencies in requirements.txt
3. Create a .env file based on .env.example
4. Add the required UNC AI Gateway configuration to the local .env
5. Run the notebook with the RAG pipeline

## Steps of RAG Pipeline
1. Load NASA Apollo documents
2. Chunk documents
   - Documents split into text chunks from create_chunks() function and RecursiveCharacterTextSplitter().
   - Chunk size is 1000 characters and chunk overlap is 100 characters
3. Create chunk embeddings
4. Store embeddings in Chroma
5. User submits a query
6. Validate user input
7. Retrieve relevant chunks
8. Check retrieval relevance with Self-RAG
9. Generate an answer
10. Self-RAG checks answer suppot
11. Return result








