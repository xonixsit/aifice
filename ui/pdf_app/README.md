# PDF Extractor App

## Start

**Terminal 1 — Backend:**
```bash
cd social-agent-system
python -m uvicorn ui.pdf_app.backend.main:app --reload --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd social-agent-system/ui/pdf_app/frontend
npm run dev
```

Open: http://localhost:5173
