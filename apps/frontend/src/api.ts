import type { AnalysisResponse, ComparisonResponse } from './types'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

async function parse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: 'Request failed.' }))
    throw new Error(typeof body.detail === 'string' ? body.detail : 'Request failed.')
  }
  return response.json() as Promise<T>
}

export async function analyze(
  file: File,
  analysisMode: 'demo' | 'gemini',
  decisionMode: 'demo' | 'jev',
): Promise<AnalysisResponse> {
  const form = new FormData()
  form.append('file', file)
  form.append('analysis_mode', analysisMode)
  form.append('decision_mode', decisionMode)
  return parse(await fetch(`${API_BASE}/api/analyze`, { method: 'POST', body: form }))
}

export async function compare(file: File, live: boolean): Promise<ComparisonResponse> {
  const form = new FormData()
  form.append('file', file)
  form.append('live', String(live))
  return parse(await fetch(`${API_BASE}/api/compare`, { method: 'POST', body: form }))
}

