import { GitCompareArrows, ShieldCheck } from 'lucide-react'
import type { ComparisonResponse } from '../types'

export function ComparisonPanel({ comparison }: { comparison: ComparisonResponse | null }) {
  if (!comparison) return null
  const max = Math.max(...comparison.arms.map((arm) => arm.total_duration_ms), 1)
  return (
    <section className="panel comparison-panel">
      <div className="panel-heading">
        <div><span className="eyebrow">03 / BENCHMARK</span><h2>Controlled comparison</h2></div>
        <GitCompareArrows size={22} />
      </div>
      <div className="comparison-arms">
        {comparison.arms.map((arm) => (
          <article key={arm.label}>
            <div className="arm-title"><strong>{arm.label}</strong><span>{arm.decision.simulated ? 'simulated' : arm.decision.model}</span></div>
            <div className="duration">{arm.total_duration_ms.toFixed(1)} <small>ms</small></div>
            <div className="duration-track"><i style={{ width: `${Math.max((arm.total_duration_ms / max) * 100, 2)}%` }} /></div>
            <dl>
              <div><dt>Routing</dt><dd>{arm.conditions.decision_provider}</dd></div>
              <div><dt>Cache</dt><dd>{arm.conditions.cache_used ? 'used' : 'not used'}</dd></div>
              <div><dt>Input</dt><dd>#{arm.conditions.input_fingerprint}</dd></div>
            </dl>
          </article>
        ))}
      </div>
      <div className="method-note"><ShieldCheck size={19} /><div><strong>Measurement context</strong>{comparison.comparability_notes.map((note) => <p key={note}>{note}</p>)}</div></div>
      <p className="disclaimer">{comparison.disclaimer}</p>
    </section>
  )
}

