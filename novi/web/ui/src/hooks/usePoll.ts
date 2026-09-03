import { useEffect, useRef } from 'react'

/**
 * Run a callback immediately, then on a fixed interval. The callback is kept in
 * a ref so callers never re-subscribe when it changes identity.
 *
 * When `enabled` is false no timer runs and no fetch fires, so pages that do
 * not need a feature stop its network/CPU cost on unmount-or-hide (plan 02,
 * page-local polling). Re-enabling resumes immediately.
 */
export function usePoll(
  callback: () => void | Promise<void>,
  intervalMs: number,
  enabled = true,
): void {
  const cbRef = useRef(callback)
  cbRef.current = callback

  useEffect(() => {
    if (!enabled) return
    void cbRef.current()
    const id = setInterval(() => void cbRef.current(), intervalMs)
    return () => clearInterval(id)
  }, [intervalMs, enabled])
}
