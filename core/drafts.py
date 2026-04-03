"""
Drafts queue — stores agent-generated posts for human review before publishing.
Uses a simple JSON file so it persists across restarts.
"""
import json
import os
import uuid
from datetime import datetime

DRAFTS_FILE = "./data/drafts.json"


def _load() -> list:
    if not os.path.exists(DRAFTS_FILE):
        return []
    with open(DRAFTS_FILE, "r") as f:
        return json.load(f)


def _save(drafts: list):
    os.makedirs(os.path.dirname(DRAFTS_FILE), exist_ok=True)
    with open(DRAFTS_FILE, "w") as f:
        json.dump(drafts, f, indent=2)


def add_draft(platform: str, content: str, topic: str = "") -> str:
    """Add a new draft post to the queue. Returns the draft ID."""
    drafts = _load()
    draft_id = str(uuid.uuid4())[:8]
    drafts.append({
        "id":        draft_id,
        "platform":  platform,
        "content":   content,
        "topic":     topic,
        "status":    "pending",   # pending | approved | rejected
        "created_at": datetime.now().isoformat(),
        "reviewed_at": None,
    })
    _save(drafts)
    return draft_id


def get_drafts(status: str = None) -> list:
    """Get all drafts, optionally filtered by status."""
    drafts = _load()
    if status:
        return [d for d in drafts if d["status"] == status]
    return drafts


def update_status(draft_id: str, status: str):
    """Approve or reject a draft."""
    drafts = _load()
    for d in drafts:
        if d["id"] == draft_id:
            d["status"] = status
            d["reviewed_at"] = datetime.now().isoformat()
            break
    _save(drafts)


def delete_draft(draft_id: str):
    drafts = [d for d in _load() if d["id"] != draft_id]
    _save(drafts)
