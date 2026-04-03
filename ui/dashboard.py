"""
Streamlit dashboard for the Autonomous Social Media Agent System.
Run with: streamlit run ui/dashboard.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
from datetime import datetime
from core import memory
from core.drafts import get_drafts, update_status, delete_draft
from config.settings import CLIENT_NAME, CLIENT_INDUSTRY, CLIENT_TONE

DRAFT_MODE = os.getenv("DRAFT_MODE", "true").lower() == "true"

st.set_page_config(
    page_title=f"{CLIENT_NAME} — Agent Dashboard",
    page_icon="🤖",
    layout="wide",
)

# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🤖 Agent Control")
    st.caption(f"{CLIENT_NAME} · {CLIENT_INDUSTRY} · {CLIENT_TONE}")
    mode_label = "✋ Draft Mode (approval required)" if DRAFT_MODE else "🚀 Auto-publish Mode"
    st.info(mode_label)
    st.divider()

    st.subheader("Run a Task Now")
    task = st.selectbox("Select task", ["content", "learn", "leads", "followups", "engage"])
    platform = st.selectbox("Platform", ["linkedin", "instagram", "facebook", "telegram", "all"])
    topic_input = st.text_input("Topic / Context", placeholder="e.g. AI trends in 2026")

    if st.button("▶ Run Task", use_container_width=True, type="primary"):
        with st.spinner(f"Running {task}..."):
            try:
                from agents.orchestrator import build_orchestrator
                orch = build_orchestrator()
                task_map = {
                    "content":   f"run_content_creation for platform: {platform}" + (f", topic: {topic_input}" if topic_input else ""),
                    "leads":     "run_lead_generation" + (f" focus: {topic_input}" if topic_input else ""),
                    "followups": "run_followups",
                    "learn":     "run_learning",
                    "engage":    f"run_engagement — context: {topic_input or 'check all platforms'}",
                }
                result = orch(task_map[task])
                st.session_state["last_result"] = str(result)
                st.success("Done!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    st.divider()
    st.subheader("Upload Business Data")
    uploaded = st.file_uploader("PDF, TXT or MD", type=["pdf", "txt", "md"])
    if uploaded and st.button("Save & Ingest", use_container_width=True):
        save_path = f"data/business/{uploaded.name}"
        os.makedirs("data/business", exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(uploaded.getbuffer())
        st.success(f"Saved. Run 'learn' task to ingest.")

# ── Main tabs ──────────────────────────────────────────────────────────────
st.title(f"🤖 {CLIENT_NAME} — Social Agent Dashboard")
st.caption(f"Groq · Strands Agents · {datetime.now().strftime('%d %b %Y %H:%M')}")

tab_drafts, tab_leads, tab_posts, tab_engage, tab_knowledge = st.tabs([
    "✋ Drafts Queue", "👥 Leads", "📝 Posts", "💬 Engagement", "📚 Knowledge"
])

# ── Tab 1: Drafts approval ─────────────────────────────────────────────────
with tab_drafts:
    pending = get_drafts(status="pending")
    approved = get_drafts(status="approved")
    rejected = get_drafts(status="rejected")

    col1, col2, col3 = st.columns(3)
    col1.metric("⏳ Pending", len(pending))
    col2.metric("✅ Approved", len(approved))
    col3.metric("❌ Rejected", len(rejected))

    st.divider()

    if not pending:
        st.info("No drafts waiting for approval. Run the 'content' task to generate posts.")
    else:
        st.subheader(f"⏳ {len(pending)} post(s) awaiting your approval")
        for draft in pending:
            with st.container(border=True):
                col_meta, col_actions = st.columns([3, 1])
                with col_meta:
                    st.markdown(f"**Platform:** `{draft['platform'].upper()}`  |  **Topic:** {draft.get('topic') or '—'}  |  **Created:** {draft['created_at'][:16]}")
                    st.text_area(
                        "Content",
                        draft["content"],
                        height=150,
                        key=f"content_{draft['id']}",
                        disabled=False,
                    )
                with col_actions:
                    st.markdown("###")
                    if st.button("✅ Approve & Publish", key=f"approve_{draft['id']}", use_container_width=True, type="primary"):
                        # Publish now
                        try:
                            platform = draft["platform"]
                            content = draft["content"]
                            if platform == "linkedin":
                                from tools.social_tools import linkedin_post
                                linkedin_post(content)
                            elif platform == "instagram":
                                from tools.social_tools import instagram_post
                                st.warning("Instagram requires an image path — post manually.")
                            elif platform == "facebook":
                                from tools.social_tools import facebook_post
                                facebook_post(content)
                            elif platform == "telegram":
                                from tools.social_tools import telegram_post
                                telegram_post(content)
                            update_status(draft["id"], "approved")
                            st.success("Published!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Publish failed: {e}")

                    if st.button("✏️ Edit & Approve", key=f"edit_{draft['id']}", use_container_width=True):
                        update_status(draft["id"], "approved")
                        st.info("Marked approved. Edit content above and re-run publish manually.")
                        st.rerun()

                    if st.button("❌ Reject", key=f"reject_{draft['id']}", use_container_width=True):
                        update_status(draft["id"], "rejected")
                        st.rerun()

    if approved or rejected:
        st.divider()
        with st.expander("View approved / rejected history"):
            for d in (approved + rejected)[-20:][::-1]:
                icon = "✅" if d["status"] == "approved" else "❌"
                st.markdown(f"{icon} `{d['platform'].upper()}` — {d['content'][:100]}...")

# ── Tab 2: Leads ───────────────────────────────────────────────────────────
with tab_leads:
    leads = memory.recall_all("leads")
    st.metric("Total leads tracked", len(leads))
    if leads:
        for lead in leads[::-1]:
            st.markdown(f"- {lead[:200]}")
    else:
        st.info("No leads yet. Run the 'leads' task.")

# ── Tab 3: Posts ───────────────────────────────────────────────────────────
with tab_posts:
    posts = memory.recall_all("posts")
    st.metric("Total posts published", len(posts))
    if posts:
        for post in posts[::-1]:
            with st.expander(post[:80] + "..."):
                st.write(post)
    else:
        st.info("No posts published yet.")

# ── Tab 4: Engagement ──────────────────────────────────────────────────────
with tab_engage:
    col_eng, col_fu = st.columns(2)
    with col_eng:
        st.subheader("💬 Engagements")
        engagements = memory.recall_all("engagement")
        if engagements:
            for e in engagements[::-1]:
                st.markdown(f"- {e[:150]}")
        else:
            st.info("No engagements logged yet.")
    with col_fu:
        st.subheader("📧 Follow-ups")
        followups = memory.recall_all("followups")
        if followups:
            for f in followups[::-1]:
                st.markdown(f"- {f[:150]}")
        else:
            st.info("No follow-ups yet.")

# ── Tab 5: Knowledge base ──────────────────────────────────────────────────
with tab_knowledge:
    st.subheader("Search business knowledge")
    query = st.text_input("Query", placeholder="e.g. target audience, product features, tone of voice")
    if query:
        results = memory.recall("business", query, n=5)
        if results:
            for r in results:
                st.info(r[:600])
        else:
            st.warning("Nothing found. Upload docs and run 'learn' first.")

    st.divider()
    st.subheader("All stored knowledge")
    all_docs = memory.recall_all("business")
    st.caption(f"{len(all_docs)} documents in memory")
    for doc in all_docs:
        with st.expander(doc[:80] + "..."):
            st.write(doc)

# ── Last agent output ──────────────────────────────────────────────────────
if "last_result" in st.session_state:
    with st.expander("🧠 Last agent output"):
        st.text(st.session_state["last_result"])
