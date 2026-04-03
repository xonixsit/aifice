"""
Content Agent — creates platform-specific posts, captions, and scripts
grounded in business memory and brand tone.

DRAFT_MODE=true  → saves to drafts queue for human approval
DRAFT_MODE=false → publishes immediately (default)
"""
import os
from strands import Agent, tool
from core.model_factory import get_model
from tools.social_tools import linkedin_post, instagram_post, facebook_post, telegram_post
from tools.data_tools import recall_business_context, ingest_text
from config.settings import CLIENT_NAME, CLIENT_TONE, CLIENT_INDUSTRY

DRAFT_MODE = os.getenv("DRAFT_MODE", "true").lower() == "true"


@tool
def save_draft(platform: str, content: str, topic: str = "") -> str:
    """Save a post as a draft for human review instead of publishing immediately.

    Args:
        platform: Target platform (linkedin | instagram | facebook | telegram).
        content: The post content to save as draft.
        topic: The topic or theme of the post.
    """
    from core.drafts import add_draft
    draft_id = add_draft(platform, content, topic)
    return f"Draft saved (ID: {draft_id}) — awaiting approval in dashboard."


SYSTEM_PROMPT = f"""
You are the content creator for {CLIENT_NAME}, a {CLIENT_INDUSTRY} brand.
Tone: {CLIENT_TONE}.

Your job:
1. Use recall_business_context to ground every post in real business knowledge.
2. Create platform-native content (LinkedIn = thought leadership, Instagram = visual hooks,
   Facebook = community-friendly, Telegram = concise updates).
3. Always include a clear CTA.
4. {"Save the post as a draft using save_draft — DO NOT publish directly." if DRAFT_MODE else "Publish using the appropriate posting tool."}
5. After saving/posting, log the content with ingest_text to 'posts' memory.

Never fabricate facts about the business. Always recall context first.
"""


def build_content_agent():
    tools = [recall_business_context, ingest_text]
    if DRAFT_MODE:
        tools.append(save_draft)
    else:
        tools += [linkedin_post, instagram_post, facebook_post, telegram_post]

    return Agent(
        model=get_model(),
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
    )
