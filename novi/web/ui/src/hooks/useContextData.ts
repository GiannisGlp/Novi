import { useCallback, useRef, useState } from 'react'
import { api } from '../api/client'
import type { ContextResponse } from '../api/types'
import { usePoll } from './usePoll'

export const CONTEXT_POLL_MS = 1100

/** 1.1s poll of /api/context; keeps the last response on failure. */
export function useContextData(
  reportConnection: (ok: boolean) => void,
  opts?: { enabled?: boolean },
): {
  response: ContextResponse | null
  refresh: () => Promise<void>
} {
  const [response, setResponse] = useState<ContextResponse | null>(null)
  const reportRef = useRef(reportConnection)
  reportRef.current = reportConnection

  const refresh = useCallback(async () => {
    try {
      const d = await api.context()
      reportRef.current(true)
      setResponse(d)
    } catch {
      reportRef.current(false)
    }
  }, [])

  usePoll(refresh, CONTEXT_POLL_MS, opts?.enabled ?? true)
  return { response, refresh }
}
