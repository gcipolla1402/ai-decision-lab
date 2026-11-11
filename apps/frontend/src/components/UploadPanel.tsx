import { FileText, FlaskConical, UploadCloud } from 'lucide-react'
import { useRef, useState } from 'react'
import type { ProviderMode } from '../types'

interface Props {
  busy: boolean
  onAnalyze: (file: File, mode: ProviderMode) => void
  onCompare: (file: File, mode: ProviderMode) => void
}

export function UploadPanel({ busy, onAnalyze, onCompare }: Props) {
  const [file, setFile] = useState<File | null>(null)
  const [mode, setMode] = useState<ProviderMode>('demo')
  const input = useRef<HTMLInputElement>(null)

  const choose = (candidate?: File) => {
    if (candidate && ['application/pdf', 'text/plain'].includes(candidate.type)) setFile(candidate)
  }

  return (
    <section className="panel upload-panel">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">01 / INPUT</span>
          <h2>Document intake</h2>
        </div>
        <span className={`mode-pill ${mode !== 'demo' ? 'live' : ''}`}>
          {mode === 'demo' ? 'SAFE DEMO' : mode === 'gemini' ? 'GEMINI LIVE' : 'GEMINI + JEV LIVE'}
        </span>
      </div>

      <button
        className="dropzone"
        type="button"
        onClick={() => input.current?.click()}
        onDragOver={(event) => event.preventDefault()}
        onDrop={(event) => { event.preventDefault(); choose(event.dataTransfer.files[0]) }}
      >
        <input ref={input} hidden type="file" accept=".pdf,.txt,application/pdf,text/plain" onChange={(event) => choose(event.target.files?.[0])} />
        {file ? <FileText size={30} /> : <UploadCloud size={30} />}
        <strong>{file?.name ?? 'Drop a synthetic PDF or TXT'}</strong>
        <span>{file ? `${(file.size / 1024).toFixed(1)} KB · ready` : 'or click to browse · configured server limit applies'}</span>
      </button>

      <div className="provider-mode" role="group" aria-label="Provider mode">
        <span><strong>Provider mode</strong><small>Select the exact execution path</small></span>
        <div className="mode-options">
          <button type="button" className={mode === 'demo' ? 'active' : ''} onClick={() => setMode('demo')}>
            <strong>DEMO</strong><small>Local analysis + routing</small>
          </button>
          <button type="button" className={mode === 'gemini' ? 'active' : ''} onClick={() => setMode('gemini')}>
            <strong>GEMINI ONLY</strong><small>Gemini + local routing</small>
          </button>
          <button type="button" className={mode === 'gemini_jev' ? 'active' : ''} onClick={() => setMode('gemini_jev')}>
            <strong>GEMINI + JEV</strong><small>Both live providers</small>
          </button>
        </div>
      </div>

      <div className="actions">
        <button className="primary" disabled={!file || busy} onClick={() => file && onAnalyze(file, mode)}>
          <FlaskConical size={18} /> {busy ? 'Running…' : 'Analyze document'}
        </button>
        <button
          className="secondary"
          disabled={!file || busy || mode === 'gemini'}
          title={mode === 'gemini' ? 'Select GEMINI + JEV to run the live comparison.' : undefined}
          onClick={() => file && onCompare(file, mode)}
        >
          {mode === 'gemini' ? 'Select JEV to compare' : 'Compare modes'}
        </button>
      </div>
      <p className="microcopy">
        {mode === 'demo' ? 'No external API calls.' : mode === 'gemini' ? 'Makes a Gemini call; routing stays local.' : 'Makes one Gemini analysis call and one JEV routing call.'}
        {' '}Use synthetic content only.
      </p>
    </section>
  )
}

