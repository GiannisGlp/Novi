import { useEffect, useRef } from 'react'

/**
 * Run a callback immediately, then on a fixed interval. The callback is kept in
 * a ref so callers never re-subscribe when it changes identity.
 */
export function usePoll(callback: () => void | Promise<void>, intervalMs: number): void {
  const cbRef = useRef(callback)
  cbRef.current = callback

  useEffect(() => {
    void cbRef.current()
    const id = setInterval(() => void cbRef.current(), intervalMs)
    return () => clearInterval(id)
  }, [intervalMs])
}
