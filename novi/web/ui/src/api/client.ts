import type {
  AttentionSnapshot,
  BrainState,
  ChatChunk,
  ContextResponse,
  EventsChunk,
  IdentityDetail,
  KnowledgeResults,
  ListenResult,
  MemoryResults,
  ModelInfo,
  NameObjectResult,
  OpaqueResult,
  PreviewFrame,
  RealIOStatus,
  RecognitionList,
  RecognitionProposals,
  SoulDetail,
  StreamEvent,
} from './types'

export class ApiError extends Error {
  constructor(status: number) {
    super(`HTTP ${status}`)
    this.name = 'ApiError'
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(path, init)
  if (!resp.ok) throw new ApiError(resp.status)
  return (await resp.json()) as T
}

function postJson(body: object): RequestInit {
  return {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }
}

/**
 * Streaming chat: POST /api/chat/stream yields SSE `data:` frames separated by
 * a blank line. Frames are either {token}, {done, user, novi}, {error}, or
 * {deduplicated}. Ported from the legacy console's fetch-stream loop.
 */
export async function streamChat(
  text: string,
  confidence: number,
  onEvent: (e: StreamEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const resp = await fetch('/api/chat/stream', {
    ...postJson({ text, confidence }),
    signal,
  })
  if (!resp.ok || !resp.body) throw new Error('no stream')
  const reader = resp.body.getReader()
  const dec = new TextDecoder()
  let buf = ''
  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    buf += dec.decode(value, { stream: true })
    let idx: number
    while ((idx = buf.indexOf('\n\n')) !== -1) {
      const frame = buf.slice(0, idx)
      buf = buf.slice(idx + 2)
      for (const line of frame.split('\n')) {
        if (!line.startsWith('data:')) continue
        const jsonStr = line.slice(5).trim()
        if (!jsonStr) continue
        try {
          const evt = JSON.parse(jsonStr)
          if (evt.deduplicated) {
            onEvent({
              kind: 'deduplicated',
              after: evt.after,
              noviSeq: evt.novi?.seq,
              userSeq: evt.user?.seq,
            })
          } else if (evt.token != null) {
            onEvent({ kind: 'token', token: String(evt.token) })
          } else if (evt.done) {
            onEvent({
              kind: 'done',
              after: evt.after,
              text: evt.novi?.text,
              trace: evt.novi?.trace,
              userSeq: evt.user?.seq,
              noviSeq: evt.novi?.seq,
            })
          } else if (evt.error) {
            onEvent({ kind: 'error', error: String(evt.error) })
          }
        } catch {
          /* skip malformed frame */
        }
      }
    }
  }
}

export const api = {
  state: () => request<BrainState>('/api/state'),
  model: () => request<ModelInfo>('/api/model'),
  setModel: (model: string) => request<ModelInfo>('/api/model', postJson({ model })),
  attention: () => request<AttentionSnapshot>('/api/attention'),
  context: () => request<ContextResponse>('/api/context'),
  soul: () => request<SoulDetail>('/api/soul'),
  identity: () => request<IdentityDetail>('/api/identity'),
  memory: (query: string, limit = 8) =>
    request<MemoryResults>(`/api/memory?query=${encodeURIComponent(query)}&limit=${limit}`),
  knowledge: (entity: string, limit = 10) =>
    request<KnowledgeResults>(`/api/knowledge?entity=${encodeURIComponent(entity)}&limit=${limit}`),
  events: (after: number) => request<EventsChunk>(`/api/events?after=${after}`),
  chat: (after: number) => request<ChatChunk>(`/api/chat?after=${after}`),

  perceptionState: () => request<OpaqueResult>('/api/perception/state'),
  preview: (signal?: AbortSignal) =>
    request<PreviewFrame>('/api/preview', signal ? { signal } : undefined),
  recognition: (kind?: string) =>
    request<RecognitionList>(`/api/recognition${kind ? `?kind=${encodeURIComponent(kind)}` : ''}`),
  realStatus: () => request<RealIOStatus>('/api/real/status'),
  realEnable: () => request<OpaqueResult>('/api/real/enable', postJson({ camera: true, mic: true, speaker: true })),
  realSpeakback: (enabled: boolean) => request<OpaqueResult>('/api/real/speakback', postJson({ enabled })),
  voiceListen: (seconds = 3, clientSpeaks = true) =>
    request<OpaqueResult>('/api/voice/listen', postJson({ seconds, client_speaks: clientSpeaks })),
  voiceTurn: (text: string) => request<OpaqueResult>('/api/voice/turn', postJson({ text })),
  enrollFace: (name: string) => request<OpaqueResult>('/api/recognition/enroll-face', postJson({ name })),
  enrollVoice: (name: string) => request<OpaqueResult>('/api/recognition/enroll-voice', postJson({ name })),
  proposals: () => request<RecognitionProposals>('/api/recognition/proposals'),
  nameObject: (body: { category: string; name: string; frame_id?: string }) =>
    request<NameObjectResult>('/api/recognition/name-object', postJson(body)),
  p0Gate: () => request<OpaqueResult>('/api/p0-gate'),

  // action buttons
  audio: (hint: string | null, rms = 0.7, novelty = 0.9, confidence = 0.9) =>
    request<OpaqueResult>('/api/audio', postJson({ event_hint: hint, rms, novelty, confidence })),
  goal: (x: number, y: number, maxSteps = 60) =>
    request<OpaqueResult>('/api/goal', postJson({ x, y, max_steps: maxSteps })),
  step: () => request<OpaqueResult>('/api/step', postJson({})),
  health: () => request<OpaqueResult>('/api/health', postJson({})),
  chatClear: () => request<OpaqueResult>('/api/chat/clear', postJson({})),
  listen: () => request<ListenResult>('/api/listen', postJson({})),
  // generic fallback for the non-streaming chat path
  chatFallback: (text: string, confidence: number) =>
    request<OpaqueResult>('/api/chat', postJson({ text, confidence })),
}
