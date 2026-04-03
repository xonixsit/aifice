"""
Engagement Agent — monitors and responds to comments, DMs, and mentions
across all platforms to maintain an active, human-like presence.
"""
from strands import Agent
from core.model_factory import get_model
from tools.social_tools import linkedin_comment, instagram_comment, whatsapp_send
from tools.data_tools import recall_business_context, ingest_text
from config.settings import CLIENT_NAME, CLIENT_TONE

SYSTEM_PROMPT = f"""
You are the community manager for {CLIENT_NAME}.
Tone: {CLIENT_TONE}.

Your job:
1. Respond to comments and messages in a warm, on-brand way.
2. Always recall_business_context before replying to ensure accuracy.
3. If someone expresses buying intent or asks for pricing, flag them as a hot lead
   by calling ingest_text with category='leads'.
4. Keep replies concise — 1-3 sentences max for comments, slightly longer for DMs.
5. Never argue, never spam, never repeat the same reply twice.
6. Log every interaction via ingest_text to 'engagement' memory.
"""

def build_engagement_agent():
    return Agent(
        model=get_model(),
        tools=[
            linkedin_comment,
            instagram_comment,
            whatsapp_send,
            recall_business_context,
            ingest_text,
        ],
        system_prompt=SYSTEM_PROMPT,
    )
