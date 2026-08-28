import { useCallback, useRef, useState } from 'react'
import { api } from '../api/client'
import type { RealIOStatus } from '../api/types'
import { usePoll } from './usePoll'

export const REALIO_POLL_MS = 3000

/** Polls /api/real/status for the real-I/O devices (see useRecognition). */
export function useRealIO(reportConnection: (ok: boolean) => void): {
  status: RealIOStatus | null
  refresh: () => Promise<void>
} {
  const [status, setStatus] = useState<RealIOStatus | null>(null)
  const reportRef = useRef(reportConnection)
  reportRef.current = reportConnection

  const refresh = useCallback(async () => {
    try {
      const d = await api.realStatus()
      reportRef.current(true)
      setStatus(d)
    } catch {
      reportRef.current(false)
    }
  }, [])

  usePoll(refresh, REALIO_POLL_MS)
  return { status, refresh }
}
