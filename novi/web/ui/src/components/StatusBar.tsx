export interface StatusBarProps {
  connected?: boolean
  updatedAt?: string | null
  runId?: string | null
  cycle?: number | null
  memCount?: number | null
  theme?: string
}

/** Bottom status strip: connection state, run/cycle, memory + theme summary. */
export function StatusBar({
  connected = false,
  updatedAt = null,
  runId = null,
  cycle = null,
  memCount = null,
  theme = 'dark',
}: StatusBarProps) {
  return (
    <footer className="statusbar">
      <span className={'live' + (connected ? '' : ' off')}>
        <i></i>
        {connected ? 'live' : 'offline'}
      </span>
      <span id="sbUpdated">updated {updatedAt ?? '—'}</span>
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
