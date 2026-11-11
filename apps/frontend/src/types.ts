export type Route = 'APPROVE_FOR_REVIEW' | 'NEEDS_HUMAN_REVIEW' | 'INSUFFICIENT_INFORMATION'
export type ProviderMode = 'demo' | 'gemini' | 'gemini_jev'

export interface Indicator {
  name: string
  value: string
  observed: boolean
  evidence: string
}

export interface DocumentAnalysis {
  summary: string
  document_type: string
  attention_items: string[]
  indicators: Indicator[]
  completeness_score: number
}

export interface Decision {
  route: Route
  confidence: number
  rationale: string
  provider: string
  simulated: boolean
  model?: string
}

export interface Timing { stage: string; duration_ms: number }

export interface Conditions {
  execution_mode: 'DEMO' | 'GEMINI_ONLY' | 'GEMINI_JEV'
  analysis_provider: string
  analysis_model: string
  analysis_simulated: boolean
  decision_provider: string
  decision_simulated: boolean
  input_fingerprint: string
  shared_extraction: boolean
  shared_analysis: boolean
  cache_used: boolean
  paid_calls_made: boolean
  notes: string[]
}

export interface AnalysisResponse {
  run_id: string
  filename: string
  analysis: DocumentAnalysis
  decision: Decision
  timings: Timing[]
  total_duration_ms: number
  conditions: Conditions
  disclaimer: string
}

export interface ComparisonArm {
  label: string
  decision: Decision
  timings: Timing[]
  total_duration_ms: number
  conditions: Conditions
}

export interface ComparisonResponse {
  run_id: string
  filename: string
  analysis: DocumentAnalysis
  arms: ComparisonArm[]
  comparable: boolean
  comparability_notes: string[]
  disclaimer: string
}

export interface HistoryEntry {
  id: string
  filename: string
  route: Route
  duration: number
  timestamp: string
  simulated: boolean
}

