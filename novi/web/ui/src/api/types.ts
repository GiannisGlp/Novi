/**
 * API contracts for the Novi web console. Field names mirror the JSON the
 * Python server emits verbatim (see novi/web/server.py + integration_api.py).
 */

export interface ModelInfo {
  available: string[]
  current: string
}

export interface HealthStatus {
  status?: string
}

export interface ReasoningTrace {
  conclusion?: string
  confidence?: number
  route?: string
  route_reason?: string
  action?: string
  rationale?: string
  recalled?: number
  detections?: string[]
  cycle?: number
  inferences?: string[]
  hypotheses?: { hypothesis: string }[]
  deliberation?: {
    analysis?: string
    decision?: { rationale?: string }
    rounds?: {
      round: number
      analysis?: string
      evaluation?: string
      confirm?: boolean
      decision?: { action?: string }
    }[]
  }
}

export interface SoulState {
  identity?: string
  persona?: string
  tone?: string
  traits?: Record<string, number>
  affect?: Record<string, number>
  values?: Record<string, number>
}

export interface ActiveGoal {
  kind?: string
  target?: string
  status?: string
  steps_taken?: number
  distance_to_goal?: number
}

export interface PlanStep {
  action?: string
  done?: boolean
}

export interface GoalHistoryEntry {
  kind?: string
  status?: string
}

export interface BodyState {
  x_m?: number
  y_m?: number
  heading_deg?: number
}

export interface HearingEvent {
  event_type?: string
}

export interface MemorySummary {
  entity_refs?: string[]
  content?: string
}

export interface EmbedderState {
  provider?: string
  dimension?: number
  mode?: string
  available?: boolean
  error?: string
}

export interface MemoryState {
  active?: number
  summaries?: MemorySummary[]
  embedder?: EmbedderState
}

/** GET /api/soul — the standalone soul detail endpoint (identity + traits). */
export interface SoulDetail extends SoulState {
  [key: string]: unknown
}

export interface KnowledgeState {
  triples?: number
  entities?: number
  contradicted?: number
}

export interface SleepCycleState {
  enabled?: boolean
  every_n_cycles?: number
  phases_run?: number
  last_phase?: { phase?: string; summary?: string }
}

export interface RouterState {
  route_counts_by_class?: Record<string, number>
  last_route?: string
  last_reason?: string
}

export interface BrainState {
  cycle: number
  run_id?: string
  health?: HealthStatus
  reasoning_trace?: ReasoningTrace
  last_step?: { detections?: string[] }
  soul?: SoulState
  active_goal?: ActiveGoal | null
  plan?: { steps?: PlanStep[] }
  goals_history?: GoalHistoryEntry[]
  body?: BodyState
  knowledge?: KnowledgeState
  hearing?: HearingEvent[]
  memory?: MemoryState
  narrative?: string[]
  sleep_cycle?: SleepCycleState
  router?: RouterState
}

// ---- attention / context / identity ----

export interface AttentionCandidate {
  entity_id?: string
  id?: string
  target?: string
  attention_score?: number
  score?: number
  reason?: string
  suggested_action?: string
  kind?: string
}

export interface AttentionSnapshot {
  candidates?: AttentionCandidate[]
  typed_cognition?: { situation?: { salience?: string; kind?: string } }
  situations?: { situation_id?: string; kind?: string; salience?: string }[]
}

export interface ContextEntity {
  entity_ref?: string
  id?: string
  ref?: string
  epistemic_status?: string
  status?: string
}

export interface ContextRelation {
  subject?: string
  a?: string
  predicate?: string
  relation?: string
  object?: string
  b?: string
}

export interface ContextUncertainty {
  entity?: string
  ref?: string
  reason?: string
  status?: string
}

export interface ContextPackage {
  visible_entities?: ContextEntity[]
  entities?: ContextEntity[]
  relations?: ContextRelation[]
  relationships?: ContextRelation[]
  uncertainty?: ContextUncertainty[]
  contradictions?: ContextUncertainty[]
}

export interface ContextResponse {
  package?: ContextPackage
  cycle?: number
}

export interface IdentityEntry {
  name?: string
  person?: string
  tier?: string
  confidence?: number
  evidence?: Record<string, unknown>
  modality?: string
}

export interface IdentityDetail {
  current?: IdentityEntry
  snapshot?: { history?: IdentityEntry[]; identities?: IdentityEntry[] }
}

// ---- memory / knowledge ----

export interface MemoryResult {
  memory_type?: string
  entity_refs?: string[]
  confidence?: number
  content?: string
}

export interface MemoryResults {
  results: MemoryResult[]
  retrieval_state?: string
}

export interface KnowledgeTriple {
  subject?: string
  s?: string
  predicate?: string
  pred?: string
  relation?: string
  object?: string
  o?: string
}

export interface KnowledgeResults {
  triples: KnowledgeTriple[]
  counts: { triples?: number }
}

// ---- events / chat ----

export interface BrainEvent {
  seq?: number
  ts?: number
  event: {
    event_type?: string
    cycle?: number
    [key: string]: unknown
  }
}

export interface EventsChunk {
  after: number
  events?: BrainEvent[]
}

export interface ChatEntry {
  seq?: number
  role: 'user' | 'novi'
  text: string
  trace?: ReasoningTrace
}

export interface ChatChunk {
  after: number
  entries?: ChatEntry[]
}

export type StreamEvent =
  | { kind: 'deduplicated'; after?: number; noviSeq?: number; userSeq?: number }
  | { kind: 'token'; token: string }
  | { kind: 'done'; after?: number; text?: string; trace?: ReasoningTrace; userSeq?: number; noviSeq?: number }
  | { kind: 'error'; error: string }

// ---- perception / recognition / real I/O ----

export interface PreviewFace {
  bbox?: number[]
  person?: string
  tier?: string
  proposal?: boolean
}

export interface PreviewTrack {
  bbox?: number[]
  label?: string
  track_id?: number
  is_person?: boolean
  name?: string
}

export interface PreviewFrame {
  camera_health?: string
  stale?: boolean
  image_data_url?: string
  person?: string
  tier?: string
  place?: string
  detections?: { label?: string; confidence?: number; bbox?: number[] }[]
  face?: PreviewFace
  tracks?: PreviewTrack[]
  detector_backend?: string
  faces_backend?: string
}

export interface RecognitionList {
  enrollments?: { kind?: string; label?: string }[]
}

export interface RealIOStatus {
  enabled?: boolean
  devices?: { camera?: boolean; mic?: boolean; speaker?: boolean }
  speak_back?: boolean
}

export interface ListenResult {
  error?: string
  result?: { heard?: boolean }
}

// The remaining integration endpoints (perception/state, p0-gate, real/enable,
// voice/*, recognition/enroll-*) return opaque JSON; typed as Record<string, unknown>.
export type OpaqueResult = Record<string, unknown>
