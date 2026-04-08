"""
Telegram Bot Interface — chat with your agent system via Telegram.

Commands:
  /start        — welcome message
  /status       — show metrics (leads, posts, drafts)
  /content      — generate a post (goes to drafts queue)
  /leads        — run lead generation
  /followups    — process follow-ups
  /learn        — run learning cycle
  /drafts       — show pending drafts
  /approve <id> — approve and publish a draft
  /reject <id>  — reject a draft
  /ask <text>   — ask the orchestrator anything

Run with: python interfaces/telegram_bot.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import asyncio
import logging
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN   = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_IDS = os.getenv("TELEGRAM_ALLOWED_IDS", "")  # comma-separated chat IDs, empty = allow all


def is_allowed(update: Update) -> bool:
    if not ALLOWED_IDS:
        return True
    allowed = [x.strip() for x in ALLOWED_IDS.split(",")]
    return str(update.effective_chat.id) in allowed


def run_agent_task(task_prompt: str) -> str:
    try:
        from agents.orchestrator import build_orchestrator
        orch = build_orchestrator()
        return str(orch(task_prompt))
    except Exception as e:
        return f"Error: {e}"


# ── Command handlers ───────────────────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return
    from config.settings import CLIENT_NAME
    await update.message.reply_text(
        f"👋 Hi! I'm the AI agent for *{CLIENT_NAME}*.\n\n"
        f"Commands:\n"
        f"/status — system overview\n"
        f"/content — generate a post\n"
        f"/leads — find new leads\n"
        f"/followups — process follow-ups\n"
        f"/learn — ingest new data\n"
        f"/drafts — pending approvals\n"
        f"/approve <id> — publish a draft\n"
        f"/reject <id> — reject a draft\n"
        f"/ask <question> — ask me anything",
        parse_mode="Markdown"
    )


async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return
    from core import memory
    from core.drafts import get_drafts
    posts    = len(memory.recall_all("posts"))
    leads    = len(memory.recall_all("leads"))
    pending  = len(get_drafts("pending"))
    followups = len(memory.recall_all("followups"))
    await update.message.reply_text(
        f"📊 *System Status*\n\n"
        f"📝 Posts published: {posts}\n"
        f"👥 Leads tracked: {leads}\n"
        f"⏳ Drafts pending: {pending}\n"
        f"📧 Follow-ups sent: {followups}",
        parse_mode="Markdown"
    )


async def cmd_content(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return
    topic = " ".join(ctx.args) if ctx.args else ""
    await update.message.reply_text("✍️ Generating content draft...")
    prompt = f"run_content_creation for platform: linkedin" + (f", topic: {topic}" if topic else "")
    result = run_agent_task(prompt)
    # Show pending drafts after generation
    from core.drafts import get_drafts
    pending = get_drafts("pending")
    if pending:
        latest = pending[-1]
        await update.message.reply_text(
            f"✅ Draft saved (ID: `{latest['id']}`)\n\n"
            f"*Platform:* {latest['platform'].upper()}\n\n"
            f"{latest['content'][:800]}\n\n"
            f"Reply /approve {latest['id']} to publish or /reject {latest['id']} to discard.",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(result[:1000])


async def cmd_leads(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return
    keywords = " ".join(ctx.args) if ctx.args else ""
    await update.message.reply_text("🔍 Running lead generation...")
    prompt = "run_lead_generation" + (f" focus: {keywords}" if keywords else "")
    result = run_agent_task(prompt)
    await update.message.reply_text(result[:1000])


async def cmd_followups(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return
    await update.message.reply_text("📧 Processing follow-ups...")
    result = run_agent_task("run_followups")
    await update.message.reply_text(result[:1000])


async def cmd_learn(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return
    await update.message.reply_text("🧠 Running learning cycle...")
    result = run_agent_task("run_learning")
    await update.message.reply_text(result[:1000])


async def cmd_drafts(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return
    from core.drafts import get_drafts
    pending = get_drafts("pending")
    if not pending:
        await update.message.reply_text("No drafts pending approval.")
        return
    msg = f"⏳ *{len(pending)} draft(s) pending:*\n\n"
    for d in pending[-5:]:
        msg += f"ID: `{d['id']}` | {d['platform'].upper()}\n{d['content'][:200]}...\n\n"
    msg += "Use /approve <id> or /reject <id>"
    await update.message.reply_text(msg, parse_mode="Markdown")


async def cmd_approve(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return
    if not ctx.args:
        await update.message.reply_text("Usage: /approve <draft_id>")
        return
    draft_id = ctx.args[0]
    from core.drafts import get_drafts, update_status
    drafts = [d for d in get_drafts("pending") if d["id"] == draft_id]
    if not drafts:
        await update.message.reply_text(f"Draft {draft_id} not found.")
        return
    draft = drafts[0]
    try:
        platform = draft["platform"]
        content  = draft["content"]
        if platform == "linkedin":
            from tools.social_tools import linkedin_post
            linkedin_post(content)
        elif platform == "facebook":
            from tools.social_tools import facebook_post
            facebook_post(content)
        elif platform == "telegram":
            from tools.social_tools import telegram_post
            telegram_post(content)
        update_status(draft_id, "approved")
        await update.message.reply_text(f"✅ Draft `{draft_id}` approved and published to {platform.upper()}!", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Publish failed: {e}")


async def cmd_reject(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return
    if not ctx.args:
        await update.message.reply_text("Usage: /reject <draft_id>")
        return
    from core.drafts import update_status
    update_status(ctx.args[0], "rejected")
    await update.message.reply_text(f"❌ Draft `{ctx.args[0]}` rejected.", parse_mode="Markdown")


async def cmd_ask(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return
    if not ctx.args:
        await update.message.reply_text("Usage: /ask <your question>")
        return
    question = " ".join(ctx.args)
    await update.message.reply_text("🤔 Thinking...")
    result = run_agent_task(question)
    await update.message.reply_text(result[:1000])


async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle plain text messages as free-form agent queries."""
    if not is_allowed(update):
        return
    text = update.message.text
    await update.message.reply_text("🤔 On it...")
    result = run_agent_task(text)
    await update.message.reply_text(result[:1000])


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    if not BOT_TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN not set in .env")
        return

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",     cmd_start))
    app.add_handler(CommandHandler("status",    cmd_status))
    app.add_handler(CommandHandler("content",   cmd_content))
    app.add_handler(CommandHandler("leads",     cmd_leads))
    app.add_handler(CommandHandler("followups", cmd_followups))
    app.add_handler(CommandHandler("learn",     cmd_learn))
    app.add_handler(CommandHandler("drafts",    cmd_drafts))
    app.add_handler(CommandHandler("approve",   cmd_approve))
    app.add_handler(CommandHandler("reject",    cmd_reject))
    app.add_handler(CommandHandler("ask",       cmd_ask))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Telegram bot running... Press Ctrl+C to stop.")
    app.run_polling()


if __name__ == "__main__":
    main()
