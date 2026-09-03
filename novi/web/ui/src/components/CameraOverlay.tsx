import { useCallback, useLayoutEffect, useRef, useState, type ReactNode } from 'react'
import type { PreviewFrame } from '../api/types'
import { computeOverlayBoxes, type OverlayBox } from '../canvas/cameraOverlay'

export interface CameraOverlayProps {
  frame: PreviewFrame | null
  showImage: boolean
  badges?: ReactNode
  placeholder?: ReactNode
  showOverlay?: boolean
}

/**
 * Camera stage: letterboxed image + status badges + detection overlay. The
 * overlay boxes are absolutely-positioned divs computed by computeOverlayBoxes
 * against the stage size and the image's natural size (same math as the legacy
 * canvas-drawn overlay). Recomputes on resize and when the image loads.
 */
export function CameraOverlay({
  frame,
  showImage,
  badges,
  placeholder,
  showOverlay = true,
}: CameraOverlayProps) {
  const stageRef = useRef<HTMLDivElement>(null)
  const imgRef = useRef<HTMLImageElement>(null)
  const [boxes, setBoxes] = useState<OverlayBox[]>([])
  const [imgTick, setImgTick] = useState(0)
  // The frame arrives up to ~3x/sec; keep it in a ref so the overlay math and
  // the ResizeObserver below stay stable instead of being recreated per frame.
  const frameRef = useRef(frame)
  frameRef.current = frame

  const recompute = useCallback(() => {
    const stage = stageRef.current
    if (!stage) return
    const f = frameRef.current
    const img = imgRef.current
    const cw = stage.clientWidth
    const ch = stage.clientHeight
    const iw = img ? img.naturalWidth : 0
    const ih = img ? img.naturalHeight : 0
    setBoxes(
      computeOverlayBoxes(f?.detections, f?.face, f?.tracks, iw, ih, cw, ch),
    )
  }, [])

  // Recompute when the frame content or the loaded image changes.
  useLayoutEffect(() => {
    recompute()
  }, [frame, imgTick, recompute])

  // Observe stage resizes once for the component's lifetime.
  useLayoutEffect(() => {
    const stage = stageRef.current
    if (!stage || typeof ResizeObserver === 'undefined') return
    const ro = new ResizeObserver(() => recompute())
    ro.observe(stage)
    return () => ro.disconnect()
  }, [recompute])

  return (
    <div className="stage" id="stage" ref={stageRef}>
      {badges && <div className="badges">{badges}</div>}
      {showImage && frame?.image_data_url && (
        <img
          ref={imgRef}
          id="cam"
          alt="camera preview"
          src={frame.image_data_url}
          onLoad={() => setImgTick((t) => t + 1)}
        />
      )}
      {!showImage && <span className="placeholder" id="placeholder">{placeholder}</span>}
      {showOverlay && <div className="overlay" aria-hidden="true">
        {boxes.map((b, i) => (
          <div
            key={i}
            className={'dbox ' + b.cls}
            style={{ left: b.left, top: b.top, width: b.width, height: b.height }}
          >
            <span className="dlabel">{b.label}</span>
          </div>
        ))}
      </div>}
    </div>
  )
}
