import { useEffect, useRef } from 'react'

/**
 * Run a callback immediately, then on a fixed interval. The callback is kept in
 * a ref so callers never re-subscribe when it changes identity.
 *
 * When `enabled` is false no timer runs and no fetch fires, so pages that do
 * not need a feature stop its network/CPU cost on unmount-or-hide (plan 02,
 * page-local polling). Re-enabling resumes immediately.
 *
 * Stability discipline (memory/CPU):
 * - ticks never overlap: while one invocation is still in flight, interval
 *   ticks are skipped instead of stacking concurrent fetches behind a slow
 *   server (each piled-up response allocates a full JSON payload + React
 *   state that then queues behind the others);
 * - ticks are skipped while the tab is hidden, so a background tab stops
 *   allocating poll payloads and re-renders entirely. Only the explicit
 *   `'hidden'` state skips — prerender/test environments keep polling.
 */
export function usePoll(
  callback: () => void | Promise<void>,
  intervalMs: number,
  enabled = true,
): void {
  const cbRef = useRef(callback)
  cbRef.current = callback
  const inFlightRef = useRef(false)

  useEffect(() => {
    if (!enabled) return
    let cancelled = false
    const tick = () => {
      if (cancelled || inFlightRef.current) return
      if (typeof document !== 'undefined' && document.visibilityState === 'hidden') return
      inFlightRef.current = true
      let result: unknown
      try {
        result = cbRef.current()
      } catch {
        inFlightRef.current = false
        return
      }
      void Promise.resolve(result).finally(() => {
        inFlightRef.current = false
      })
    }
    tick()
    const id = setInterval(tick, intervalMs)
    return () => {
      cancelled = true
      clearInterval(id)
    }
  }, [intervalMs, enabled])
}
