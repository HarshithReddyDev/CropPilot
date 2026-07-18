import asyncio
import os
import argparse
from pathlib import Path

from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_postgres import PGVector

import sys
sys.path.append(str(Path(__file__).parent.parent / "backend"))
from core.config import settings

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from a PDF file using pypdf."""
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

async def ingest_pdf_to_pgvector(pdf_path: str, scheme_name: str, state: str):
    """Chunk and embed PDF text into PGVector using Ollama."""
    print(f"Reading PDF: {pdf_path}")
    text = extract_text_from_pdf(pdf_path)
    
    if not text.strip():
        print("No text extracted from PDF. Exiting.")
        return

    print("Splitting text into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        is_separator_regex=False,
    )
    chunks = text_splitter.split_text(text)
    print(f"Created {len(chunks)} chunks.")

    print("Initializing Ollama Embeddings...")
    embeddings = OllamaEmbeddings(
        model=settings.OLLAMA_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
    )
    
    print("Initializing PGVector...")
    vector_store = PGVector(
        embeddings=embeddings,
        collection_name=settings.SCHEMES_VECTOR_COLLECTION,
        connection=settings.db_url_sync,
        use_jsonb=True,
    )
    
    print("Embedding and storing in Postgres...")
    metadatas = [{"scheme_name": scheme_name, "state_jurisdiction": state, "source_file": os.path.basename(pdf_path)} for _ in chunks]
    
    vector_store.add_texts(chunks, metadatas=metadatas)
    print("Ingestion complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest Government Scheme PDF into CropPilot DB")
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument("--name", required=True, help="Name of the government scheme")
    parser.add_argument("--state", default="All India", help="State jurisdiction (default: All India)")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.pdf_path):
        print(f"File not found: {args.pdf_path}")
        sys.exit(1)
        
    asyncio.run(ingest_pdf_to_pgvector(args.pdf_path, args.name, args.state))
