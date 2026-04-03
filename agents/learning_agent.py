"""
Learning Agent — continuously ingests business data and performance signals
to improve all other agents over time.
"""
import os
from strands import Agent
from core.model_factory import get_model
from tools.data_tools import ingest_text, ingest_pdf, ingest_url, recall_business_context
from core import memory
from config.settings import CLIENT_NAME, BUSINESS_DATA_DIR

SYSTEM_PROMPT = f"""
You are the knowledge manager for {CLIENT_NAME}.

Your job:
1. Scan the business data directory for new files (PDFs, text files) and ingest them.
2. Analyse post performance stored in 'posts' memory — identify what content gets
   the most engagement and summarise the patterns.
3. Update 'business' memory with any new insights or strategy changes.
4. Summarise weekly learnings as a single document stored as 'weekly_summary_<date>'.
5. Flag any gaps in business knowledge that need human input.

You are the brain that makes the whole system smarter over time.
"""

def build_learning_agent():
    return Agent(
        model=get_model(),
        tools=[
            ingest_text,
            ingest_pdf,
            ingest_url,
            recall_business_context,
        ],
        system_prompt=SYSTEM_PROMPT,
    )


def run_learning_cycle():
    """Scan business data dir and ingest any new files automatically."""
    agent = build_learning_agent()
    if not os.path.exists(BUSINESS_DATA_DIR):
        os.makedirs(BUSINESS_DATA_DIR, exist_ok=True)
        return

    files = [f for f in os.listdir(BUSINESS_DATA_DIR)
             if f.endswith((".pdf", ".txt", ".md"))]

    if not files:
        return

    file_list = "\n".join(files)
    agent(
        f"New files found in the business data directory:\n{file_list}\n\n"
        f"Ingest each one using the appropriate tool, then summarise what you learned."
    )
