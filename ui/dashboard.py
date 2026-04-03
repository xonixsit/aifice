"""
Streamlit dashboard for the Autonomous Social Media Agent System.
Run with: streamlit run ui/dashboard.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import json
from datetime import datetime
from core import memory
from config.settings import CLIENT_NAME, CLIENT_INDUSTRY, CLIENT_TONE

st.set_page_config(
    page_title=f"{CLIENT_NAME} — Agent Dashboard",
    page_icon="🤖",
    layout="wide",
)

# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🤖 Agent Control")
    st.caption(f"{CLIENT_NAME} · {CLIENT_INDUSTRY} · {CLIENT_TONE}")
    st.divider()

    st.subheader("Run a Task Now")
    task = st.selectbox("Select task", ["learn", "content", "leads", "followups", "engage"])
    platform = st.selectbox("Platform (content only)", ["linkedin", "instagram", "facebook", "telegram", "all"])
    context_input = st.text_input("Context (engage only)", placeholder="e.g. someone asked about pricing")

    if st.button("▶ Run Task", use_container_width=True, type="primary"):
        with st.spinner(f"Running {task}..."):
            try:
                from agents.orchestrator import build_orchestrator
                orch = build_orchestrator()
                task_map = {
                    "content":   f"run_content_creation for platform: {platform}",
                    "leads":     "run_lead_generation",
                    "followups": "run_followups",
                    "learn":     "run_learning",
                    "engage":    f"run_engagement — context: {context_input or 'check all platforms'}",
                }
                result = orch(task_map[task])
                st.session_state["last_result"] = str(result)
                st.success("Done!")
            except Exception as e:
                st.error(f"Error: {e}")

    st.divider()
    st.subheader("Ingest Business Data")
    uploaded = st.file_uploader("Upload PDF or TXT", type=["pdf", "txt", "md"])
    if uploaded and st.button("Ingest File", use_container_width=True):
        save_path = f"data/business/{uploaded.name}"
        with open(save_path, "wb") as f:
            f.write(uploaded.getbuffer())
        st.success(f"Saved to {save_path} — run 'learn' task to ingest.")

# ── Main area ──────────────────────────────────────────────────────────────
st.title(f"🤖 {CLIENT_NAME} — Social Agent Dashboard")
st.caption(f"Powered by Groq · Strands Agents · Last refresh: {datetime.now().strftime('%H:%M:%S')}")

# ── Metrics row ────────────────────────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5)

def count_collection(name):
    try:
        docs = memory.recall_all(name)
        return len(docs)
    except:
        return 0

col1.metric("📚 Business Docs", count_collection("business"))
col2.metric("📝 Posts Published", count_collection("posts"))
col3.metric("👥 Leads Tracked", count_collection("leads"))
col4.metric("💬 Engagements", count_collection("engagement"))
col5.metric("📧 Follow-ups", count_collection("followups"))

st.divider()

# ── Two column layout ──────────────────────────────────────────────────────
left, right = st.columns(2)

with left:
    st.subheader("👥 Recent Leads")
    leads = memory.recall_all("leads")
    if leads:
        for lead in leads[-10:][::-1]:
            st.markdown(f"- {lead[:120]}...")
    else:
        st.info("No leads yet. Run the 'leads' task to start prospecting.")

    st.subheader("📝 Recent Posts")
    posts = memory.recall_all("posts")
    if posts:
        for post in posts[-5:][::-1]:
            with st.expander(post[:80] + "..."):
                st.write(post)
    else:
        st.info("No posts yet. Run the 'content' task to publish.")

with right:
    st.subheader("💬 Recent Engagements")
    engagements = memory.recall_all("engagement")
    if engagements:
        for eng in engagements[-10:][::-1]:
            st.markdown(f"- {eng[:120]}...")
    else:
        st.info("No engagements logged yet.")

    st.subheader("📧 Follow-up Status")
    followups = memory.recall_all("followups")
    if followups:
        for fu in followups[-10:][::-1]:
            st.markdown(f"- {fu[:120]}...")
    else:
        st.info("No follow-ups yet.")

# ── Last agent output ──────────────────────────────────────────────────────
if "last_result" in st.session_state:
    st.divider()
    st.subheader("🧠 Last Agent Output")
    st.text_area("", st.session_state["last_result"], height=200)

# ── Business context viewer ────────────────────────────────────────────────
st.divider()
st.subheader("📚 Business Knowledge Base")
query = st.text_input("Search business context", placeholder="e.g. target audience, product features")
if query:
    results = memory.recall("business", query, n=3)
    if results:
        for r in results:
            st.info(r[:500])
    else:
        st.warning("Nothing found. Upload business docs and run the 'learn' task first.")
