import { useEffect, useRef } from 'react'
import { drawLineChart, type LineSeries } from '../canvas/lineChart'
import { useThemeTick } from '../hooks/useThemeTick'

export interface ActivityChartProps {
  series: LineSeries[]
}

/** Hand-rolled line chart (events/s, confidence, knowledge triples), redrawn on data + theme change. */
export function ActivityChart({ series }: ActivityChartProps) {
  const ref = useRef<HTMLCanvasElement>(null)
  const themeTick = useThemeTick()
  const seriesRef = useRef(series)
  seriesRef.current = series

  useEffect(() => {
    const cv = ref.current
    if (!cv) return
    const dpr = window.devicePixelRatio || 1
    const w = cv.clientWidth
    const h = cv.clientHeight
    if (cv.width !== w * dpr || cv.height !== h * dpr) {
      cv.width = w * dpr
      cv.height = h * dpr
    }
    const ctx = cv.getContext('2d')
    if (!ctx) return
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    drawLineChart(ctx, w, h, seriesRef.current, { xLabel: 'time' })
  }, [series, themeTick])

  return <canvas ref={ref} className="chart tall" aria-label="Activity chart" />
}
