import { useNow } from '../hooks/useNow'

export interface StatusBarProps {
  connected?: boolean
  /** Last successful brain-state fetch (ms epoch); the "updated … ago" label ticks locally. */
  lastUpdatedAt?: number | null
  runId?: string | null
  cycle?: number | null
  memCount?: number | null
  theme?: string
}

/**
 * Bottom status strip: connection state, run/cycle, memory + theme summary.
 *
 * Owns the 1s "updated Xs ago" ticker locally so the tick re-renders only
 * this strip — it previously lived in App and re-rendered the whole tree
 * (every page, the chat drawer, all canvases) once per second.
 */
export function StatusBar({
  connected = false,
  lastUpdatedAt = null,
  runId = null,
  cycle = null,
  memCount = null,
  theme = 'dark',
}: StatusBarProps) {
  const now = useNow(1000)
  const secsAgo =
    lastUpdatedAt != null ? Math.max(0, Math.round((now - lastUpdatedAt) / 1000)) : null
  const updatedLabel = secsAgo === null ? '—' : secsAgo <= 1 ? 'just now' : `${secsAgo}s ago`

  return (
    <footer className="statusbar">
      <span className={'live' + (connected ? '' : ' off')}>
        <i></i>
        {connected ? 'live' : 'offline'}
      </span>
      <span id="sbUpdated">updated {updatedLabel}</span>
      <span>
        run <b id="sbRun">{runId ?? '—'}</b>
      </span>
      <span>
        cycle <b id="sbCycle">{cycle ?? 0}</b>
      </span>
      <span className="grow">
        mem <b id="sbMem">{memCount ?? 0}</b> · theme <b id="sbTheme">{theme}</b>
      </span>
    </footer>
  )
}
