"""
FastAPI backend for PDF → Excel extractor.
Streams real-time progress via Server-Sent Events (SSE).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

import asyncio
import json
import uuid
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="PDF Extractor API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("data/uploads");  UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR = Path("output");        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# In-memory job store
jobs: dict = {}


def sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def run_extraction(job_id: str, pdf_path: str,
                         start: int, end: int | None, delay: float):
    import fitz, openpyxl, time
    from agents.pdf_extractor_agent import (
        extract_page_data, write_page_to_sheet, create_summary_sheet
    )

    job = jobs[job_id]
    doc = fitz.open(pdf_path)
    total = len(doc)
    doc.close()

    pages = list(range(start, min(end or total, total)))
    job["total"]  = len(pages)
    job["status"] = "running"

    wb       = openpyxl.Workbook()
    wb.remove(wb.active)
    all_data = []

    for idx, page_num in enumerate(pages):
        job["current_page"] = page_num + 1
        job["log"].append({"page": page_num+1, "status": "processing", "title": "...", "tables": 0, "metrics": 0})

        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, extract_page_data, pdf_path, page_num)

        if data:
            all_data.append(data)
            await loop.run_in_executor(None, write_page_to_sheet, wb, page_num, data)
            job["log"][-1].update({
                "status":  "done",
                "title":   data.get("page_title", "—")[:55],
                "tables":  len(data.get("tables", [])),
                "metrics": len(data.get("key_metrics", [])),
            })
        else:
            all_data.append({"page_title": f"Page {page_num+1}", "page_type": "empty"})
            job["log"][-1].update({"status": "empty", "title": "No data extracted"})

        job["done_count"] = idx + 1
        job["progress"]   = round((idx + 1) / len(pages) * 100)

        if idx < len(pages) - 1:
            job["waiting"] = True
            await asyncio.sleep(delay)
            job["waiting"] = False

    await asyncio.get_event_loop().run_in_executor(None, create_summary_sheet, wb, all_data)

    stem     = Path(pdf_path).stem
    out_path = str(OUTPUT_DIR / f"{stem}_extracted.xlsx")
    wb.save(out_path)

    job["status"]      = "done"
    job["output_path"] = out_path
    job["progress"]    = 100
    job["total_tables"]  = sum(len(d.get("tables",[])) for d in all_data)
    job["total_metrics"] = sum(len(d.get("key_metrics",[])) for d in all_data)


@app.post("/extract")
async def start_extraction(
    file:       UploadFile = File(...),
    start_page: int   = Form(0),
    end_page:   int   = Form(0),
    delay:      float = Form(15.0),
):
    job_id   = str(uuid.uuid4())[:8]
    pdf_path = str(UPLOAD_DIR / f"{job_id}_{file.filename}")

    with open(pdf_path, "wb") as f:
        f.write(await file.read())

    jobs[job_id] = {
        "status": "queued", "progress": 0, "total": 0,
        "done_count": 0, "current_page": 0, "waiting": False,
        "log": [], "output_path": None,
        "total_tables": 0, "total_metrics": 0,
    }

    end = end_page if end_page > 0 else None
    asyncio.create_task(run_extraction(job_id, pdf_path, start_page, end, delay))
    return {"job_id": job_id}


@app.get("/progress/{job_id}")
async def progress_stream(job_id: str):
    async def event_stream() -> AsyncGenerator[str, None]:
        last_log_len = 0
        while True:
            job = jobs.get(job_id)
            if not job:
                yield sse("error", {"message": "Job not found"})
                break

            # Send new log entries
            new_entries = job["log"][last_log_len:]
            for entry in new_entries:
                yield sse("log", entry)
            last_log_len = len(job["log"])

            yield sse("progress", {
                "progress":    job["progress"],
                "done_count":  job["done_count"],
                "total":       job["total"],
                "current_page": job["current_page"],
                "status":      job["status"],
                "waiting":     job.get("waiting", False),
            })

            if job["status"] == "done":
                yield sse("complete", {
                    "job_id":        job_id,
                    "total_tables":  job["total_tables"],
                    "total_metrics": job["total_metrics"],
                    "pages":         job["total"],
                })
                break

            if job["status"] == "error":
                yield sse("error", {"message": job.get("error", "Unknown error")})
                break

            await asyncio.sleep(1)

    return StreamingResponse(event_stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.get("/download/{job_id}")
async def download(job_id: str):
    job = jobs.get(job_id)
    if not job or not job.get("output_path"):
        return {"error": "Not ready"}
    path = job["output_path"]
    return FileResponse(path, filename=Path(path).name,
                        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@app.get("/health")
async def health():
    return {"status": "ok"}
