import { Activity, Braces, CodeXml, Sparkles } from 'lucide-react'
import { useEffect, useState } from 'react'
import { analyze, compare } from './api'
import { ComparisonPanel } from './components/ComparisonPanel'
import { HistoryPanel } from './components/HistoryPanel'
import { ResultPanel } from './components/ResultPanel'
import { UploadPanel } from './components/UploadPanel'
import type { AnalysisResponse, ComparisonResponse, HistoryEntry, ProviderMode } from './types'

const HISTORY_KEY = 'ai-decision-lab-history-v1'

export default function App() {
  const [result, setResult] = useState<AnalysisResponse | null>(null)
  const [comparison, setComparison] = useState<ComparisonResponse | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [history, setHistory] = useState<HistoryEntry[]>(() => {
    try { return JSON.parse(sessionStorage.getItem(HISTORY_KEY) ?? '[]') as HistoryEntry[] } catch { return [] }
  })

  useEffect(() => { sessionStorage.setItem(HISTORY_KEY, JSON.stringify(history)) }, [history])

  const run = async (file: File, mode: ProviderMode) => {
    setBusy(true); setError(null); setResult(null); setComparison(null)
    try {
      const payload = mode === 'demo'
        ? { analysis: 'demo' as const, decision: 'demo' as const }
        : mode === 'gemini'
          ? { analysis: 'gemini' as const, decision: 'demo' as const }
          : { analysis: 'gemini' as const, decision: 'jev' as const }
      const response = await analyze(file, payload.analysis, payload.decision)
      setResult(response)
      setHistory((current) => [{ id: response.run_id, filename: response.filename, route: response.decision.route, duration: response.total_duration_ms, timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }), simulated: response.decision.simulated }, ...current].slice(0, 8))
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Analysis failed.') }
    finally { setBusy(false) }
  }

  const runComparison = async (file: File, mode: ProviderMode) => {
    setBusy(true); setError(null); setComparison(null)
    try { setComparison(await compare(file, mode !== 'demo')) }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Comparison failed.') }
    finally { setBusy(false) }
  }

  return (
    <div className="app-shell">
      <header>
        <a className="brand" href="#top" aria-label="AI Decision Lab home"><span><Braces size={22} /></span><strong>AI Decision Lab</strong></a>
        <nav><a href="#workspace">Workspace</a><a href="#methodology">Methodology</a><span className="status"><i /> Local session</span></nav>
      </header>

      <main id="top">
        <section className="hero">
          <div className="hero-copy">
            <span className="kicker"><Sparkles size={14} /> AI ENGINEERING PORTFOLIO LAB</span>
            <h1>Documents in.<br /><em>Decisions explained.</em></h1>
            <p>Explore structured document analysis and typed decision routing with measurable, transparent execution paths.</p>
            <div className="hero-meta"><span><Activity size={16} /> deterministic demo ready</span><span>PDF + TXT</span><span>no persistence</span></div>
          </div>
          <div className="signal-card" aria-hidden="true"><div className="orb orb-a" /><div className="orb orb-b" /><div className="signal-grid" /><div className="signal-line"><i /><i /><i /><i /></div><span>ANALYZE</span><span>STRUCTURE</span><span>ROUTE</span></div>
        </section>

        {error && <div className="error-banner" role="alert">{error}</div>}
        <section className="workspace" id="workspace">
          <div className="workspace-main">
            <UploadPanel busy={busy} onAnalyze={run} onCompare={runComparison} />
            <ResultPanel result={result} />
            <ComparisonPanel comparison={comparison} />
          </div>
          <HistoryPanel entries={history} onClear={() => setHistory([])} />
        </section>

        <section className="methodology" id="methodology">
          <span className="eyebrow">MEASUREMENT PRINCIPLES</span><h2>Evidence before claims.</h2>
          <div><article><strong>01</strong><h3>Same input</h3><p>Each comparison reports a content fingerprint and whether extraction or analysis was shared.</p></article><article><strong>02</strong><h3>Stage timing</h3><p>Extraction, model analysis, and routing are timed independently with a monotonic clock.</p></article><article><strong>03</strong><h3>Explicit conditions</h3><p>Provider, model, cache status, paid-call status, and simulation state travel with every result.</p></article></div>
        </section>
      </main>
      <footer><span>Personal demonstration project · synthetic data only · not legal advice</span><span><CodeXml size={15} /> Built for reproducible AI engineering</span></footer>
    </div>
  )
}

