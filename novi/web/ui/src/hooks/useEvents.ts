import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../api/client'
import type { BrainEvent, EventsChunk } from '../api/types'
import { HISTORY_CAP } from './useBrainState'

export const EVENT_POLL_MS = 1200
export const SSE_RECONNECT_MS = 5000
export const MAX_EVENTS = 500

export interface EventsData {
  events: BrainEvent[]
  evHist: number[]
  refresh: () => Promise<void>
}

/**
 * Event log fed by the /api/events/stream SSE with a 1.2s poll fallback and a 5s
 * reconnect. Ports the legacy startEventStream / refreshEvents / handleEventChunk,
 * including the non-overlapping refresh guard, rendered-seq dedup, the 500-entry
 * cap and the events/sec history for the activity chart.
 */
export function useEvents(reportConnection: (ok: boolean) => void): EventsData {
  const [events, setEvents] = useState<BrainEvent[]>([])
  const [evHist, setEvHist] = useState<number[]>([])
  const afterRef = useRef(0)
  const renderedSeqRef = useRef(new Set<number>())
  const refreshingRef = useRef(false)
  const reportRef = useRef(reportConnection)
  reportRef.current = reportConnection

  const applyChunk = useCallback((chunk: EventsChunk) => {
    afterRef.current = chunk.after
    if (chunk.events && chunk.events.length) {
      const fresh = chunk.events.filter((it) => it.seq == null || !renderedSeqRef.current.has(it.seq))
      for (const it of fresh) if (it.seq != null) renderedSeqRef.current.add(it.seq)
      if (fresh.length) setEvents((prev) => [...prev, ...fresh].slice(-MAX_EVENTS))
    }
    setEvHist((h) => [...h, chunk.events?.length ?? 0].slice(-HISTORY_CAP))
  }, [])

  const refresh = useCallback(async () => {
    if (refreshingRef.current) return
    refreshingRef.current = true
    try {
      const r = await api.events(afterRef.current)
      reportRef.current(true)
      applyChunk(r)
    } catch {
      reportRef.current(false)
    } finally {
      refreshingRef.current = false
    }
  }, [applyChunk])

  useEffect(() => {
    let es: EventSource | null = null
    let pollTimer: ReturnType<typeof setInterval> | null = null
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null

    const stopPoll = () => {
      if (pollTimer) {
        clearInterval(pollTimer)
        pollTimer = null
      }
    }
    const startPoll = () => {
      if (pollTimer) return
      void refresh()
      pollTimer = setInterval(() => void refresh(), EVENT_POLL_MS)
    }
    const startSSE = () => {
      if (es) return
      try {
        es = new EventSource('/api/events/stream?after=' + afterRef.current)
        es.onopen = () => reportRef.current(true)
        es.onmessage = (e) => {
          try {
            const data = JSON.parse(e.data) as EventsChunk
            applyChunk(data)
            reportRef.current(true)
          } catch {
            /* ignore malformed chunk */
          }
        }
        es.onerror = () => {
          reportRef.current(false)
          try {
            es?.close()
          } catch {
            /* already closed */
          }
          es = null
          if (!pollTimer) {
            startPoll()
            reconnectTimer = setTimeout(() => {
              stopPoll()
              startSSE()
            }, SSE_RECONNECT_MS)
          }
        }
      } catch {
        startPoll()
      }
    }

    startSSE()
    return () => {
      try {
        es?.close()
      } catch {
        /* already closed */
      }
      es = null
      if (pollTimer) clearInterval(pollTimer)
      if (reconnectTimer) clearTimeout(reconnectTimer)
    }
  }, [applyChunk, refresh])

  return { events, evHist, refresh }
}
