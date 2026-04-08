import { useState, useRef, useCallback } from 'react'
import {
  Upload, FileText, Zap, CheckCircle2, XCircle,
  Download, ChevronDown, ChevronUp, Table2,
  BarChart3, Loader2, AlertCircle, Sparkles
} from 'lucide-react'

// ── Types ──────────────────────────────────────────────────────────────────
type Speed = 'safe' | 'fast' | 'turbo'
type Status = 'idle' | 'running' | 'done' | 'error'

interface LogEntry {
  page: number
  status: 'processing' | 'done' | 'empty'
  title: string
  tables: number
  metrics: number
}

interface ProgressData {
  progress: number
  done_count: number
  total: number
  current_page: number
  status: string
  waiting: boolean
}

interface CompleteData {
  job_id: string
  total_tables: number
  total_metrics: number
  pages: number
}

// ── Helpers ────────────────────────────────────────────────────────────────
const SPEED_MAP: Record<Speed, { label: string; delay: number; color: string }> = {
  safe:  { label: 'Safe · 15s',  delay: 15, color: 'text-green-400' },
  fast:  { label: 'Fast · 8s',   delay: 8,  color: 'text-amber-400' },
  turbo: { label: 'Turbo · 4s',  delay: 4,  color: 'text-red-400'   },
}

function cn(...classes: (string | false | undefined)[]) {
  return classes.filter(Boolean).join(' ')
}

// ── Sub-components ─────────────────────────────────────────────────────────

function Badge({ children, color = 'indigo' }: { children: React.ReactNode; color?: string }) {
  const map: Record<string, string> = {
    indigo: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20',
    green:  'bg-green-500/10  text-green-400  border-green-500/20',
    amber:  'bg-amber-500/10  text-amber-400  border-amber-500/20',
    red:    'bg-red-500/10    text-red-400    border-red-500/20',
    cyan:   'bg-cyan-500/10   text-cyan-400   border-cyan-500/20',
  }
  return (
    <span className={cn('inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border', map[color] ?? map.indigo)}>
      {children}
    </span>
  )
}

function StatCard({ label, value, color }: { label: string; value: string | number; color: string }) {
  return (
    <div className="bg-[#111827] border border-[#1e293b] rounded-xl p-4 text-center">
      <div className={cn('text-2xl font-bold', color)}>{value}</div>
      <div className="text-xs text-slate-500 uppercase tracking-widest mt-1">{label}</div>
    </div>
  )
}

function LogRow({ entry, index }: { entry: LogEntry; index: number }) {
  const isProcessing = entry.status === 'processing'
  const isDone       = entry.status === 'done'

  return (
    <div className={cn(
      'flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-all slide-up',
      isDone       ? 'bg-green-500/5'  : '',
      isProcessing ? 'bg-amber-500/5'  : '',
    )} style={{ animationDelay: `${index * 30}ms` }}>
      <div className="w-5 flex-shrink-0">
        {isProcessing && <Loader2 size={14} className="text-amber-400 animate-spin" />}
        {isDone       && <CheckCircle2 size={14} className="text-green-400" />}
        {entry.status === 'empty' && <AlertCircle size={14} className="text-slate-500" />}
      </div>
      <span className="text-slate-500 text-xs w-14 flex-shrink-0">Page {entry.page}</span>
      <span className="text-slate-300 flex-1 truncate">{entry.title}</span>
      {isDone && (
        <div className="flex gap-2 flex-shrink-0">
          {entry.tables > 0  && <Badge color="indigo">{entry.tables} tables</Badge>}
          {entry.metrics > 0 && <Badge color="cyan">{entry.metrics} metrics</Badge>}
        </div>
      )}
    </div>
  )
}

