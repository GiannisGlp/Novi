import { useEffect, useRef } from 'react'

const THEMES = ['dark', 'light', 'nord'] as const

export interface TopBarProps {
  runId?: string | null
  cycle?: number | null
  health?: string | null
  identity?: string | null
  theme: string
  onThemeChange: (theme: string) => void
  models: readonly string[]
  model: string | null
  onModelChange: (model: string) => void
  chatOpen: boolean
  onToggleChat: () => void
  onToggleNav?: () => void
  navOpen?: boolean
}

/** Top header: brand mark, live chips, theme + model controls, chat toggle. */
export function TopBar({
  runId = null,
  cycle = null,
  health = null,
  identity = null,
  theme,
  onThemeChange,
  models,
  model,
  onModelChange,
  chatOpen,
  onToggleChat,
  onToggleNav,
  navOpen = false,
}: TopBarProps) {
  // One "core beat" pulse per cognitive cycle (matches the legacy console).
  const coreRef = useRef<HTMLSpanElement>(null)
  const lastCycleRef = useRef<number | null>(null)
  useEffect(() => {
    if (cycle === null || cycle === lastCycleRef.current) return
    lastCycleRef.current = cycle
    const c = coreRef.current
    if (c) {
      c.classList.remove('beat')
      void c.offsetWidth
      c.classList.add('beat')
    }
  }, [cycle])

  return (
    <header className="topbar">
      <button
        id="navToggle"
        className="iconbtn"
        title="Toggle navigation"
        aria-label="Toggle navigation"
        aria-expanded={navOpen}
        onClick={onToggleNav}
      >
        ☰
      </button>
      <div className="brand">
        <div className="wordmark">
          <span>N</span>
          <span className="wm-o" ref={coreRef} aria-hidden="true"></span>
          <span>VI</span>
        </div>
        <div className="sub">brain console</div>
      </div>
      <span className="chip" id="runid" title="run id">
        {runId ?? '…'}
      </span>
      <span className="chip">
        cycle <b id="cycle">{cycle ?? 0}</b>
      </span>
      <span className={'chip health-' + (health ?? 'UNKNOWN')} id="health">
        <span className="dot"></span>
        <span id="healthText">{health ?? '—'}</span>
      </span>
      <span className="chip" id="identBadge" title="who Novi thinks you are">
        {identity ?? '—'}
      </span>
      <div className="spacer"></div>
      <div className="hgrp">
        <div className="seg" role="group" aria-label="Theme">
          {THEMES.map((t) => (
            <button
              key={t}
              data-theme-set={t}
              aria-pressed={theme === t}
              onClick={() => onThemeChange(t)}
            >
              {t === 'dark' ? 'Dark' : t === 'light' ? 'Light' : 'Nord'}
            </button>
          ))}
        </div>
        <select
          id="modelSelect"
          title="chat/reasoning model"
          aria-label="Chat model"
          value={model ?? ''}
          onChange={(e) => onModelChange(e.target.value)}
        >
          {model === null && <option value="" disabled>…</option>}
          {models.map((m) => (
            <option key={m} value={m}>
              {m}
            </option>
          ))}
        </select>
        <button
          id="chatToggle"
          className={'iconbtn' + (chatOpen ? ' active' : '')}
          title="Toggle conversation"
          aria-label="Toggle conversation"
          aria-pressed={chatOpen}
          onClick={onToggleChat}
        >
          💬
        </button>
      </div>
    </header>
  )
}
