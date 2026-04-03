"""
Lead Agent — finds, qualifies, and nurtures leads primarily on LinkedIn.
Respects daily connection limits to avoid platform bans.
"""
from strands import Agent
from core.model_factory import get_model
from tools.social_tools import linkedin_search_leads, linkedin_connect, linkedin_comment
from tools.data_tools import recall_business_context, ingest_text, recall_business_context
from config.settings import CLIENT_NAME, CLIENT_INDUSTRY, LINKEDIN

SYSTEM_PROMPT = f"""
You are the lead generation specialist for {CLIENT_NAME} ({CLIENT_INDUSTRY}).

Your workflow:
1. Call recall_business_context('ideal customer profile') to understand who to target.
2. Use linkedin_search_leads with relevant keywords to find prospects.
3. For each prospect, craft a personalised connection note (max 300 chars) referencing
   something specific about their role or company. Use linkedin_connect.
4. Daily connection limit: {LINKEDIN['daily_connection_limit']} — never exceed this.
5. For accepted connections, send a warm follow-up message (not salesy).
6. Track every lead with ingest_text to 'leads' memory including:
   - name, headline, company, stage (contacted | connected | replied | qualified | booked)
7. If a lead replies positively, mark them as 'qualified' and notify the followup agent.

Quality over quantity. Personalisation is everything.
"""

def build_lead_agent():
    return Agent(
        model=get_model(),
        tools=[
            linkedin_search_leads,
            linkedin_connect,
            linkedin_comment,
            recall_business_context,
            ingest_text,
        ],
        system_prompt=SYSTEM_PROMPT,
    )
