"""
Business data ingestion tools — feed PDFs, docs, URLs into memory.
"""
import os
from strands import tool
from core import memory
from config.settings import BUSINESS_DATA_DIR


@tool
def ingest_text(content: str, doc_id: str, category: str = "business") -> str:
    """Store a piece of business knowledge into long-term memory.

    Args:
        content: The text content to remember.
        doc_id: Unique identifier for this document (e.g. 'about_us', 'product_v2').
        category: Memory collection to store in (business | posts | leads | engagement).
    """
    memory.remember(category, doc_id, content)
    return f"Stored '{doc_id}' in '{category}' memory."


@tool
def ingest_pdf(file_path: str) -> str:
    """Extract and store text from a PDF file into business memory.

    Args:
        file_path: Path to the PDF file.
    """
    try:
        import PyPDF2
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            text = "\n".join(p.extract_text() or "" for p in reader.pages)
        doc_id = os.path.basename(file_path)
        memory.remember("business", doc_id, text)
        return f"PDF '{doc_id}' ingested into business memory ({len(text)} chars)."
    except Exception as e:
        return f"PDF ingest failed: {e}"


@tool
def ingest_url(url: str) -> str:
    """Scrape a webpage and store its content into business memory.

    Args:
        url: The URL to scrape.
    """
    try:
        import requests
        from bs4 import BeautifulSoup
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        text = soup.get_text(separator="\n", strip=True)[:8000]
        memory.remember("business", url, text)
        return f"URL '{url}' ingested into business memory."
    except Exception as e:
        return f"URL ingest failed: {e}"


@tool
def recall_business_context(query: str) -> str:
    """Retrieve relevant business knowledge to inform content or outreach.

    Args:
        query: What you want to know (e.g. 'our product features', 'target audience').
    """
    docs = memory.recall("business", query, n=3)
    return "\n---\n".join(docs) if docs else "No relevant business context found."
