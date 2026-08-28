import { useEffect, useRef } from 'react'
import { drawPulseFrame, type PulseState } from '../canvas/pulse'

export interface PulseCanvasProps {
  affect: number
  confidence: number
  cycle: number | null
}

const W = 240
const H = 240

/** Cognitive pulse — a requestAnimationFrame canvas that re-reads CSS vars each frame. */
export function PulseCanvas({ affect, confidence, cycle }: PulseCanvasProps) {
  const ref = useRef<HTMLCanvasElement>(null)
  const stateRef = useRef<PulseState>({ beat: 0, affect: 0.5, confidence: 0 })
  const lastCycleRef = useRef<number | null>(null)
  const propsRef = useRef({ affect, confidence, cycle })
  propsRef.current = { affect, confidence, cycle }

  useEffect(() => {
    const cv = ref.current
    if (!cv) return
    const dpr = window.devicePixelRatio || 1
    if (cv.width !== W * dpr || cv.height !== H * dpr) {
      cv.width = W * dpr
      cv.height = H * dpr
    }
    const ctx = cv.getContext('2d')
    if (!ctx) return
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)

    let raf = 0
    const frame = () => {
      const p = propsRef.current
      const st = stateRef.current
      if (p.cycle !== lastCycleRef.current) {
        lastCycleRef.current = p.cycle
        st.beat = 1 // one pulse per cognitive cycle
      }
      st.affect = p.affect
      st.confidence = p.confidence
      drawPulseFrame(ctx, st, performance.now() / 1000)
      raf = requestAnimationFrame(frame)
    }
    raf = requestAnimationFrame(frame)
    return () => cancelAnimationFrame(raf)
  }, [])

  return (
    <canvas
      ref={ref}
      className="pulse-canvas"
      width={W}
      height={H}
      aria-label="Cognitive pulse visualization"
    />
  )
}
