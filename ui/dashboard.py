"""
Enterprise-grade Streamlit dashboard for the Autonomous Social Media Agent System.
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
    page_title=f"{CLIENT_NAME} · AI Agent",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Base ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: #0a0a0f;
    color: #e2e8f0;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0f0f1a !important;
    border-right: 1px solid #1e1e2e;
}
[data-testid="stSidebar"] * { color: #cbd5e1 !important; }

/* ── Hide default header ── */
#MainMenu, footer, header { visibility: hidden; }

/* ── Metric cards ── */
[data-testid="metric-container"] {
    background: #111827;
    border: 1px solid #1e293b;
    border-radius: 12px;
    padding: 20px !important;
    transition: border-color 0.2s;
}
[data-testid="metric-container"]:hover { border-color: #6366f1; }
[data-testid="stMetricValue"] { color: #f1f5f9 !important; font-size: 2rem !important; font-weight: 700 !important; }
[data-testid="stMetricLabel"] { color: #64748b !important; font-size: 0.75rem !important; text-transform: uppercase; letter-spacing: 0.1em; }

/* ── Tabs ── */
[data-testid="stTabs"] button {
    color: #64748b !important;
    font-weight: 500;
    font-size: 0.875rem;
    border-bottom: 2px solid transparent !important;
    padding: 10px 20px !important;
}
[data-testid="stTabs"] button[aria-selected="true"] {
    color: #6366f1 !important;
    border-bottom: 2px solid #6366f1 !important;
    background: transparent !important;
}

/* ── Buttons ── */
.stButton > button {
    background: #6366f1 !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    padding: 10px 20px !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: #4f46e5 !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 20px rgba(99,102,241,0.4) !important;
}
.stButton > button[kind="secondary"] {
    background: #1e293b !important;
    color: #94a3b8 !important;
}
.stButton > button[kind="secondary"]:hover {
    background: #334155 !important;
    color: #f1f5f9 !important;
}

/* ── Inputs ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
    background: #111827 !important;
    border: 1px solid #1e293b !important;
    border-radius: 8px !important;
    color: #f1f5f9 !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.15) !important;
}

/* ── Expander ── */
[data-testid="stExpander"] {
    background: #111827 !important;
    border: 1px solid #1e293b !important;
    border-radius: 10px !important;
}

/* ── Divider ── */
hr { border-color: #1e293b !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0a0a0f; }
::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #334155; }
</style>
""", unsafe_allow_html=True)


# ── Custom components ──────────────────────────────────────────────────────

def badge(text: str, color: str = "#6366f1") -> str:
    return f'<span style="background:{color}22;color:{color};border:1px solid {color}44;padding:2px 10px;border-radius:20px;font-size:0.75rem;font-weight:600;">{text}</span>'


def card(content: str, border_color: str = "#1e293b"):
    st.markdown(f"""
    <div style="background:#111827;border:1px solid {border_color};border-radius:12px;padding:20px;margin-bottom:12px;">
        {content}
    </div>""", unsafe_allow_html=True)


def stat_row(items: list):
    """items = list of (label, value, color) tuples"""
    cols = st.columns(len(items))
    for col, (label, value, color) in zip(cols, items):
        with col:
            st.markdown(f"""
            <div style="background:#111827;border:1px solid #1e293b;border-radius:12px;padding:20px;text-align:center;">
                <div style="font-size:2rem;font-weight:700;color:{color};">{value}</div>
                <div style="font-size:0.7rem;color:#64748b;text-transform:uppercase;letter-spacing:0.1em;margin-top:4px;">{label}</div>
            </div>""", unsafe_allow_html=True)


def section_header(title: str, subtitle: str = ""):
    st.markdown(f"""
    <div style="margin:24px 0 16px 0;">
        <div style="font-size:1rem;font-weight:600;color:#f1f5f9;">{title}</div>
        {"<div style='font-size:0.8rem;color:#64748b;margin-top:2px;'>" + subtitle + "</div>" if subtitle else ""}
    </div>""", unsafe_allow_html=True)


# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="padding:16px 0 24px 0;">
        <div style="font-size:1.25rem;font-weight:700;color:#f1f5f9;">⚡ {CLIENT_NAME}</div>
        <div style="font-size:0.75rem;color:#64748b;margin-top:4px;">{CLIENT_INDUSTRY} · {CLIENT_TONE.title()}</div>
    </div>""", unsafe_allow_html=True)

    mode_color = "#f59e0b" if DRAFT_MODE else "#10b981"
    mode_text  = "Draft Mode" if DRAFT_MODE else "Auto-publish"
    st.markdown(f"""
    <div style="background:#111827;border:1px solid #1e293b;border-radius:8px;padding:10px 14px;margin-bottom:20px;display:flex;align-items:center;gap:8px;">
        <div style="width:8px;height:8px;border-radius:50%;background:{mode_color};box-shadow:0 0 6px {mode_color};"></div>
        <span style="font-size:0.8rem;color:#94a3b8;">{mode_text}</span>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div style="font-size:0.7rem;color:#475569;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:8px;">Run Agent Task</div>', unsafe_allow_html=True)

    task     = st.selectbox("Task", ["content", "learn", "leads", "followups", "engage"], label_visibility="collapsed")
    platform = st.selectbox("Platform", ["linkedin", "instagram", "facebook", "telegram", "all"], label_visibility="collapsed")
    topic    = st.text_input("Topic", placeholder="e.g. AI trends for startups", label_visibility="collapsed")

    if st.button("▶  Run Task", use_container_width=True):
        with st.spinner(f"Running {task}..."):
            try:
                from agents.orchestrator import build_orchestrator
                orch = build_orchestrator()
                task_map = {
                    "content":   f"run_content_creation for platform: {platform}" + (f", topic: {topic}" if topic else ""),
                    "leads":     "run_lead_generation" + (f" focus: {topic}" if topic else ""),
                    "followups": "run_followups",
                    "learn":     "run_learning",
                    "engage":    f"run_engagement — context: {topic or 'check all platforms'}",
                }
                result = orch(task_map[task])
                st.session_state["last_result"] = str(result)
                st.success("Done!")
                st.rerun()
            except Exception as e:
                st.error(str(e))

    st.markdown('<hr style="margin:20px 0;">', unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.7rem;color:#475569;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:8px;">Business Data</div>', unsafe_allow_html=True)

    uploaded = st.file_uploader("Upload PDF / TXT / MD", type=["pdf", "txt", "md"])
    if uploaded and st.button("Ingest File", use_container_width=True):
        os.makedirs("data/business", exist_ok=True)
        with open(f"data/business/{uploaded.name}", "wb") as f:
            f.write(uploaded.getbuffer())
        st.success("Saved — run 'learn' to ingest.")

    st.markdown('<hr style="margin:20px 0;">', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:0.7rem;color:#334155;text-align:center;">{datetime.now().strftime("%d %b %Y · %H:%M")}</div>', unsafe_allow_html=True)


# ── Top header ─────────────────────────────────────────────────────────────
pending_count = len(get_drafts("pending"))

st.markdown(f"""
<div style="display:flex;align-items:center;justify-content:space-between;padding:8px 0 24px 0;border-bottom:1px solid #1e293b;margin-bottom:28px;">
    <div>
        <div style="font-size:1.5rem;font-weight:700;color:#f1f5f9;">Agent Dashboard</div>
        <div style="font-size:0.8rem;color:#475569;margin-top:2px;">Autonomous Social Media System · Powered by Groq + Strands</div>
    </div>
    <div style="display:flex;gap:10px;align-items:center;">
        {badge(f"⏳ {pending_count} pending", "#f59e0b") if pending_count else badge("✓ All clear", "#10b981")}
        {badge("● Live", "#10b981")}
    </div>
</div>
""", unsafe_allow_html=True)


# ── Metrics ────────────────────────────────────────────────────────────────
def count(col): 
    try: return len(memory.recall_all(col))
    except: return 0

stat_row([
    ("Posts Published",   count("posts"),       "#6366f1"),
    ("Leads Tracked",     count("leads"),        "#06b6d4"),
    ("Pending Drafts",    pending_count,          "#f59e0b"),
    ("Engagements",       count("engagement"),   "#10b981"),
    ("Follow-ups Sent",   count("followups"),    "#f43f5e"),
])

st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)


# ── Tabs ───────────────────────────────────────────────────────────────────
tab_drafts, tab_leads, tab_posts, tab_engage, tab_knowledge = st.tabs([
    "✋  Drafts Queue",
    "👥  Leads",
    "📝  Posts",
    "💬  Engagement",
    "📚  Knowledge Base",
])


# ── Tab 1: Drafts ──────────────────────────────────────────────────────────
with tab_drafts:
    pending  = get_drafts("pending")
    approved = get_drafts("approved")
    rejected = get_drafts("rejected")

    stat_row([
        ("Awaiting Review", len(pending),  "#f59e0b"),
        ("Approved",        len(approved), "#10b981"),
        ("Rejected",        len(rejected), "#f43f5e"),
    ])

    st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)

    if not pending:
        st.markdown("""
        <div style="background:#111827;border:1px dashed #1e293b;border-radius:12px;padding:48px;text-align:center;">
            <div style="font-size:2rem;margin-bottom:12px;">✓</div>
            <div style="color:#64748b;font-size:0.9rem;">No drafts pending. Run the <strong style="color:#6366f1;">content</strong> task to generate posts.</div>
        </div>""", unsafe_allow_html=True)
    else:
        section_header(f"{len(pending)} Post{'s' if len(pending)>1 else ''} Awaiting Approval")
        for draft in pending:
            platform_colors = {"linkedin":"#0077b5","instagram":"#e1306c","facebook":"#1877f2","telegram":"#229ed9","all":"#6366f1"}
            pc = platform_colors.get(draft["platform"], "#6366f1")

            with st.container():
                st.markdown(f"""
                <div style="background:#111827;border:1px solid #1e293b;border-radius:12px;padding:20px;margin-bottom:16px;border-left:3px solid {pc};">
                    <div style="display:flex;align-items:center;gap:10px;margin-bottom:14px;">
                        {badge(draft['platform'].upper(), pc)}
                        {badge('⏳ Pending', '#f59e0b')}
                        <span style="font-size:0.75rem;color:#475569;margin-left:auto;">{draft['created_at'][:16]}</span>
                    </div>
                    {"<div style='font-size:0.75rem;color:#64748b;margin-bottom:8px;'>Topic: " + draft.get('topic','—') + "</div>" if draft.get('topic') else ""}
                </div>""", unsafe_allow_html=True)

                edited = st.text_area("Content", draft["content"], height=160, key=f"txt_{draft['id']}", label_visibility="collapsed")

                c1, c2, c3, _ = st.columns([2, 2, 1, 3])
                with c1:
                    if st.button("✅  Approve & Publish", key=f"app_{draft['id']}", use_container_width=True):
                        try:
                            p = draft["platform"]
                            if p == "linkedin":
                                from tools.social_tools import linkedin_post; linkedin_post(edited)
                            elif p == "facebook":
                                from tools.social_tools import facebook_post; facebook_post(edited)
                            elif p == "telegram":
                                from tools.social_tools import telegram_post; telegram_post(edited)
                            elif p == "instagram":
                                st.warning("Instagram requires an image — post manually.")
                            update_status(draft["id"], "approved")
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))
                with c2:
                    if st.button("✏️  Save Edits", key=f"edit_{draft['id']}", use_container_width=True):
                        from core.drafts import _load, _save
                        drafts = _load()
                        for d in drafts:
                            if d["id"] == draft["id"]:
                                d["content"] = edited
                        _save(drafts)
                        st.success("Saved!")
                with c3:
                    if st.button("✕", key=f"rej_{draft['id']}", use_container_width=True):
                        update_status(draft["id"], "rejected")
                        st.rerun()

    if approved or rejected:
        st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)
        with st.expander("📋  History (approved & rejected)"):
            for d in (approved + rejected)[-20:][::-1]:
                color = "#10b981" if d["status"] == "approved" else "#f43f5e"
                icon  = "✅" if d["status"] == "approved" else "❌"
                st.markdown(f"""
                <div style="display:flex;gap:12px;align-items:flex-start;padding:10px 0;border-bottom:1px solid #1e293b;">
                    <span>{icon}</span>
                    <div>
                        <div style="font-size:0.75rem;color:#64748b;">{d['platform'].upper()} · {d.get('reviewed_at','')[:16]}</div>
                        <div style="font-size:0.85rem;color:#cbd5e1;margin-top:2px;">{d['content'][:120]}...</div>
                    </div>
                </div>""", unsafe_allow_html=True)


