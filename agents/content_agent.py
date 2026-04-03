"""
Content Agent — creates platform-specific posts, captions, and scripts
grounded in business memory and brand tone.
"""
from strands import Agent
from core.model_factory import get_model
from tools.social_tools import linkedin_post, instagram_post, facebook_post, telegram_post
from tools.data_tools import recall_business_context
from config.settings import CLIENT_NAME, CLIENT_TONE, CLIENT_INDUSTRY

SYSTEM_PROMPT = f"""
You are the content creator for {CLIENT_NAME}, a {CLIENT_INDUSTRY} brand.
Tone: {CLIENT_TONE}.

Your job:
1. Use recall_business_context to ground every post in real business knowledge.
2. Create platform-native content (LinkedIn = thought leadership, Instagram = visual hooks,
   TikTok = short punchy scripts, Facebook = community-friendly, Telegram = concise updates).
3. Always include a clear CTA.
4. Publish using the appropriate posting tool.
5. After posting, log the content with ingest_text to 'posts' memory for future learning.

Never fabricate facts about the business. Always recall context first.
"""

def build_content_agent():
    return Agent(
        model=get_model(),
        tools=[
            linkedin_post,
            instagram_post,
            facebook_post,
            telegram_post,
            recall_business_context,
        ],
        system_prompt=SYSTEM_PROMPT,
    )
