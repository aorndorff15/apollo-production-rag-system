from pathlib import Path
from langchain_community.document_loaders import (
    PyPDFLoader,
    BSHTMLLoader,
    TextLoader)

def load_documents(folder_path):
    """Load PDF and HTML documents from a folder and its subfolders."""

    documents = []
    folder = Path(folder_path)

    # Load PDF documents
    for pdf_path in sorted(folder.rglob("*.pdf")):
        # Skip hidden folders and files
        if any(part.startswith(".") for part in pdf_path.parts):
            continue

        loader = PyPDFLoader(str(pdf_path))
        documents.extend(loader.load())

    # Load HTML documents
    for html_path in sorted(folder.rglob("*.html")):
        # Skip hidden folders and files
        if any(part.startswith(".") for part in html_path.parts):
            continue

        loader = BSHTMLLoader(str(html_path), open_encoding="utf-8")
        documents.extend(loader.load())

    # Load plain text documents
    for txt_path in sorted(folder.rglob("*.txt")):
        if any(part.startswith(".") for part in txt_path.parts):
            continue

        loader = TextLoader(str(txt_path), encoding="utf-8")
        documents.extend(loader.load())

    # Count unique source files
    unique_sources = set(
        doc.metadata.get("source", "") for doc in documents
    )

    print(f"Loaded {len(documents)} total pages/documents")
    print(f"Found {len(unique_sources)} source files")

    if documents:
        print(documents[0].page_content[:500] + "...")

    return documents
