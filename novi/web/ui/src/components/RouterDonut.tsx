import { useEffect, useRef } from 'react'
import { drawDonutChart, type DonutSlice } from '../canvas/donutChart'
import { useThemeTick } from '../hooks/useThemeTick'

export interface RouterDonutProps {
  data: DonutSlice[]
}

const W = 150
const H = 150

/** Router routing-decisions donut, redrawn on data + theme change. */
export function RouterDonut({ data }: RouterDonutProps) {
  const ref = useRef<HTMLCanvasElement>(null)
  const themeTick = useThemeTick()
  const dataRef = useRef(data)
  dataRef.current = data

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
    drawDonutChart(ctx, W, H, dataRef.current, { label: 'routes' })
  }, [data, themeTick])

  return <canvas ref={ref} className="donut-canvas" width={W} height={H} aria-label="Routing decisions donut" />
}
