"""
Master Orchestrator — the top-level agent that delegates tasks to
specialised sub-agents based on the current schedule or incoming trigger.
"""
import time
from strands import Agent, tool
from core.model_factory import get_model
from config.settings import CLIENT_NAME

# ── Sub-agent runners exposed as tools ────────────────────────────────────

@tool
def run_content_creation(platform: str, topic: str = "") -> str:
    """Trigger the content agent to create and publish a post.

    Args:
        platform: Target platform (linkedin | instagram | facebook | telegram | all).
        topic: Optional topic hint. If empty, agent decides based on business context.
    """
    from agents.content_agent import build_content_agent
    agent = build_content_agent()
    prompt = f"Create and publish a {platform} post"
    if topic:
        prompt += f" about: {topic}"
    else:
        prompt += ". Choose the best topic based on business context and recent posts."
    return str(agent(prompt))


@tool
def run_engagement(platform: str, context: str) -> str:
    """Trigger the engagement agent to respond to interactions.

    Args:
        platform: Platform where engagement is needed.
        context: Description of the interaction (e.g. 'comment on post X saying Y').
    """
    from agents.engagement_agent import build_engagement_agent
    agent = build_engagement_agent()
    return str(agent(f"Handle this {platform} interaction: {context}"))


@tool
def run_lead_generation(keywords: str = "") -> str:
    """Trigger the lead agent to find and connect with new prospects on LinkedIn.

    Args:
        keywords: Optional keyword override. Defaults to ICP from business memory.
    """
    from agents.lead_agent import build_lead_agent
    agent = build_lead_agent()
    prompt = "Run today's lead generation session on LinkedIn."
    if keywords:
        prompt += f" Focus on: {keywords}"
    return str(agent(prompt))


@tool
def run_followups() -> str:
    """Trigger the follow-up agent to process pending email sequences and bookings."""
    from agents.followup_agent import build_followup_agent
    agent = build_followup_agent()
    return str(agent("Process all pending follow-ups and check for new Calendly bookings."))


@tool
def run_learning() -> str:
    """Trigger the learning agent to ingest new data and update business memory."""
    from agents.learning_agent import run_learning_cycle
    run_learning_cycle()
    time.sleep(2)
    return "Learning cycle complete."


# ── Orchestrator agent ─────────────────────────────────────────────────────

SYSTEM_PROMPT = f"""
You are the master orchestrator for {CLIENT_NAME}'s autonomous social media system.

You coordinate five specialised agents:
- Content Agent: creates and publishes posts
- Engagement Agent: handles comments, replies, DMs
- Lead Agent: finds and nurtures LinkedIn leads
- Follow-up Agent: manages email sequences and Calendly bookings
- Learning Agent: ingests business data and improves the system

When given a task or schedule trigger, delegate to the right agent using the tools.
Prioritise: learning first (so agents have fresh context), then content, then leads,
then engagement, then follow-ups.

Always report what was done and any issues encountered.
"""

def build_orchestrator():
    return Agent(
        model=get_model(),
        tools=[
            run_content_creation,
            run_engagement,
            run_lead_generation,
            run_followups,
            run_learning,
        ],
        system_prompt=SYSTEM_PROMPT,
    )