// ── Main App ───────────────────────────────────────────────────────────────
export default function App() {
  const [file,       setFile]       = useState<File | null>(null)
  const [dragging,   setDragging]   = useState(false)
  const [speed,      setSpeed]      = useState<Speed>('safe')
  const [pageMode,   setPageMode]   = useState<'all' | 'custom'>('all')
  const [startPage,  setStartPage]  = useState(1)
  const [endPage,    setEndPage]    = useState(10)
  const [status,     setStatus]     = useState<Status>('idle')
  const [progress,   setProgress]   = useState(0)
  const [progData,   setProgData]   = useState<ProgressData | null>(null)
  const [complete,   setComplete]   = useState<CompleteData | null>(null)
  const [log,        setLog]        = useState<LogEntry[]>([])
  const [jobId,      setJobId]      = useState<string | null>(null)
  const [error,      setError]      = useState<string | null>(null)
  const [logOpen,    setLogOpen]    = useState(true)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // ── Drop zone ────────────────────────────────────────────────────────────
  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault(); setDragging(false)
    const f = e.dataTransfer.files[0]
    if (f?.type === 'application/pdf') setFile(f)
  }, [])

  // ── Start extraction ─────────────────────────────────────────────────────
  const startExtraction = async () => {
    if (!file) return
    setStatus('running'); setLog([]); setProgress(0)
    setProgData(null); setComplete(null); setError(null)

    const form = new FormData()
    form.append('file', file)
    form.append('start_page', pageMode === 'custom' ? String(startPage - 1) : '0')
    form.append('end_page',   pageMode === 'custom' ? String(endPage) : '0')
    form.append('delay',      String(SPEED_MAP[speed].delay))

    const res  = await fetch('/api/extract', { method: 'POST', body: form })
    const data = await res.json()
    const id   = data.job_id
    setJobId(id)

    // SSE stream
    const es = new EventSource(`/api/progress/${id}`)

    es.addEventListener('log', (e) => {
      const entry: LogEntry = JSON.parse(e.data)
      setLog(prev => {
        const idx = prev.findIndex(l => l.page === entry.page)
        if (idx >= 0) { const n = [...prev]; n[idx] = entry; return n }
        return [...prev, entry]
      })
    })

    es.addEventListener('progress', (e) => {
      const d: ProgressData = JSON.parse(e.data)
      setProgData(d); setProgress(d.progress)
    })

    es.addEventListener('complete', (e) => {
      const d: CompleteData = JSON.parse(e.data)
      setComplete(d); setStatus('done'); setProgress(100); es.close()
    })

    es.addEventListener('error', (e) => {
      const d = JSON.parse((e as MessageEvent).data ?? '{}')
      setError(d.message ?? 'Unknown error'); setStatus('error'); es.close()
    })
  }

  const reset = () => {
    setFile(null); setStatus('idle'); setLog([]); setProgress(0)
    setProgData(null); setComplete(null); setError(null); setJobId(null)
  }

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-[#0a0a0f] text-slate-100">
      <div className="max-w-3xl mx-auto px-4 py-16">

        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-500 to-cyan-500 flex items-center justify-center shadow-lg shadow-indigo-500/25">
              <Zap size={22} className="text-white" />
            </div>
            <div className="text-left">
              <h1 className="text-2xl font-bold text-white">PDF → Excel</h1>
              <p className="text-sm text-slate-500">AI-powered data extraction</p>
            </div>
          </div>
          <p className="text-slate-400 text-sm max-w-md mx-auto leading-relaxed">
            Upload any PDF — scanned or digital. The AI reads every page, extracts all tables and metrics, and generates a clean Excel file.
          </p>
        </div>

        {/* Upload zone */}
        {status === 'idle' && (
          <div className="slide-up space-y-4">
            <div
              onDragOver={e => { e.preventDefault(); setDragging(true) }}
              onDragLeave={() => setDragging(false)}
              onDrop={onDrop}
              onClick={() => fileInputRef.current?.click()}
              className={cn(
                'relative border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all duration-200',
                dragging ? 'border-indigo-500 bg-indigo-500/5 scale-[1.01]' : 'border-[#1e293b] hover:border-indigo-500/50 hover:bg-[#111827]',
                file ? 'border-green-500/50 bg-green-500/5' : '',
              )}
            >
              <input ref={fileInputRef} type="file" accept=".pdf" className="hidden"
                onChange={e => e.target.files?.[0] && setFile(e.target.files[0])} />

              {file ? (
                <div className="flex flex-col items-center gap-3">
                  <div className="w-14 h-14 rounded-xl bg-green-500/10 border border-green-500/20 flex items-center justify-center">
                    <FileText size={24} className="text-green-400" />
                  </div>
                  <div>
                    <p className="font-semibold text-white">{file.name}</p>
                    <p className="text-sm text-slate-500 mt-0.5">{(file.size / 1024).toFixed(1)} KB · Click to change</p>
                  </div>
                  <Badge color="green">Ready to extract</Badge>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-3">
                  <div className="w-14 h-14 rounded-xl bg-[#1e293b] flex items-center justify-center">
                    <Upload size={24} className="text-slate-400" />
                  </div>
                  <div>
                    <p className="font-medium text-slate-300">Drop your PDF here</p>
                    <p className="text-sm text-slate-500 mt-0.5">or click to browse</p>
                  </div>
                </div>
              )}
            </div>

            {/* Options */}
            <div className="bg-[#111827] border border-[#1e293b] rounded-2xl p-5 space-y-4">
              <p className="text-xs text-slate-500 uppercase tracking-widest font-semibold">Options</p>

              {/* Speed */}
              <div>
                <p className="text-sm text-slate-400 mb-2">Processing speed</p>
                <div className="grid grid-cols-3 gap-2">
                  {(Object.keys(SPEED_MAP) as Speed[]).map(s => (
                    <button key={s} onClick={() => setSpeed(s)}
                      className={cn(
                        'py-2 px-3 rounded-lg text-sm font-medium border transition-all',
                        speed === s
                          ? 'bg-indigo-500/10 border-indigo-500/40 text-indigo-300'
                          : 'bg-[#0a0a0f] border-[#1e293b] text-slate-400 hover:border-slate-600',
                      )}>
                      {SPEED_MAP[s].label}
                    </button>
                  ))}
                </div>
                <p className="text-xs text-slate-600 mt-1.5">
                  {speed === 'safe' ? 'Recommended — avoids Groq rate limits' :
                   speed === 'fast' ? 'May hit rate limits on large PDFs' :
                   'Risk of 429 errors on free tier'}
                </p>
              </div>

              {/* Page range */}
              <div>
                <p className="text-sm text-slate-400 mb-2">Page range</p>
                <div className="flex gap-2 mb-2">
                  {(['all', 'custom'] as const).map(m => (
                    <button key={m} onClick={() => setPageMode(m)}
                      className={cn(
                        'py-1.5 px-4 rounded-lg text-sm font-medium border transition-all',
                        pageMode === m
                          ? 'bg-indigo-500/10 border-indigo-500/40 text-indigo-300'
                          : 'bg-[#0a0a0f] border-[#1e293b] text-slate-400 hover:border-slate-600',
                      )}>
                      {m === 'all' ? 'All pages' : 'Custom range'}
                    </button>
                  ))}
                </div>
                {pageMode === 'custom' && (
                  <div className="flex gap-3 items-center">
                    <input type="number" min={1} value={startPage}
                      onChange={e => setStartPage(Number(e.target.value))}
                      className="w-24 bg-[#0a0a0f] border border-[#1e293b] rounded-lg px-3 py-1.5 text-sm text-slate-200 focus:outline-none focus:border-indigo-500" />
                    <span className="text-slate-500 text-sm">to</span>
                    <input type="number" min={1} value={endPage}
                      onChange={e => setEndPage(Number(e.target.value))}
                      className="w-24 bg-[#0a0a0f] border border-[#1e293b] rounded-lg px-3 py-1.5 text-sm text-slate-200 focus:outline-none focus:border-indigo-500" />
                  </div>
                )}
              </div>
            </div>

            {/* Extract button */}
            <button
              onClick={startExtraction}
              disabled={!file}
              className={cn(
                'w-full py-3.5 rounded-xl font-semibold text-sm transition-all duration-200 flex items-center justify-center gap-2',
                file
                  ? 'bg-gradient-to-r from-indigo-600 to-indigo-500 text-white hover:from-indigo-500 hover:to-indigo-400 shadow-lg shadow-indigo-500/25 hover:shadow-indigo-500/40 hover:-translate-y-0.5'
                  : 'bg-[#1e293b] text-slate-600 cursor-not-allowed',
              )}>
              <Sparkles size={16} />
              Extract & Generate Excel
            </button>
          </div>
        )}

        {/* Processing view */}
        {(status === 'running' || status === 'done') && (
          <div className="space-y-4 slide-up">

            {/* Progress card */}
            <div className="bg-[#111827] border border-[#1e293b] rounded-2xl p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2.5">
                  {status === 'running' && !progData?.waiting && (
                    <div className="w-2.5 h-2.5 rounded-full bg-amber-400 pulse-dot" />
                  )}
                  {status === 'running' && progData?.waiting && (
                    <div className="w-2.5 h-2.5 rounded-full bg-indigo-400 pulse-dot" />
                  )}
                  {status === 'done' && (
                    <div className="w-2.5 h-2.5 rounded-full bg-green-400" />
                  )}
                  <span className="font-semibold text-white">
                    {status === 'done' ? 'Complete' :
                     progData?.waiting ? '⏳ Rate limiting — waiting before next page...' :
                     `Extracting page ${progData?.current_page ?? ''}...`}
                  </span>
                </div>
                <span className="text-slate-500 text-sm">
                  {progData ? `${progData.done_count} / ${progData.total} pages` : ''}
                </span>
              </div>

              {/* Progress bar */}
              <div className="h-2 bg-[#1e293b] rounded-full overflow-hidden mb-4">
                <div
                  className="h-full bg-gradient-to-r from-indigo-600 to-cyan-500 rounded-full transition-all duration-500"
                  style={{ width: `${progress}%` }}
                />
              </div>

              {/* Rate limit banner */}
              {progData?.waiting && (
                <div className="flex items-center gap-2.5 bg-indigo-500/10 border border-indigo-500/20 rounded-lg px-4 py-2.5 mb-4">
                  <Loader2 size={14} className="text-indigo-400 animate-spin flex-shrink-0" />
                  <span className="text-indigo-300 text-sm">
                    Rate limit pause — waiting before next API call. This is normal on the free tier.
                  </span>
                </div>
              )}

              {/* Stats */}
              <div className="grid grid-cols-4 gap-3">
                <StatCard label="Pages Done" value={progData?.done_count ?? 0}  color="text-indigo-400" />
                <StatCard label="Remaining"  value={(progData?.total ?? 0) - (progData?.done_count ?? 0)} color="text-slate-300" />
                <StatCard label="Tables"     value={complete?.total_tables ?? log.filter(l=>l.tables>0).reduce((a,l)=>a+l.tables,0)} color="text-cyan-400" />
                <StatCard label="Progress"   value={`${progress}%`} color="text-green-400" />
              </div>
            </div>

            {/* Live log */}
            <div className="bg-[#111827] border border-[#1e293b] rounded-2xl overflow-hidden">
              <button
                onClick={() => setLogOpen(o => !o)}
                className="w-full flex items-center justify-between px-5 py-3.5 text-sm font-medium text-slate-300 hover:bg-[#1e293b]/50 transition-colors">
                <span>Processing log</span>
                {logOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
              </button>
              {logOpen && (
                <div className="px-3 pb-3 max-h-64 overflow-y-auto space-y-1">
                  {[...log].reverse().map((entry, i) => (
                    <LogRow key={entry.page} entry={entry} index={i} />
                  ))}
                  {log.length === 0 && (
                    <div className="text-center py-6 text-slate-600 text-sm">Waiting for first page...</div>
                  )}
                </div>
              )}
            </div>

            {/* Download — shown when done */}
            {status === 'done' && complete && (
              <div className="bg-gradient-to-br from-green-500/10 to-cyan-500/10 border border-green-500/20 rounded-2xl p-6 text-center slide-up">
                <CheckCircle2 size={36} className="text-green-400 mx-auto mb-3" />
                <h2 className="text-lg font-bold text-white mb-1">Extraction Complete</h2>
                <p className="text-slate-400 text-sm mb-5">
                  {complete.pages} pages · {complete.total_tables} tables · {complete.total_metrics} metrics
                </p>
                <div className="flex gap-3 justify-center">
                  <a
                    href={`/api/download/${complete.job_id}`}
                    download
                    className="inline-flex items-center gap-2 bg-gradient-to-r from-green-600 to-green-500 text-white px-6 py-2.5 rounded-xl font-semibold text-sm hover:from-green-500 hover:to-green-400 shadow-lg shadow-green-500/25 hover:-translate-y-0.5 transition-all">
                    <Download size={16} />
                    Download Excel
                  </a>
                  <button
                    onClick={reset}
                    className="inline-flex items-center gap-2 bg-[#1e293b] text-slate-300 px-6 py-2.5 rounded-xl font-semibold text-sm hover:bg-[#334155] transition-all">
                    Extract Another
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Error */}
        {status === 'error' && (
          <div className="bg-red-500/10 border border-red-500/20 rounded-2xl p-5 flex gap-3 items-start slide-up">
            <XCircle size={18} className="text-red-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-red-300">Extraction failed</p>
              <p className="text-sm text-red-400/70 mt-0.5">{error}</p>
              <button onClick={reset} className="mt-3 text-sm text-slate-400 hover:text-white underline">Try again</button>
            </div>
          </div>
        )}

        {/* How it works */}
        {status === 'idle' && !file && (
          <div className="grid grid-cols-4 gap-3 mt-10">
            {[
              { icon: <Upload size={18} />,    title: 'Upload',   desc: 'Any PDF, scanned or digital' },
              { icon: <Sparkles size={18} />,  title: 'AI Reads', desc: 'Vision model per page'       },
              { icon: <Table2 size={18} />,    title: 'Extracts', desc: 'Tables, metrics, text'       },
              { icon: <Download size={18} />,  title: 'Download', desc: 'Formatted Excel file'        },
            ].map(({ icon, title, desc }) => (
              <div key={title} className="bg-[#111827] border border-[#1e293b] rounded-xl p-4 text-center">
                <div className="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 mx-auto mb-2">
                  {icon}
                </div>
                <p className="text-sm font-semibold text-slate-200">{title}</p>
                <p className="text-xs text-slate-500 mt-0.5">{desc}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
