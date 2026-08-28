export function cssVar(name: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim()
}

export const PULSE_COLORS = [
  '#34d6d0',
  '#f5b868',
  '#4cc38a',
  '#7be8e3',
  '#e0b34a',
  '#ff6b6b',
  '#88c0d0',
]

export function hashStr(s: string): number {
  let h = 0
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0
  return Math.abs(h)
}

/** Resolved CSS palette a canvas draw needs, read via cssVar on each frame. */
export function canvasColors(): {
  border: string
  mute: string
  mono: string
  text: string
  accent: string
  accent2: string
  soul: string
  panel2: string
} {
  return {
    border: cssVar('--border') || '#232c3d',
    mute: cssVar('--text-mute') || '#6b7a90',
    mono: cssVar('--mono') || 'monospace',
    text: cssVar('--text') || '#e4eaf3',
    accent: cssVar('--accent') || '#34d6d0',
    accent2: cssVar('--accent-2') || '#7be8e3',
    soul: cssVar('--soul') || '#f5b868',
    panel2: cssVar('--panel-2') || '#1a212e',
  }
}
