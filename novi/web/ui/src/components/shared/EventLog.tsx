import { useEffect, useMemo, useRef, useState } from 'react'
import type { BrainEvent } from '../../api/types'

function fmtTime(ts?: number): string {
  if (!ts) return ''
  const d = new Date(ts * 1000)
  const p = (n: number) => String(n).padStart(2, '0')
  return p(d.getHours()) + ':' + p(d.getMinutes()) + ':' + p(d.getSeconds())
}

function stripJson(ev: Record<string, unknown>): Record<string, unknown> {
  const c = { ...ev }
  delete c.event_type
  delete c.cycle
  delete c.cycle_id
  return c
}

/** Filterable event log, ported from applyEventFilter + the legacy .ev rows. */
export function EventLog({ events }: { events: BrainEvent[] }) {
  const [filter, setFilter] = useState('')
  const logRef = useRef<HTMLDivElement>(null)

  const q = filter.trim().toLowerCase()
  const visible = useMemo(() => {
    if (!q) return events
    return events.filter((it) => {
      const kind = (it.event?.event_type ?? '').toLowerCase()
      const cyc = String(it.event?.cycle ?? '').toLowerCase()
      return kind.includes(q) || cyc.includes(q) || ('c' + cyc).includes(q)
    })
  }, [events, q])

  useEffect(() => {
    const el = logRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [visible.length])

  return (
    <>
      <div className="evfilter">
        <input
          placeholder="filter by event kind or cycle, e.g. person or c12"
          aria-label="Filter events"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
        />
        <span className="count">{visible.length} shown</span>
      </div>
      <div className="evlog" ref={logRef} aria-live="polite">
        {visible.length === 0 && <span className="muted">waiting for events…</span>}
        {visible.map((it, i) => {
          const ev = it.event ?? {}
          return (
            <div
              key={it.seq ?? i}
              className="ev"
              data-kind={ev.event_type ?? ''}
              data-cycle={ev.cycle ?? ''}
            >
              <span className="t">{fmtTime(it.ts)}</span>
              <span className="e">
                <span className="ec">{ev.cycle != null ? 'c' + ev.cycle : ''}</span>{' '}
                <span className="ek">{ev.event_type ?? 'event'}</span>{' '}
                {JSON.stringify(stripJson(ev)).slice(0, 180)}
              </span>
            </div>
          )
        })}
      </div>
    </>
  )
}
