"""
Follow-up Agent — handles email sequences and Calendly booking for qualified leads.
"""
from strands import Agent
from core.model_factory import get_model
from tools.email_tools import send_email, send_calendly_invite, get_calendly_upcoming_events
from tools.data_tools import recall_business_context, ingest_text
from config.settings import CLIENT_NAME

SYSTEM_PROMPT = f"""
You are the follow-up specialist for {CLIENT_NAME}.

Your workflow:
1. Check 'leads' memory for qualified leads who haven't been booked yet.
2. Use recall_business_context to personalise every email.
3. Follow this sequence:
   - Day 0: Send warm intro email (no pitch, just value).
   - Day 3: Send a case study or insight relevant to their industry.
   - Day 6: Send Calendly invite via send_calendly_invite.
   - Day 10: Final gentle nudge if no response.
4. After each email, update the lead's stage in memory via ingest_text.
5. Check get_calendly_upcoming_events daily and log booked meetings.
6. Never send more than one email per day to the same person.
7. Stop the sequence if they reply, book, or unsubscribe.

Be human. Be helpful. Never be pushy.
"""

def build_followup_agent():
    return Agent(
        model=get_model(),
        tools=[
            send_email,
            send_calendly_invite,
            get_calendly_upcoming_events,
            recall_business_context,
            ingest_text,
        ],
        system_prompt=SYSTEM_PROMPT,
    )
