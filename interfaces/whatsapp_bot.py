"""
WhatsApp Bot Interface via Twilio — chat with your agent system over WhatsApp.

How it works:
  Twilio receives your WhatsApp message → sends webhook to this Flask server
  → agent processes it → replies back to your WhatsApp.

Setup:
  1. Create a Twilio account at twilio.com
  2. Enable WhatsApp sandbox: Twilio Console → Messaging → Try it out → WhatsApp
  3. Set webhook URL in Twilio to: https://your-server/whatsapp
     (use ngrok for local testing: ngrok http 5001)
  4. Fill TWILIO_* vars in .env

Run with: python interfaces/whatsapp_bot.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from dotenv import load_dotenv
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

ACCOUNT_SID  = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN   = os.getenv("TWILIO_AUTH_TOKEN")
FROM_NUMBER  = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
ALLOWED_NUMBERS = os.getenv("WHATSAPP_ALLOWED_NUMBERS", "")  # comma-separated, empty = allow all


def is_allowed(from_number: str) -> bool:
    if not ALLOWED_NUMBERS:
        return True
    allowed = [x.strip() for x in ALLOWED_NUMBERS.split(",")]
    return any(from_number.endswith(n.replace("+", "")) for n in allowed)


def run_agent_task(prompt: str) -> str:
    try:
        from agents.orchestrator import build_orchestrator
        orch = build_orchestrator()
        return str(orch(prompt))[:1500]
    except Exception as e:
        return f"Error: {e}"


def parse_command(text: str) -> str:
    """Parse WhatsApp message and route to the right agent task."""
    text = text.strip().lower()

    if text in ["hi", "hello", "start", "help"]:
        from config.settings import CLIENT_NAME
        return (
            f"👋 Hi! I'm the AI agent for {CLIENT_NAME}.\n\n"
            "Commands:\n"
            "• status — system overview\n"
            "• post <topic> — generate a post\n"
            "• leads <keywords> — find leads\n"
            "• followups — process follow-ups\n"
            "• learn — ingest new data\n"
            "• drafts — pending approvals\n"
            "• approve <id> — publish draft\n"
            "• reject <id> — reject draft\n"
            "• Or just ask me anything!"
        )

    if text == "status":
        from core import memory
        from core.drafts import get_drafts
        return (
            f"📊 Status\n"
            f"Posts: {len(memory.recall_all('posts'))}\n"
            f"Leads: {len(memory.recall_all('leads'))}\n"
            f"Pending drafts: {len(get_drafts('pending'))}\n"
            f"Follow-ups: {len(memory.recall_all('followups'))}"
        )

    if text.startswith("post"):
        topic = text[4:].strip()
        prompt = "run_content_creation for platform: linkedin" + (f", topic: {topic}" if topic else "")
        run_agent_task(prompt)
        from core.drafts import get_drafts
        pending = get_drafts("pending")
        if pending:
            d = pending[-1]
            return (
                f"✅ Draft saved (ID: {d['id']})\n\n"
                f"{d['content'][:600]}\n\n"
                f"Reply: approve {d['id']} or reject {d['id']}"
            )
        return "Draft generated — check dashboard."

    if text.startswith("leads"):
        keywords = text[5:].strip()
        prompt = "run_lead_generation" + (f" focus: {keywords}" if keywords else "")
        return run_agent_task(prompt)

    if text == "followups":
        return run_agent_task("run_followups")

    if text == "learn":
        return run_agent_task("run_learning")

    if text == "drafts":
        from core.drafts import get_drafts
        pending = get_drafts("pending")
        if not pending:
            return "No drafts pending."
        msg = f"⏳ {len(pending)} pending:\n\n"
        for d in pending[-3:]:
            msg += f"ID: {d['id']} | {d['platform'].upper()}\n{d['content'][:150]}...\n\n"
        return msg

    if text.startswith("approve "):
        draft_id = text.split(" ", 1)[1].strip()
        from core.drafts import get_drafts, update_status
        drafts = [d for d in get_drafts("pending") if d["id"] == draft_id]
        if not drafts:
            return f"Draft {draft_id} not found."
        draft = drafts[0]
        try:
            if draft["platform"] == "linkedin":
                from tools.social_tools import linkedin_post
                linkedin_post(draft["content"])
            elif draft["platform"] == "facebook":
                from tools.social_tools import facebook_post
                facebook_post(draft["content"])
            elif draft["platform"] == "telegram":
                from tools.social_tools import telegram_post
                telegram_post(draft["content"])
            update_status(draft_id, "approved")
            return f"✅ Published to {draft['platform'].upper()}!"
        except Exception as e:
            return f"Publish failed: {e}"

    if text.startswith("reject "):
        draft_id = text.split(" ", 1)[1].strip()
        from core.drafts import update_status
        update_status(draft_id, "rejected")
        return f"❌ Draft {draft_id} rejected."

    # Free-form — pass directly to orchestrator
    return run_agent_task(text)


@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    from_number = request.form.get("From", "")
    body = request.form.get("Body", "").strip()

    if not is_allowed(from_number):
        resp = MessagingResponse()
        resp.message("Unauthorized.")
        return str(resp)

    reply = parse_command(body)

    resp = MessagingResponse()
    resp.message(reply)
    return str(resp)


@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    print("🤖 WhatsApp bot running on http://localhost:5001")
    print("Set Twilio webhook to: https://your-domain/whatsapp")
    print("For local testing: ngrok http 5001")
    app.run(port=5001, debug=False)
