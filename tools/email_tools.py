"""
Email (SendGrid) and Calendly booking tools.
"""
from strands import tool
from config.settings import EMAIL, CALENDLY
import requests


@tool
def send_email(to_address: str, subject: str, body: str) -> str:
    """Send a follow-up email via SendGrid.

    Args:
        to_address: Recipient email address.
        subject: Email subject line.
        body: Plain-text email body.
    """
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
        msg = Mail(
            from_email=EMAIL["from_address"],
            to_emails=to_address,
            subject=subject,
            plain_text_content=body,
        )
        sg = SendGridAPIClient(EMAIL["sendgrid_key"])
        sg.send(msg)
        return f"Email sent to {to_address}."
    except Exception as e:
        return f"Email failed: {e}"


@tool
def send_calendly_invite(to_address: str, lead_name: str) -> str:
    """Send a Calendly booking link via email to a lead.

    Args:
        to_address: Lead's email address.
        lead_name: Lead's first name for personalisation.
    """
    booking_link = CALENDLY["event_url"]
    body = (
        f"Hi {lead_name},\n\n"
        f"I'd love to connect and learn more about your goals. "
        f"Feel free to grab a time that works for you:\n\n"
        f"{booking_link}\n\n"
        f"Looking forward to speaking soon!"
    )
    return send_email(to_address, "Let's connect — book a quick call", body)


@tool
def get_calendly_upcoming_events() -> str:
    """Fetch upcoming scheduled Calendly events.

    Returns a summary of booked meetings.
    """
    try:
        headers = {"Authorization": f"Bearer {CALENDLY['api_key']}"}
        me = requests.get("https://api.calendly.com/users/me", headers=headers).json()
        user_uri = me["resource"]["uri"]
        events = requests.get(
            "https://api.calendly.com/scheduled_events",
            headers=headers,
            params={"user": user_uri, "status": "active", "count": 10},
        ).json()
        items = events.get("collection", [])
        if not items:
            return "No upcoming Calendly events."
        summary = "\n".join(
            f"- {e['name']} at {e['start_time']}" for e in items
        )
        return f"Upcoming meetings:\n{summary}"
    except Exception as e:
        return f"Calendly fetch failed: {e}"
