import { useCallback, useRef, useState } from 'react'
import { api, streamChat } from '../api/client'
import type { ReasoningTrace } from '../api/types'
import { usePoll } from './usePoll'

export const CHAT_POLL_MS = 1200
export const STREAM_TIMEOUT_MS = 125000
export const DUPLICATE_WINDOW_MS = 15000
export const MAX_TURNS = 90

export interface ChatTurn {
  seq?: number
  role: 'user' | 'novi'
  text: string
  trace?: ReasoningTrace
}

export interface StreamingState {
  text: string
  error?: string
}

export interface ChatData {
  turns: ChatTurn[]
  streaming: StreamingState | null
  isStreaming: boolean
  isListening: boolean
  send: (text: string, confidence: number) => Promise<void>
  refresh: () => Promise<void>
  clear: () => Promise<void>
  step: () => Promise<void>
  listen: () => Promise<void>
  notice: (text: string) => void
}

/**
 * Conversation state + the streaming chat flow. Ports the legacy console's
 * refreshChat / streamChat / clear / step / listen, including the re-entrancy
 * guards (non-overlapping refresh, rendered-seq dedup, clear epoch), the 15s
 * duplicate-send window and the 125s stream timeout. The message list itself is
 * rendered by the chat drawer from `turns` + `streaming`.
 */
