import { cssVar } from './cssVars'

export interface FloorMapState {
  body?: { x_m?: number; y_m?: number; heading_deg?: number }
  active_goal?: { target?: string } | null
}

/** Faithful port of the legacy virtual floor map (10×6m grid, goal 'G', heading triangle). */
export function drawFloorMap(
  ctx: CanvasRenderingContext2D,
  W: number,
  H: number,
  s: FloorMapState,
): void {
  ctx.clearRect(0, 0, W, H)
  ctx.fillStyle = cssVar('--panel-2') || '#1a212e'
  ctx.fillRect(0, 0, W, H)
  const grid = cssVar('--border') || '#232c3d'
  ctx.strokeStyle = grid
  ctx.lineWidth = 1
  const world = 10
  const px = W / world
  const py = H / 6
  for (let i = 1; i < world; i++) {
    ctx.beginPath()
    ctx.moveTo(i * px, 0)
    ctx.lineTo(i * px, H)
    ctx.stroke()
  }
  for (let i = 1; i < 6; i++) {
    ctx.beginPath()
    ctx.moveTo(0, i * py)
    ctx.lineTo(W, i * py)
    ctx.stroke()
  }
  ctx.font = '9px ' + cssVar('--mono')
  ctx.fillStyle = cssVar('--text-mute') || '#6b7a90'
  ctx.fillText('0', 2, H - 4)
  ctx.fillText(world + 'm', W - 28, H - 4)
  ctx.fillText('6m', 2, 12)

  const pos = s.body || {}
  const bx = pos.x_m || 0
  const by = pos.y_m || 0
  const goal = s.active_goal || {}
  let tx = 0
  let ty = 0
  const m = /([-+]?\d+(?:\.\d+)?)\s*,\s*([-+]?\d+(?:\.\d+)?)/.exec(goal.target || '')
  if (m) {
    tx = parseFloat(m[1])
    ty = parseFloat(m[2])
  }
  const cx = (v: number) => Math.max(3, Math.min(W - 3, v * px))
  const cy = (v: number) => Math.max(3, Math.min(H - 3, H - v * py))

  ctx.strokeStyle = cssVar('--warn') || '#e0b34a'
  ctx.lineWidth = 2
  ctx.beginPath()
  ctx.arc(cx(tx), cy(ty), 6, 0, 2 * Math.PI)
  ctx.stroke()
  ctx.fillStyle = cssVar('--warn') || '#e0b34a'
  ctx.font = 'bold 9px ' + cssVar('--mono')
  ctx.textAlign = 'center'
  ctx.fillText('G', cx(tx), cy(ty) + 3)
  ctx.textAlign = 'left'
  ctx.fillStyle = cssVar('--text-mute') || '#6b7a90'
  ctx.fillRect(cx(0) - 1.5, cy(0) - 1.5, 3, 3)

  const hdg = (pos.heading_deg != null ? pos.heading_deg : 0) * (Math.PI / 180)
  const nx = cx(bx)
  const ny = cy(by)
  ctx.fillStyle = cssVar('--accent') || '#34d6d0'
  ctx.beginPath()
  ctx.moveTo(nx + Math.cos(hdg) * 8, ny - Math.sin(hdg) * 8)
  ctx.lineTo(nx + Math.cos(hdg + 2.4) * 5, ny - Math.sin(hdg + 2.4) * 5)
  ctx.lineTo(nx + Math.cos(hdg - 2.4) * 5, ny - Math.sin(hdg - 2.4) * 5)
  ctx.closePath()
  ctx.fill()
  ctx.fillStyle = cssVar('--accent') || '#34d6d0'
  ctx.fillText('novi', nx + 8, ny + 14)
}
