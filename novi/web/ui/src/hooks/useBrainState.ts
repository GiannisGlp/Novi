import { useCallback, useRef, useState } from 'react'
import { api } from '../api/client'
import type { BrainState } from '../api/types'
import { usePoll } from './usePoll'

export const STATE_POLL_MS = 2000
export const HISTORY_CAP = 60

export interface BrainStateData {
  state: BrainState | null
  confHist: number[]
  memHist: number[]
  lastUpdatedAt: number
  refresh: () => Promise<void>
}

/**
 * 2s poll of /api/state. Ports the legacy refreshState(): keeps the last good
 * state on failure, records the confidence + triples histories for the activity
 * chart (capped at 60 samples each).
 */
export function useBrainState(reportConnection: (ok: boolean) => void): BrainStateData {
  const [state, setState] = useState<BrainState | null>(null)
  const [confHist, setConfHist] = useState<number[]>([])
  const [memHist, setMemHist] = useState<number[]>([])
  const [lastUpdatedAt, setLastUpdatedAt] = useState(0)
  const reportRef = useRef(reportConnection)
  reportRef.current = reportConnection

  const push = <T,>(arr: T[], value: T): T[] => {
    const next = [...arr, value]
    return next.length > HISTORY_CAP ? next.slice(-HISTORY_CAP) : next
  }

  const refresh = useCallback(async () => {
    try {
      const s = await api.state()
      reportRef.current(true)
      setLastUpdatedAt(Date.now())
      setState(s)
      setConfHist((h) => push(h, s.reasoning_trace?.confidence ?? 0))
      setMemHist((h) => push(h, s.knowledge?.triples ?? 0))
    } catch {
      reportRef.current(false)
    }
  }, [])

  usePoll(refresh, STATE_POLL_MS)
  return { state, confHist, memHist, lastUpdatedAt, refresh }
}
