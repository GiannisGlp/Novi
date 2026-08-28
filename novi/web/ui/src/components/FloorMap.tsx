import { useEffect, useRef } from 'react'
import { drawFloorMap, type FloorMapState } from '../canvas/floorMap'
import { useThemeTick } from '../hooks/useThemeTick'

export interface FloorMapProps {
  state: FloorMapState
}

const W = 340
const H = 170

/** Virtual 10×6m floor map with goal marker and heading triangle, redrawn on state + theme change. */
export function FloorMap({ state }: FloorMapProps) {
  const ref = useRef<HTMLCanvasElement>(null)
  const themeTick = useThemeTick()
  const stateRef = useRef(state)
  stateRef.current = state

  useEffect(() => {
    const cv = ref.current
    if (!cv) return
    const ctx = cv.getContext('2d')
    if (!ctx) return
    drawFloorMap(ctx, W, H, stateRef.current)
  }, [state, themeTick])

  return <canvas ref={ref} width={W} height={H} aria-label="Virtual floor map" />
}
