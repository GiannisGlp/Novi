import { cssVar } from './cssVars'

export interface LineSeries {
  data: number[]
  color: string
}

export interface LineChartOpts {
  xLabel?: string
}

/** Faithful port of the legacy hand-rolled line chart (grid + area + line). */
export function drawLineChart(
  ctx: CanvasRenderingContext2D,
  W: number,
  H: number,
  series: LineSeries[],
  opts?: LineChartOpts,
): void {
  const padL = 34
  const padR = 8
  const padT = 10
  const padB = 20
  ctx.clearRect(0, 0, W, H)
  const grid = cssVar('--border') || '#232c3d'
  const mute = cssVar('--text-mute') || '#6b7a90'
  const mono = cssVar('--mono') || 'monospace'
  const plotW = W - padL - padR
  const plotH = H - padT - padB

  // grid + y labels
  ctx.strokeStyle = grid
  ctx.lineWidth = 1
  ctx.font = '9px ' + mono
  ctx.fillStyle = mute
  ctx.textAlign = 'right'
  const yTicks = 4
  for (let i = 0; i <= yTicks; i++) {
    const y = padT + (plotH / yTicks) * i
    ctx.beginPath()
    ctx.moveTo(padL, y)
    ctx.lineTo(W - padR, y)
    ctx.stroke()
    ctx.fillText('', padL - 4, y + 3)
  }
  // x label
  ctx.textAlign = 'left'
  ctx.fillText(opts?.xLabel || '', padL, H - 6)

  const n = series[0]?.data.length ?? 0
  if (n < 2) return
  const all = series.flatMap((s) => s.data)
  const max = Math.max(...all, 1)
  const min = Math.min(...all, 0)
  const span = max - min || 1
  const y = (v: number) => padT + plotH - ((v - min) / span) * plotH
  const x = (i: number) => padL + (i / (n - 1)) * plotW

  for (const s of series) {
    const color = cssVar(s.color) || s.color
    // area fill
    ctx.fillStyle = color + '1c'
    ctx.beginPath()
    ctx.moveTo(x(0), padT + plotH)
    for (let i = 0; i < n; i++) ctx.lineTo(x(i), y(s.data[i]))
    ctx.lineTo(x(n - 1), padT + plotH)
    ctx.closePath()
    ctx.fill()
    // line
    ctx.strokeStyle = color
    ctx.lineWidth = 2
    ctx.beginPath()
    for (let i = 0; i < n; i++) {
      if (i === 0) ctx.moveTo(x(i), y(s.data[i]))
      else ctx.lineTo(x(i), y(s.data[i]))
    }
    ctx.stroke()
    // last point
    ctx.fillStyle = color
    ctx.beginPath()
    ctx.arc(x(n - 1), y(s.data[n - 1]), 2.5, 0, 2 * Math.PI)
    ctx.fill()
  }

  // y max/min labels
  ctx.fillStyle = mute
  ctx.textAlign = 'right'
  ctx.fillText(max.toFixed(1), padL - 4, padT + 8)
  ctx.fillText(min.toFixed(1), padL - 4, padT + plotH + 3)
}
