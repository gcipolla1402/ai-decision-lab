import { AlertTriangle, CheckCircle2, CircleDashed, Gauge, Route as RouteIcon } from 'lucide-react'
import type { AnalysisResponse, Route } from '../types'

const routeLabel: Record<Route, string> = {
  APPROVE_FOR_REVIEW: 'Approve for review',
  NEEDS_HUMAN_REVIEW: 'Human review needed',
  INSUFFICIENT_INFORMATION: 'Insufficient information',
}

export function ResultPanel({ result }: { result: AnalysisResponse | null }) {
  if (!result) {
    return (
      <section className="panel result-panel empty-state">
        <CircleDashed size={34} />
        <h2>Awaiting an analysis</h2>
        <p>Upload a synthetic document to inspect structured extraction, routing, and stage timings.</p>
      </section>
    )
  }

  const { analysis, decision } = result
  const executionLabel = {
    DEMO: 'DEMO · LOCAL',
    GEMINI_ONLY: 'GEMINI ONLY · LIVE ANALYSIS',
    GEMINI_JEV: 'GEMINI + JEV · LIVE',
  }[result.conditions.execution_mode]
  return (
    <section className="panel result-panel">
      <div className="panel-heading">
        <div><span className="eyebrow">02 / OUTPUT</span><h2>Analysis record</h2></div>
        <span className="fingerprint">#{result.conditions.input_fingerprint}</span>
      </div>

      <div className={`decision-banner route-${decision.route}`}>
        <RouteIcon size={22} />
        <div><small>RECOMMENDED ROUTE</small><strong>{routeLabel[decision.route]}</strong></div>
        <span>{Math.round(decision.confidence * 100)}% confidence</span>
      </div>

      <div className="result-grid">
        <div className="summary-block">
          <span className="label">DOCUMENT SUMMARY</span>
          <p>{analysis.summary}</p>
          <div className="tags">
            <span>{analysis.document_type}</span>
            <span className={result.conditions.paid_calls_made ? 'tag-live' : ''}>{executionLabel}</span>
          </div>
        </div>
        <div className="score-block">
          <Gauge size={20} /><strong>{analysis.completeness_score}</strong><span>/ 100</span><small>completeness</small>
        </div>
      </div>

      <div className="provider-trace">
        <div>
          <span className="label">ANALYSIS PROVIDER</span>
          <strong>{result.conditions.analysis_provider}</strong>
          <small>{result.conditions.analysis_model} · {result.conditions.analysis_simulated ? 'simulated' : 'live API'}</small>
        </div>
        <div>
          <span className="label">ROUTING PROVIDER</span>
          <strong>{result.conditions.decision_provider}</strong>
          <small>{decision.model ?? 'not reported'} · {result.conditions.decision_simulated ? 'simulated' : 'live API'}</small>
        </div>
        <span className={`call-status ${result.conditions.paid_calls_made ? 'live' : ''}`}>
          {result.conditions.paid_calls_made ? 'EXTERNAL API USED' : 'NO EXTERNAL CALLS'}
        </span>
      </div>

      <div className="indicators">
        <span className="label">OBJECTIVE INDICATORS</span>
        {analysis.indicators.map((indicator) => (
          <div className="indicator" key={indicator.name} title={indicator.evidence}>
            {indicator.observed ? <CheckCircle2 size={17} /> : <AlertTriangle size={17} />}
            <span>{indicator.name}</span><strong>{indicator.value}</strong>
          </div>
        ))}
      </div>

      <div className="timings">
        {result.timings.map((item) => (
          <div key={item.stage}><span>{item.stage}</span><strong>{item.duration_ms.toFixed(1)} ms</strong></div>
        ))}
        <div className="total"><span>total</span><strong>{result.total_duration_ms.toFixed(1)} ms</strong></div>
      </div>
      <p className="disclaimer">{result.disclaimer}</p>
    </section>
  )
}

