import { useCallback, useRef, useState } from 'react'
import { api } from '../api/client'
import type { AttentionSnapshot } from '../api/types'
import { usePoll } from './usePoll'

export const ATTENTION_POLL_MS = 1100

/** 1.1s poll of /api/attention; keeps the last snapshot on failure. */
export function useAttention(reportConnection: (ok: boolean) => void): {
  snapshot: AttentionSnapshot | null
  refresh: () => Promise<void>
} {
  const [snapshot, setSnapshot] = useState<AttentionSnapshot | null>(null)
  const reportRef = useRef(reportConnection)
  reportRef.current = reportConnection

  const refresh = useCallback(async () => {
    try {
      const d = await api.attention()
      reportRef.current(true)
      setSnapshot(d)
    } catch {
      reportRef.current(false)
    }
  }, [])

  usePoll(refresh, ATTENTION_POLL_MS)
  return { snapshot, refresh }
}
