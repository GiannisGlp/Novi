import { useCallback, useRef, useState } from 'react'
import { api } from '../api/client'
import type { PreviewFrame } from '../api/types'
import { usePoll } from './usePoll'

export const PREVIEW_POLL_MS = 300
const HIDE_AFTER_MISSES = 3

export interface PreviewData {
  frame: PreviewFrame | null
  showImage: boolean
  refresh: () => Promise<void>
}

/**
 * 300ms poll of /api/preview. Ports the legacy refreshPreview(): keeps the last
 * frame while the server is busy, hides the image after 3 consecutive empty polls,
 * and does not report disconnection (a busy camera is not a lost server).
 */
export function usePreview(reportConnection: (ok: boolean) => void): PreviewData {
  const [frame, setFrame] = useState<PreviewFrame | null>(null)
  const [showImage, setShowImage] = useState(false)
  const refreshingRef = useRef(false)
  const missesRef = useRef(0)
  const reportRef = useRef(reportConnection)
  reportRef.current = reportConnection

  const refresh = useCallback(async () => {
    if (refreshingRef.current) return
    refreshingRef.current = true
    try {
      const d = await api.preview()
      reportRef.current(true)
      setFrame(d)
      if (d.image_data_url) {
        missesRef.current = 0
        setShowImage(true)
      } else {
        missesRef.current += 1
        if (missesRef.current > HIDE_AFTER_MISSES) setShowImage(false)
      }
    } catch {
      // server busy or offline — keep the last frame
    } finally {
      refreshingRef.current = false
    }
  }, [])

  usePoll(refresh, PREVIEW_POLL_MS)
  return { frame, showImage, refresh }
}
