import { cssVar } from './cssVars'

export interface DonutSlice {
  label: string
  value: number
  color: string
}

export interface DonutChartOpts {
  label?: string
}

/** Faithful port of the legacy router donut (arc segments + center count). */
export function drawDonutChart(
  ctx: CanvasRenderingContext2D,
  W: number,
  H: number,
  data: DonutSlice[],
  opts?: DonutChartOpts,
): void {
  ctx.clearRect(0, 0, W, H)
  const cx = W / 2
  const cy = H / 2
  const R = Math.min(W, H) / 2 - 6
  const r = R * 0.62
  const total = data.reduce((a, d) => a + d.value, 0)
  if (!total) {
    ctx.strokeStyle = cssVar('--border') || '#232c3d'
    ctx.lineWidth = 10
    ctx.beginPath()
    ctx.arc(cx, cy, R, 0, 2 * Math.PI)
    ctx.stroke()
    return
  }
  let a0 = -Math.PI / 2
  for (const d of data) {
    const a1 = a0 + (d.value / total) * 2 * Math.PI
    ctx.beginPath()
    ctx.arc(cx, cy, R, a0, a1)
    ctx.arc(cx, cy, r, a1, a0, true)
    ctx.closePath()
    ctx.fillStyle = cssVar(d.color) || d.color
    ctx.fill()
    a0 = a1
  }
  // center label
  ctx.fillStyle = cssVar('--text') || '#e4eaf3'
  ctx.textAlign = 'center'
  ctx.font = '700 20px ' + cssVar('--mono')
  ctx.fillText(String(total), cx, cy + 2)
  ctx.font = '9px ' + cssVar('--mono')
  ctx.fillStyle = cssVar('--text-mute') || '#6b7a90'
  ctx.fillText(opts?.label || 'routes', cx, cy + 14)
}
