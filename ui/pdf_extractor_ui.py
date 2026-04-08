"""
PDF → Excel Extractor UI
Run with: streamlit run ui/pdf_extractor_ui.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import threading
import time
import json
from pathlib import Path
from datetime import datetime

st.set_page_config(
    page_title="PDF → Excel · AI Extractor",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: #0a0a0f; color: #e2e8f0; }
#MainMenu, footer, header { visibility: hidden; }

/* Upload zone */
[data-testid="stFileUploader"] {
    background: #111827;
    border: 2px dashed #1e293b;
    border-radius: 16px;
    padding: 12px;
    transition: border-color 0.3s;
}
[data-testid="stFileUploader"]:hover { border-color: #6366f1; }

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #6366f1, #4f46e5) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    padding: 12px 28px !important;
    transition: all 0.2s !important;
    width: 100%;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 30px rgba(99,102,241,0.5) !important;
}
.stButton > button:disabled {
    background: #1e293b !important;
    color: #475569 !important;
    transform: none !important;
}

/* Download button */
[data-testid="stDownloadButton"] > button {
    background: linear-gradient(135deg, #10b981, #059669) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    padding: 12px 28px !important;
    width: 100%;
    transition: all 0.2s !important;
}
[data-testid="stDownloadButton"] > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 30px rgba(16,185,129,0.5) !important;
}

/* Progress bar */
.stProgress > div > div { background: #6366f1 !important; border-radius: 4px; }
.stProgress > div { background: #1e293b !important; border-radius: 4px; }

/* Expander */
[data-testid="stExpander"] {
    background: #111827 !important;
    border: 1px solid #1e293b !important;
    border-radius: 10px !important;
}

/* Selectbox / number input */
.stSelectbox > div > div, .stNumberInput > div > div > input {
    background: #111827 !important;
    border: 1px solid #1e293b !important;
    border-radius: 8px !important;
    color: #f1f5f9 !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: #0a0a0f; }
::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 3px; }

/* Metric */
[data-testid="metric-container"] {
    background: #111827;
    border: 1px solid #1e293b;
    border-radius: 12px;
    padding: 16px !important;
}
[data-testid="stMetricValue"] { color: #f1f5f9 !important; font-weight: 700 !important; }
[data-testid="stMetricLabel"] { color: #64748b !important; font-size: 0.72rem !important; text-transform: uppercase; letter-spacing: 0.08em; }
</style>
""", unsafe_allow_html=True)


# ── State ──────────────────────────────────────────────────────────────────
if "log"          not in st.session_state: st.session_state.log          = []
if "progress"     not in st.session_state: st.session_state.progress     = 0
if "total_pages"  not in st.session_state: st.session_state.total_pages  = 0
if "running"      not in st.session_state: st.session_state.running      = False
if "done"         not in st.session_state: st.session_state.done         = False
if "output_path"  not in st.session_state: st.session_state.output_path  = None
if "page_results" not in st.session_state: st.session_state.page_results = []
if "error"        not in st.session_state: st.session_state.error        = None


# ── Header ─────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;padding:48px 0 32px 0;">
    <div style="display:inline-flex;align-items:center;gap:12px;margin-bottom:16px;">
        <div style="width:48px;height:48px;background:linear-gradient(135deg,#6366f1,#06b6d4);
                    border-radius:12px;display:flex;align-items:center;justify-content:center;
                    font-size:1.5rem;">⚡</div>
        <div style="text-align:left;">
            <div style="font-size:1.6rem;font-weight:700;color:#f1f5f9;">PDF → Excel Extractor</div>
            <div style="font-size:0.8rem;color:#64748b;">AI-powered · Vision model · Structured output</div>
        </div>
    </div>
    <div style="font-size:0.9rem;color:#475569;max-width:520px;margin:0 auto;line-height:1.6;">
        Upload any PDF — scanned or digital. The AI reads every page, extracts all tables,
        metrics and data, then writes a clean formatted Excel file for download.
    </div>