# ── Tab 2: Leads ───────────────────────────────────────────────────────────
with tab_leads:
    leads = memory.recall_all("leads")
    section_header(f"{len(leads)} Leads Tracked", "LinkedIn prospects and nurture pipeline")

    stage_colors = {"contacted":"#6366f1","connected":"#06b6d4","replied":"#f59e0b","qualified":"#10b981","booked":"#f43f5e"}

    if not leads:
        st.markdown("""
        <div style="background:#111827;border:1px dashed #1e293b;border-radius:12px;padding:48px;text-align:center;">
            <div style="color:#64748b;">No leads yet. Run the <strong style="color:#6366f1;">leads</strong> task to start prospecting.</div>
        </div>""", unsafe_allow_html=True)
    else:
        for lead in leads[::-1]:
            stage = next((s for s in stage_colors if s in lead.lower()), "contacted")
            sc = stage_colors[stage]
            st.markdown(f"""
            <div style="background:#111827;border:1px solid #1e293b;border-radius:10px;padding:14px 18px;margin-bottom:8px;display:flex;align-items:center;gap:12px;">
                <div style="width:36px;height:36px;border-radius:50%;background:#1e293b;display:flex;align-items:center;justify-content:center;font-size:1rem;">👤</div>
                <div style="flex:1;font-size:0.85rem;color:#cbd5e1;">{lead[:180]}</div>
                {badge(stage.title(), sc)}
            </div>""", unsafe_allow_html=True)


