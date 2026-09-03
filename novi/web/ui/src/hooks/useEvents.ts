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

export interface EventsOptions {
  /** When false, no SSE connection or poll timer runs (page-local polling). */
  enabled?: boolean
}

/**
 * Cursor-based event deduplication in O(1) memory (plan 02, §3.2).
 *
 * The server delivers events in sequence order, and the rendered list is an
 * append-only tail window — so the monotonic high-water mark is the complete
 * dedup state. Anything at or below the cursor was already rendered (duplicate)
 * or is too old to insert into the tail (stale); both are dropped. No Set, no
 * growth: memory is O(1) however many events flow through.
 */
export class EventDedup {
  private cursor = 0

  get lastSeq(): number {
    return this.cursor
  }

  /** True when this sequence has not been rendered yet. */
  isFresh(seq: number | null | undefined): boolean {
    if (seq == null) return true
    return seq > this.cursor
  }

  remember(seq: number): void {
    if (seq > this.cursor) this.cursor = seq
  }

  /** Resync after a server gap/epoch signal: adopt the fresh snapshot. */
  resync(cursor: number): void {
    this.cursor = cursor
  }
}

/**
 * Event log fed by the /api/events/stream SSE with a 1.2s poll fallback and a 5s
 * reconnect. Ports the legacy startEventStream / refreshEvents / handleEventChunk,
 * including the non-overlapping refresh guard, the 500-entry cap and the
 * events/sec history for the activity chart.
 *
 * Memory discipline (plan 02): deduplication is a cursor-based high-water
 * mark in O(1) memory — no per-sequence Set. A server `gap` signal (cursor
 * fell outside retention) or an `epoch` change (server restarted, sequence
 * numbers reset) clears the local window and resyncs from the fresh snapshot.
 */
export function useEvents(reportConnection: (ok: boolean) => void, opts?: EventsOptions): EventsData {
  const enabled = opts?.enabled ?? true
  const [events, setEvents] = useState<BrainEvent[]>([])
  const [evHist, setEvHist] = useState<number[]>([])
  const afterRef = useRef(0)
  const dedupRef = useRef(new EventDedup())
  const refreshingRef = useRef(false)
  const reportRef = useRef(reportConnection)
  reportRef.current = reportConnection

  const epochRef = useRef<string | null>(null)

  const applyChunk = useCallback((chunk: EventsChunk) => {
    const dedup = dedupRef.current
    const epochChanged = chunk.epoch != null && epochRef.current != null && chunk.epoch !== epochRef.current
    if (chunk.epoch != null) epochRef.current = chunk.epoch
    if (chunk.gap || epochChanged) {
      // Our cursor fell outside server retention, or the server restarted
      // (sequence numbers reset): drop the stale window and resync from this
      // fresh bounded snapshot instead of assuming continuity.
      const snap = (chunk.events ?? []).slice(-MAX_EVENTS)
      afterRef.current = chunk.after
      dedup.resync(chunk.after)
      setEvents(snap)
      setEvHist((h) => [...h, chunk.events?.length ?? 0].slice(-HISTORY_CAP))
      return
    }
    afterRef.current = chunk.after
    if (chunk.events && chunk.events.length) {
      const fresh = chunk.events.filter((it) => dedup.isFresh(it.seq))
      for (const it of fresh) if (it.seq != null) dedup.remember(it.seq)
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
    if (!enabled) return
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
  }, [applyChunk, refresh, enabled])

  return { events, evHist, refresh }
}
