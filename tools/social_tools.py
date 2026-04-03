"""
Strands @tool wrappers for all social media platforms.
Each tool is self-contained and safe to call from any agent.
"""
from strands import tool
from config.settings import LINKEDIN, INSTAGRAM, FACEBOOK, TELEGRAM, WHATSAPP, TIKTOK


# ── LinkedIn ───────────────────────────────────────────────────────────────

@tool
def linkedin_post(text: str) -> str:
    """Post content to LinkedIn.

    Args:
        text: The post content to publish.
    """
    try:
        from linkedin_api import Linkedin
        api = Linkedin(LINKEDIN["email"], LINKEDIN["password"])
        api.post(text)
        return f"LinkedIn post published: {text[:60]}..."
    except Exception as e:
        return f"LinkedIn post failed: {e}"


@tool
def linkedin_search_leads(keywords: str, limit: int = 10) -> str:
    """Search LinkedIn for potential leads by keywords.

    Args:
        keywords: Job title or keywords to search (e.g. 'CTO fintech startup').
        limit: Max number of profiles to return.
    """
    try:
        from linkedin_api import Linkedin
        api = Linkedin(LINKEDIN["email"], LINKEDIN["password"])
        results = api.search_people(keywords=keywords, limit=limit)
        leads = [
            f"{r.get('firstName','')} {r.get('lastName','')} — {r.get('headline','')}"
            for r in results
        ]
        return "\n".join(leads) if leads else "No leads found."
    except Exception as e:
        return f"LinkedIn search failed: {e}"


@tool
def linkedin_connect(profile_urn: str, message: str = "") -> str:
    """Send a LinkedIn connection request with an optional note.

    Args:
        profile_urn: LinkedIn profile URN (e.g. 'urn:li:fs_miniProfile:ABC123').
        message: Optional personalised connection note (max 300 chars).
    """
    try:
        from linkedin_api import Linkedin
        api = Linkedin(LINKEDIN["email"], LINKEDIN["password"])
        api.add_connection(profile_urn, message=message[:300])
        return f"Connection request sent to {profile_urn}"
    except Exception as e:
        return f"LinkedIn connect failed: {e}"


@tool
def linkedin_comment(post_urn: str, comment: str) -> str:
    """Comment on a LinkedIn post.

    Args:
        post_urn: URN of the post to comment on.
        comment: Comment text.
    """
    try:
        from linkedin_api import Linkedin
        api = Linkedin(LINKEDIN["email"], LINKEDIN["password"])
        api.comment(post_urn, comment)
        return "Comment posted on LinkedIn."
    except Exception as e:
        return f"LinkedIn comment failed: {e}"


# ── Instagram ──────────────────────────────────────────────────────────────

@tool
def instagram_post(caption: str, image_path: str) -> str:
    """Post a photo to Instagram.

    Args:
        caption: Caption text for the post.
        image_path: Local path to the image file.
    """
    try:
        from instagrapi import Client
        cl = Client()
        cl.login(INSTAGRAM["username"], INSTAGRAM["password"])
        cl.photo_upload(image_path, caption)
        return "Instagram post published."
    except Exception as e:
        return f"Instagram post failed: {e}"


@tool
def instagram_comment(media_id: str, comment: str) -> str:
    """Comment on an Instagram post.

    Args:
        media_id: Instagram media ID.
        comment: Comment text.
    """
    try:
        from instagrapi import Client
        cl = Client()
        cl.login(INSTAGRAM["username"], INSTAGRAM["password"])
        cl.media_comment(media_id, comment)
        return "Instagram comment posted."
    except Exception as e:
        return f"Instagram comment failed: {e}"


# ── Facebook ───────────────────────────────────────────────────────────────

@tool
def facebook_post(message: str) -> str:
    """Post content to a Facebook Page.

    Args:
        message: The post content.
    """
    try:
        import facebook
        graph = facebook.GraphAPI(access_token=FACEBOOK["access_token"])
        graph.put_object(FACEBOOK["page_id"], "feed", message=message)
        return "Facebook post published."
    except Exception as e:
        return f"Facebook post failed: {e}"


# ── Telegram ───────────────────────────────────────────────────────────────

@tool
def telegram_post(message: str) -> str:
    """Send a message to a Telegram channel.

    Args:
        message: Message text (supports Markdown).
    """
    try:
        import asyncio
        from telegram import Bot
        async def _send():
            bot = Bot(token=TELEGRAM["bot_token"])
            await bot.send_message(chat_id=TELEGRAM["channel_id"], text=message, parse_mode="Markdown")
        asyncio.run(_send())
        return "Telegram message sent."
    except Exception as e:
        return f"Telegram post failed: {e}"


# ── WhatsApp ───────────────────────────────────────────────────────────────

@tool
def whatsapp_send(to_number: str, message: str) -> str:
    """Send a WhatsApp message via Twilio.

    Args:
        to_number: Recipient WhatsApp number in E.164 format (e.g. +1234567890).
        message: Message text.
    """
    try:
        from twilio.rest import Client
        client = Client(WHATSAPP["account_sid"], WHATSAPP["auth_token"])
        client.messages.create(
            from_=WHATSAPP["from_number"],
            to=f"whatsapp:{to_number}",
            body=message,
        )
        return f"WhatsApp message sent to {to_number}."
    except Exception as e:
        return f"WhatsApp send failed: {e}"
