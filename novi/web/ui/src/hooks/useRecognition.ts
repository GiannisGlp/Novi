import { useCallback, useRef, useState } from 'react'
import { api } from '../api/client'
import type { RecognitionList } from '../api/types'
import { usePoll } from './usePoll'

export const RECOGNITION_POLL_MS = 3000

/**
 * Polls /api/recognition enrollments. The legacy console only refreshed on
 * navigation to the perception page; the SPA polls while mounted instead so the
 * page never shows stale data.
 */
export function useRecognition(reportConnection: (ok: boolean) => void): {
  recognition: RecognitionList | null
  refresh: () => Promise<void>
} {
  const [recognition, setRecognition] = useState<RecognitionList | null>(null)
  const reportRef = useRef(reportConnection)
  reportRef.current = reportConnection

  const refresh = useCallback(async () => {
    try {
      const d = await api.recognition()
      reportRef.current(true)
      setRecognition(d)
    } catch {
      reportRef.current(false)
    }
  }, [])

  usePoll(refresh, RECOGNITION_POLL_MS)
  return { recognition, refresh }
}