</div>
""", unsafe_allow_html=True)


# ── Upload + config ────────────────────────────────────────────────────────
col_upload, col_config = st.columns([3, 2], gap="large")

with col_upload:
    st.markdown('<div style="font-size:0.75rem;color:#64748b;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:8px;">Upload PDF</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("PDF file", type=["pdf"], label_visibility="collapsed")

    if uploaded_file:
        st.markdown(f"""
        <div style="background:#111827;border:1px solid #1e293b;border-radius:10px;
                    padding:14px 18px;margin-top:12px;display:flex;align-items:center;gap:12px;">
            <div style="font-size:1.5rem;">📄</div>
            <div>
                <div style="font-size:0.9rem;font-weight:600;color:#f1f5f9;">{uploaded_file.name}</div>
                <div style="font-size:0.75rem;color:#64748b;margin-top:2px;">{uploaded_file.size/1024:.1f} KB</div>
            </div>
            <div style="margin-left:auto;">
                <span style="background:#10b98122;color:#10b981;border:1px solid #10b98144;
                             padding:3px 10px;border-radius:20px;font-size:0.72rem;font-weight:600;">Ready</span>
            </div>
        </div>""", unsafe_allow_html=True)

with col_config:
    st.markdown('<div style="font-size:0.75rem;color:#64748b;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:8px;">Options</div>', unsafe_allow_html=True)
    st.markdown('<div style="background:#111827;border:1px solid #1e293b;border-radius:12px;padding:20px;">', unsafe_allow_html=True)

    page_range = st.selectbox("Page range", ["All pages", "Custom range"], label_visibility="visible")
    start_page, end_page = 0, None

    if page_range == "Custom range":
        c1, c2 = st.columns(2)
        with c1:
            start_page = st.number_input("From page", min_value=1, value=1, step=1) - 1
        with c2:
            end_page = st.number_input("To page", min_value=1, value=10, step=1)

    delay = st.selectbox("Speed (rate limit)", ["Safe (15s)", "Fast (8s)", "Turbo (4s)"])
    delay_map = {"Safe (15s)": 15, "Fast (8s)": 8, "Turbo (4s)": 4}
    sleep_time = delay_map[delay]

    st.markdown('</div>', unsafe_allow_html=True)


# ── Run button ─────────────────────────────────────────────────────────────
st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)
_, btn_col, _ = st.columns([2, 3, 2])

with btn_col:
    can_run = uploaded_file is not None and not st.session_state.running
    if st.button("⚡  Extract & Generate Excel", disabled=not can_run):
        # Save uploaded PDF
        os.makedirs("data/uploads", exist_ok=True)
        pdf_path = f"data/uploads/{uploaded_file.name}"
        with open(pdf_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Reset state
        st.session_state.log          = []
        st.session_state.progress     = 0
        st.session_state.done         = False
        st.session_state.output_path  = None
        st.session_state.page_results = []
        st.session_state.error        = None
        st.session_state.running      = True

        # Count pages
        import fitz
        doc = fitz.open(pdf_path)
        total = len(doc)
        doc.close()
        ep = end_page or total
        pages = list(range(start_page, min(ep, total)))
        st.session_state.total_pages = len(pages)

        # Run extraction in background thread
        def run_extraction():
            try:
                from agents.pdf_extractor_agent import (
                    extract_page_data, write_page_to_sheet,
                    create_summary_sheet, get_page_count
                )
                import openpyxl

                wb = openpyxl.Workbook()
                wb.remove(wb.active)
                all_data = []

                for idx, page_num in enumerate(pages):
                    st.session_state.log.append({
                        "page": page_num + 1,
                        "status": "processing",
                        "title": "...",
                        "tables": 0,
                        "metrics": 0,
                    })

                    data = extract_page_data(pdf_path, page_num)

                    if data:
                        all_data.append(data)
                        write_page_to_sheet(wb, page_num, data)
                        st.session_state.log[-1].update({
                            "status":  "done",
                            "title":   data.get("page_title", "—")[:50],
                            "tables":  len(data.get("tables", [])),
                            "metrics": len(data.get("key_metrics", [])),
                        })
                    else:
                        all_data.append({"page_title": f"Page {page_num+1}", "page_type": "empty"})
                        st.session_state.log[-1].update({"status": "empty", "title": "No data"})

                    st.session_state.progress = (idx + 1) / len(pages)

                    if idx < len(pages) - 1:
                        time.sleep(sleep_time)

                create_summary_sheet(wb, all_data)

                out_dir = Path("output")
                out_dir.mkdir(exist_ok=True)
                stem = Path(pdf_path).stem
                out_path = str(out_dir / f"{stem}_extracted.xlsx")
                wb.save(out_path)

                st.session_state.output_path = out_path
                st.session_state.page_results = all_data
                st.session_state.done = True
                st.session_state.running = False

            except Exception as e:
                st.session_state.error = str(e)
                st.session_state.running = False

        t = threading.Thread(target=run_extraction, daemon=True)
        t.start()
        st.rerun()


# ── Progress UI ────────────────────────────────────────────────────────────
if st.session_state.running or st.session_state.done:
    st.markdown("<div style='margin-top:32px;'></div>", unsafe_allow_html=True)
    st.markdown('<div style="background:#111827;border:1px solid #1e293b;border-radius:16px;padding:28px;">', unsafe_allow_html=True)

    progress = st.session_state.progress
    total    = st.session_state.total_pages
    done_count = int(progress * total)

    # Status header
    if st.session_state.running:
        status_color, status_text, status_icon = "#f59e0b", "Processing...", "⚙️"
    elif st.session_state.done:
        status_color, status_text, status_icon = "#10b981", "Complete", "✅"
    else:
        status_color, status_text, status_icon = "#f43f5e", "Error", "❌"

    st.markdown(f"""
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px;">
        <div style="display:flex;align-items:center;gap:10px;">
            <div style="width:10px;height:10px;border-radius:50%;background:{status_color};
                        box-shadow:0 0 8px {status_color};
                        {'animation:pulse 1.5s infinite;' if st.session_state.running else ''}"></div>
            <span style="font-size:1rem;font-weight:600;color:#f1f5f9;">{status_icon} {status_text}</span>
        </div>
        <span style="font-size:0.85rem;color:#64748b;">{done_count} / {total} pages</span>
    </div>""", unsafe_allow_html=True)

    st.progress(progress)

    # Metrics row
    if st.session_state.page_results:
        total_tables  = sum(len(d.get("tables",[])) for d in st.session_state.page_results)
        total_metrics = sum(len(d.get("key_metrics",[])) for d in st.session_state.page_results)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Pages Done",    done_count)
        c2.metric("Tables Found",  total_tables)
        c3.metric("Metrics Found", total_metrics)
        c4.metric("Progress",      f"{int(progress*100)}%")

    # Live log
    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
    log_html = '<div style="background:#0a0a0f;border:1px solid #1e293b;border-radius:10px;padding:16px;max-height:280px;overflow-y:auto;font-family:monospace;">'

    for entry in st.session_state.log[::-1]:
        if entry["status"] == "done":
            icon, color = "✓", "#10b981"
            detail = f"{entry['tables']} tables · {entry['metrics']} metrics"
        elif entry["status"] == "processing":
            icon, color = "⟳", "#f59e0b"
            detail = "extracting..."
        else:
            icon, color = "⚠", "#f43f5e"
            detail = "no data"

        log_html += f"""
        <div style="display:flex;gap:12px;align-items:flex-start;padding:5px 0;border-bottom:1px solid #1e293b11;">
            <span style="color:{color};font-size:0.8rem;min-width:16px;">{icon}</span>
            <span style="color:#64748b;font-size:0.78rem;min-width:60px;">Page {entry['page']}</span>
            <span style="color:#94a3b8;font-size:0.78rem;flex:1;">{entry['title'][:55]}</span>
            <span style="color:#475569;font-size:0.75rem;">{detail}</span>
        </div>"""

    log_html += "</div>"
    st.markdown(log_html, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Auto-refresh while running
    if st.session_state.running:
        time.sleep(2)
        st.rerun()


# ── Error ──────────────────────────────────────────────────────────────────
if st.session_state.error:
    st.markdown(f"""
    <div style="background:#f43f5e11;border:1px solid #f43f5e44;border-radius:10px;
                padding:16px 20px;margin-top:20px;color:#f43f5e;font-size:0.85rem;">
        ❌ Error: {st.session_state.error}
    </div>""", unsafe_allow_html=True)


# ── Download ───────────────────────────────────────────────────────────────
if st.session_state.done and st.session_state.output_path:
    out_path = st.session_state.output_path
    st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)

    # Summary card
    results = st.session_state.page_results
    total_tables  = sum(len(d.get("tables",[])) for d in results)
    total_metrics = sum(len(d.get("key_metrics",[])) for d in results)
    file_size     = os.path.getsize(out_path) / 1024

    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#10b98111,#06b6d411);
                border:1px solid #10b98133;border-radius:16px;padding:28px;text-align:center;">
        <div style="font-size:2rem;margin-bottom:8px;">🎉</div>
        <div style="font-size:1.2rem;font-weight:700;color:#10b981;margin-bottom:6px;">Extraction Complete!</div>
        <div style="font-size:0.85rem;color:#64748b;margin-bottom:20px;">
            {len(results)} pages · {total_tables} tables · {total_metrics} metrics · {file_size:.1f} KB
        </div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
    _, dl_col, _ = st.columns([2, 3, 2])
    with dl_col:
        with open(out_path, "rb") as f:
            st.download_button(
                label="⬇  Download Excel File",
                data=f.read(),
                file_name=Path(out_path).name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    # Preview extracted data
    st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.75rem;color:#64748b;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:12px;">Extracted Data Preview</div>', unsafe_allow_html=True)

    for i, data in enumerate(results):
        if not data.get("tables") and not data.get("key_metrics"):
            continue
        with st.expander(f"📄  Page {i+1} — {data.get('page_title','—')[:60]}"):
            for tbl in data.get("tables", []):
                if not tbl.get("headers"):
                    continue
                st.markdown(f'<div style="font-size:0.8rem;color:#6366f1;font-weight:600;margin-bottom:6px;">📊 {tbl.get("table_title","Table")}</div>', unsafe_allow_html=True)
                import pandas as pd
                try:
                    df = pd.DataFrame(tbl.get("rows", []), columns=tbl.get("headers", []))
                    st.dataframe(df, use_container_width=True, hide_index=True)
                except:
                    st.json(tbl)

            for m in data.get("key_metrics", []):
                st.markdown(f'<span style="background:#6366f122;color:#6366f1;border:1px solid #6366f144;padding:3px 10px;border-radius:20px;font-size:0.78rem;margin-right:6px;">{m.get("metric","")}: <strong>{m.get("value","")}</strong></span>', unsafe_allow_html=True)


# ── How it works ───────────────────────────────────────────────────────────
if not st.session_state.running and not st.session_state.done:
    st.markdown("<div style='margin-top:48px;'></div>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    for col, icon, title, desc in [
        (c1, "📤", "Upload",   "Drop any PDF — scanned or digital, any size"),
        (c2, "🧠", "AI Reads", "Vision model reads each page like a human analyst"),
        (c3, "📊", "Extracts", "Tables, metrics, text — all structured precisely"),
        (c4, "⬇",  "Download", "Clean formatted Excel with one sheet per page"),
    ]:
        with col:
            st.markdown(f"""
            <div style="background:#111827;border:1px solid #1e293b;border-radius:12px;
                        padding:20px;text-align:center;">
                <div style="font-size:1.8rem;margin-bottom:10px;">{icon}</div>
                <div style="font-size:0.9rem;font-weight:600;color:#f1f5f9;margin-bottom:6px;">{title}</div>
                <div style="font-size:0.78rem;color:#64748b;line-height:1.5;">{desc}</div>
            </div>""", unsafe_allow_html=True)
