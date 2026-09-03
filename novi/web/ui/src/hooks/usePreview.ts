import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../api/client'
import type { PreviewFrame } from '../api/types'
import { usePoll } from './usePoll'

export const PREVIEW_POLL_MS = 300
const HIDE_AFTER_MISSES = 3

/**
 * Signature of every metadata field the camera/perception pages render.
 * The image bytes are compared separately with `===` (a memcmp with no
 * allocation) so identical-frame detection never copies the base64 payload.
 */
export function frameMetaSignature(d: PreviewFrame): string {
  return JSON.stringify([
    d.camera_health ?? null,
    d.stale ?? null,
    d.person ?? null,
    d.tier ?? null,
    d.place ?? null,
    d.detector_backend ?? null,
    d.faces_backend ?? null,
    d.preview_omitted_over_budget ?? null,
    d.detections ?? null,
    d.face ?? null,
    d.tracks ?? null,
  ])
}

export interface PreviewData {
  frame: PreviewFrame | null
  showImage: boolean
  refresh: () => Promise<void>
}

/**
 * 300ms poll of /api/preview. Ports the legacy refreshPreview(): keeps the last
 * frame while the server is busy, hides the image after 3 consecutive empty polls,
 * and does not report disconnection (a busy camera is not a lost server).
 *
 * Latest-frame semantics (plan 02, Phase 5): only the newest result may update
 * UI state; a stale in-flight request is aborted when a new one starts or the
 * hook disables/unmounts, so slow responses can never queue behind each other.
 */
export function usePreview(
  reportConnection: (ok: boolean) => void,
  opts?: { enabled?: boolean },
): PreviewData {
  const enabled = opts?.enabled ?? true
  const [frame, setFrame] = useState<PreviewFrame | null>(null)
  const [showImage, setShowImage] = useState(false)
  const refreshingRef = useRef(false)
  const missesRef = useRef(0)
  const requestIdRef = useRef(0)
  const abortRef = useRef<AbortController | null>(null)
  const lastImgRef = useRef<string | null | undefined>(undefined)
  const lastMetaRef = useRef<string | null>(null)
  const reportRef = useRef(reportConnection)
  reportRef.current = reportConnection

  const refresh = useCallback(async () => {
    if (refreshingRef.current) return
    refreshingRef.current = true
    abortRef.current?.abort()
    const ctrl = new AbortController()
    abortRef.current = ctrl
    const id = requestIdRef.current + 1
    requestIdRef.current = id
    try {
      const d = await api.preview(ctrl.signal)
      if (ctrl.signal.aborted || id !== requestIdRef.current) return
      reportRef.current(true)
      // Skip identical frames: with no camera (or a static scene) the server
      // returns an equivalent payload every 300ms, and each setFrame allocates
      // a new state object + re-renders the camera/perception pages (including
      // re-decoding the <img>). The image is compared by value with no copy
      // and metadata via a small signature, so a skipped update renders
      // pixel-identically to applying it. Miss/show bookkeeping still runs on
      // every poll so the hide-after-misses logic keeps working.
      const metaSig = frameMetaSignature(d)
      const same = d.image_data_url === lastImgRef.current && metaSig === lastMetaRef.current
      lastImgRef.current = d.image_data_url
      lastMetaRef.current = metaSig
      if (!same) setFrame(d)
      if (d.image_data_url) {
        missesRef.current = 0
        setShowImage(true)
      } else {
        missesRef.current += 1
        if (missesRef.current > HIDE_AFTER_MISSES) setShowImage(false)
      }
    } catch (err) {
      // Aborts and offline/busy servers both keep the last frame; only real
      // failures are ignored silently, an abort is not an error.
      if (err instanceof DOMException && err.name === 'AbortError') return
      // server busy or offline — keep the last frame
    } finally {
      if (abortRef.current === ctrl) abortRef.current = null
      refreshingRef.current = false
    }
  }, [])

  usePoll(refresh, PREVIEW_POLL_MS, enabled)

  // Navigating away aborts the in-flight frame so no late response can update
  // unmounted state or retain its closure.
  useEffect(() => {
    if (!enabled) abortRef.current?.abort()
  }, [enabled])
  useEffect(() => () => abortRef.current?.abort(), [])

  return { frame, showImage, refresh }
}
