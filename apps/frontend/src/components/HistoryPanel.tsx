import { Clock3 } from 'lucide-react'
import type { HistoryEntry } from '../types'

export function HistoryPanel({ entries, onClear }: { entries: HistoryEntry[]; onClear: () => void }) {
  return (
    <aside className="panel history-panel">
      <div className="panel-heading"><div><span className="eyebrow">SESSION</span><h2>Recent runs</h2></div><Clock3 size={20} /></div>
      {entries.length === 0 ? <p className="history-empty">No local runs yet.</p> : entries.map((entry) => (
        <div className="history-item" key={entry.id}>
          <i className={`history-dot route-${entry.route}`} />
          <div><strong>{entry.filename}</strong><span>{entry.route.replaceAll('_', ' ').toLowerCase()}</span></div>
          <div><strong>{entry.duration.toFixed(0)} ms</strong><span>{entry.timestamp}</span></div>
        </div>
      ))}
      {entries.length > 0 && <button className="clear-button" onClick={onClear}>Clear session history</button>}
    </aside>
  )
}

