import { PULSE_COLORS, canvasColors } from './cssVars'

/**
 * Mutable animation state for the cognitive pulse. `beat` decays 0.05/frame
 * inside drawPulseFrame, mirroring the legacy console's requestAnimationFrame
 * loop; the caller persists it across frames via a ref.
 */
export interface PulseState {
  beat: number
  affect: number
  confidence: number
}

export function drawPulseFrame(
  ctx: CanvasRenderingContext2D,
  state: PulseState,
  t: number,
): void {
  const { accent, accent2, border, mute, mono } = canvasColors()
  const W = 240
  const H = 240
  const cx = W / 2
  const cy = H / 2
  ctx.clearRect(0, 0, W, H)

  // outer ring: rotating attention arc
  const R1 = 100
  ctx.strokeStyle = border
  ctx.lineWidth = 1
  ctx.beginPath()
  ctx.arc(cx, cy, R1, 0, 2 * Math.PI)
  ctx.stroke()
  const arcLen = 0.5 + 0.4 * Math.sin(t * 0.6)
  const a0 = t * 0.5
  const focusColor = PULSE_COLORS[Math.floor(t * 0.3) % PULSE_COLORS.length]
  ctx.strokeStyle = focusColor
  ctx.lineWidth = 3
  ctx.lineCap = 'round'
  ctx.beginPath()
  ctx.arc(cx, cy, R1, a0, a0 + arcLen * 2 * Math.PI)
  ctx.stroke()

  // mid ring: affect (warm/cool)
  const R2 = 78
  ctx.strokeStyle = border
  ctx.lineWidth = 1
  ctx.beginPath()
  ctx.arc(cx, cy, R2, 0, 2 * Math.PI)
  ctx.stroke()
  const soul = canvasColors().soul
  const affectAngle = (state.affect * 0.9 + 0.05) * 2 * Math.PI
  ctx.strokeStyle = soul
  ctx.lineWidth = 2.5
  ctx.lineCap = 'round'
  ctx.beginPath()
  ctx.arc(cx, cy, R2, -Math.PI / 2, -Math.PI / 2 + affectAngle)
  ctx.stroke()

  // core: pulsing circle with radial gradient
  const beatScale = 1 + 0.12 * Math.max(0, state.beat)
  state.beat = Math.max(0, state.beat - 0.05)
  const Rc = 30 * beatScale
  const grad = ctx.createRadialGradient(cx, cy, 2, cx, cy, Rc)
  grad.addColorStop(0, accent2)
  grad.addColorStop(1, accent)
  ctx.fillStyle = grad
  ctx.beginPath()
  ctx.arc(cx, cy, Rc, 0, 2 * Math.PI)
  ctx.fill()

  // confidence ring around core
  ctx.strokeStyle = accent
  ctx.lineWidth = 2
  ctx.lineCap = 'round'
  ctx.beginPath()
  ctx.arc(cx, cy, Rc + 6, -Math.PI / 2, -Math.PI / 2 + state.confidence * 2 * Math.PI)
  ctx.stroke()

  // labels
  ctx.fillStyle = mute
  ctx.textAlign = 'center'
  ctx.font = '8px ' + mono
  ctx.fillText('ATTENTION', cx, cy - R1 - 8)
  ctx.fillText('AFFECT', cx, cy - R2 - 8)
}