# ── Tab 3: Posts ───────────────────────────────────────────────────────────
with tab_posts:
    posts = memory.recall_all("posts")
    section_header(f"{len(posts)} Posts Published")

    if not posts:
        st.markdown("""
        <div style="background:#111827;border:1px dashed #1e293b;border-radius:12px;padding:48px;text-align:center;">
            <div style="color:#64748b;">No posts yet. Run the <strong style="color:#6366f1;">content</strong> task.</div>
        </div>""", unsafe_allow_html=True)
    else:
        for i, post in enumerate(posts[::-1]):
            with st.expander(f"📝  {post[:90]}..."):
                st.markdown(f'<div style="color:#cbd5e1;font-size:0.9rem;line-height:1.6;">{post}</div>', unsafe_allow_html=True)


# ── Tab 4: Engagement ──────────────────────────────────────────────────────
with tab_engage:
    col_l, col_r = st.columns(2)

    with col_l:
        section_header("💬 Engagements", "Comments, replies, DMs")
        engagements = memory.recall_all("engagement")
        if not engagements:
            st.markdown('<div style="color:#475569;font-size:0.85rem;padding:20px 0;">No engagements logged yet.</div>', unsafe_allow_html=True)
        else:
            for e in engagements[::-1][:15]:
                st.markdown(f"""
                <div style="background:#111827;border:1px solid #1e293b;border-radius:8px;padding:12px 16px;margin-bottom:8px;font-size:0.83rem;color:#94a3b8;line-height:1.5;">
                    💬 {e[:160]}
                </div>""", unsafe_allow_html=True)

    with col_r:
        section_header("📧 Follow-ups", "Email sequences & bookings")
        followups = memory.recall_all("followups")
        if not followups:
            st.markdown('<div style="color:#475569;font-size:0.85rem;padding:20px 0;">No follow-ups yet.</div>', unsafe_allow_html=True)
        else:
            for f in followups[::-1][:15]:
                st.markdown(f"""
                <div style="background:#111827;border:1px solid #1e293b;border-radius:8px;padding:12px 16px;margin-bottom:8px;font-size:0.83rem;color:#94a3b8;line-height:1.5;">
                    📧 {f[:160]}
                </div>""", unsafe_allow_html=True)


# ── Tab 5: Knowledge Base ──────────────────────────────────────────────────
with tab_knowledge:
    section_header("Business Knowledge Base", "Semantic search across all ingested documents")

    query = st.text_input("Search", placeholder="🔍  Search — e.g. target audience, product features, tone of voice", label_visibility="collapsed")
    if query:
        results = memory.recall("business", query, n=5)
        if results:
            for r in results:
                st.markdown(f"""
                <div style="background:#111827;border:1px solid #6366f133;border-left:3px solid #6366f1;border-radius:10px;padding:16px 20px;margin-bottom:10px;font-size:0.85rem;color:#cbd5e1;line-height:1.6;">
                    {r[:600]}
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:#475569;padding:20px 0;">Nothing found. Upload docs and run the <strong style="color:#6366f1;">learn</strong> task first.</div>', unsafe_allow_html=True)

    st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)
    all_docs = memory.recall_all("business")
    section_header(f"All Documents ({len(all_docs)})")
    if all_docs:
        for doc in all_docs:
            with st.expander(doc[:80] + "..."):
                st.markdown(f'<div style="color:#94a3b8;font-size:0.85rem;line-height:1.6;">{doc}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="color:#475569;font-size:0.85rem;">No documents ingested yet.</div>', unsafe_allow_html=True)


# ── Last agent output ──────────────────────────────────────────────────────
if "last_result" in st.session_state:
    st.markdown("<div style='margin-top:32px;'></div>", unsafe_allow_html=True)
    with st.expander("🧠  Last Agent Output"):
        st.markdown(f"""
        <div style="background:#0f172a;border:1px solid #1e293b;border-radius:10px;padding:20px;font-family:monospace;font-size:0.8rem;color:#94a3b8;white-space:pre-wrap;line-height:1.6;">
{st.session_state['last_result'][:3000]}
        </div>""", unsafe_allow_html=True)
