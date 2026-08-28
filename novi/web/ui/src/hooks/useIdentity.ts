import { useCallback, useRef, useState } from 'react'
import { api } from '../api/client'
import type { IdentityDetail } from '../api/types'
import { usePoll } from './usePoll'

export const IDENTITY_POLL_MS = 1500

/** 1.5s poll of /api/identity; keeps the last detail on failure. */
export function useIdentity(reportConnection: (ok: boolean) => void): {
  detail: IdentityDetail | null
  refresh: () => Promise<void>
} {
  const [detail, setDetail] = useState<IdentityDetail | null>(null)
  const reportRef = useRef(reportConnection)
  reportRef.current = reportConnection

  const refresh = useCallback(async () => {
    try {
      const d = await api.identity()
      reportRef.current(true)
      setDetail(d)
    } catch {
      reportRef.current(false)
    }
  }, [])

  usePoll(refresh, IDENTITY_POLL_MS)
  return { detail, refresh }
}