export function useChat(reportConnection: (ok: boolean) => void, getModelName?: () => string): ChatData {
  const [turns, setTurns] = useState<ChatTurn[]>([])
  const [streaming, setStreaming] = useState<StreamingState | null>(null)
  const [isStreaming, setIsStreaming] = useState(false)
  const [isListening, setIsListening] = useState(false)

  const chatAfterRef = useRef(0)
  const renderedSeqRef = useRef(new Set<number>())
  const epochRef = useRef(0)
  const refreshingRef = useRef(false)
  const streamingRef = useRef(false)
  const lastSentTextRef = useRef('')
  const lastSentAtRef = useRef(0)
  const optimisticRef = useRef<ChatTurn | null>(null)
  const reportRef = useRef(reportConnection)
  reportRef.current = reportConnection
  const modelNameRef = useRef(getModelName)
  modelNameRef.current = getModelName

  const pushTurns = useCallback((...newTurns: ChatTurn[]) => {
    setTurns((prev) => [...prev, ...newTurns].slice(-MAX_TURNS))
  }, [])

  const removeOptimistic = useCallback(() => {
    const opt = optimisticRef.current
    if (opt) {
      setTurns((prev) => prev.filter((t) => t !== opt))
      optimisticRef.current = null
    }
  }, [])

  const refresh = useCallback(async () => {
    if (refreshingRef.current || streamingRef.current) return
    refreshingRef.current = true
    const epoch = epochRef.current
    try {
      const r = await api.chat(chatAfterRef.current)
      if (epoch !== epochRef.current) return
      chatAfterRef.current = r.after
      reportRef.current(true)
      const fresh = (r.entries ?? []).filter((it) => it.seq == null || !renderedSeqRef.current.has(it.seq))
      for (const it of fresh) if (it.seq != null) renderedSeqRef.current.add(it.seq)
      if (fresh.length) pushTurns(...fresh)
    } catch {
      reportRef.current(false)
    } finally {
      refreshingRef.current = false
    }
  }, [pushTurns])

  const send = useCallback(
    async (text: string, confidence: number) => {
      const now = Date.now()
      if (text === lastSentTextRef.current && now - lastSentAtRef.current < DUPLICATE_WINDOW_MS) {
        return
      }
      lastSentTextRef.current = text
      lastSentAtRef.current = now
      streamingRef.current = true
      setIsStreaming(true)

      const optimistic: ChatTurn = { role: 'user', text }
      optimisticRef.current = optimistic
      setStreaming({ text: '' })
      pushTurns(optimistic)

      // Wrapped in an object so reads after the stream closure see the declared
      // types — TS does not track assignments made inside the onEvent callback.
      const streamState = {
        full: '',
        gotToken: false,
        doneEvt: null as { after?: number } | null,
        failed: false,
      }
      let abortTimer: ReturnType<typeof setTimeout> | null = null

      try {
        const controller = typeof AbortController !== 'undefined' ? new AbortController() : null
        if (controller) abortTimer = setTimeout(() => controller.abort(), STREAM_TIMEOUT_MS)
        try {
          await streamChat(
            text,
            confidence,
            (e) => {
              if (e.kind === 'deduplicated') {
                removeOptimistic()
                setStreaming(null)
                streamState.doneEvt = { after: e.after }
                streamState.gotToken = true
                if (e.after != null) chatAfterRef.current = e.after
                if (e.noviSeq != null) renderedSeqRef.current.add(e.noviSeq)
                if (e.userSeq != null) renderedSeqRef.current.add(e.userSeq)
              } else if (e.kind === 'token') {
                streamState.gotToken = true
                streamState.full += e.token
                setStreaming({ text: streamState.full })
                reportRef.current(true)
              } else if (e.kind === 'done') {
                streamState.doneEvt = e
                setStreaming(null)
                streamState.full = e.text ?? streamState.full
                pushTurns({ seq: e.noviSeq, role: 'novi', text: streamState.full, trace: e.trace })
                if (e.userSeq != null) renderedSeqRef.current.add(e.userSeq)
                if (e.noviSeq != null) renderedSeqRef.current.add(e.noviSeq)
                if (e.after != null) chatAfterRef.current = e.after
              } else if (e.kind === 'error') {
                setStreaming({ text: streamState.full, error: e.error })
                streamState.doneEvt = {}
                streamState.gotToken = true
              }
            },
            controller ? controller.signal : undefined,
          )
        } catch (err) {
          removeOptimistic()
          setStreaming(null)
          streamState.failed = true
          // jsdom's DOMException is not an `instanceof Error`, so key on name.
          const isAbort =
            (err as { name?: string } | null)?.name === 'AbortError' ||
            (err instanceof Error && /abort/i.test(err.message))
          if (isAbort) {
            pushTurns({
              role: 'novi',
              text: '(timed out — is Ollama/' + (modelNameRef.current?.() ?? 'model') + ' reachable?)',
            })
            reportRef.current(false)
          } else {
            try {
              await api.chatFallback(text, confidence)
              reportRef.current(true)
            } catch {
              pushTurns({ role: 'novi', text: '(reply failed — is the model reachable?)' })
              reportRef.current(false)
            }
          }
        }

        if (streamState.doneEvt && streamState.doneEvt.after == null) {
          chatAfterRef.current = Math.max(chatAfterRef.current, ...[...renderedSeqRef.current])
        } else if (!streamState.doneEvt && !streamState.failed) {
          // The stream ended without a `done` frame, so the server never recorded
          // the user's message (it appends chat rows only when done). Don't drop
          // the send silently: keep the optimistic turn and surface why there's
          // no reply so the user can decide whether to retry.
          pushTurns({
            role: 'novi',
            text: streamState.gotToken
              ? '(reply interrupted — the connection dropped mid-reply)'
              : '(no response received — the model may still be loading; try again)',
          })
        }
      } finally {
        if (abortTimer) clearTimeout(abortTimer)
        streamingRef.current = false
        setIsStreaming(false)
        // Keep only an explicit error bubble. A token-only stream that ends
        // without `done` is a dropped reply and gets the interruption notice
        // above; its partial text never survives as a frozen streaming bubble.
        setStreaming((s) => (s && s.error ? s : null))
        void refresh()
      }
    },
    [pushTurns, refresh, removeOptimistic],
  )

  const clear = useCallback(async () => {
    try {
      await api.chatClear()
      reportRef.current(true)
    } catch {
      reportRef.current(false)
    }
    epochRef.current++
    chatAfterRef.current = 0
    renderedSeqRef.current.clear()
    setTurns([])
  }, [])

  const step = useCallback(async () => {
    await api.step()
    void refresh()
  }, [refresh])

  const listen = useCallback(async () => {
    setIsListening(true)
    try {
      const r = await api.listen()
      reportRef.current(true)
      if (r.error) throw new Error(r.error)
      if (!r.result?.heard) pushTurns({ role: 'novi', text: '(nothing heard)' })
    } catch {
      pushTurns({ role: 'novi', text: '(Listen needs real sensing — start the brain with --camera real)' })
      reportRef.current(false)
    } finally {
      setIsListening(false)
    }
    void refresh()
  }, [pushTurns, refresh])

  const notice = useCallback((text: string) => pushTurns({ role: 'novi', text }), [pushTurns])

  usePoll(refresh, CHAT_POLL_MS)
  return { turns, streaming, isStreaming, isListening, send, refresh, clear, step, listen, notice }
}
