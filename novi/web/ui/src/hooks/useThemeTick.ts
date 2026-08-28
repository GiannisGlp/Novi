import { useEffect, useState } from 'react'

/**
 * Increments each time `data-theme` changes on <html>, so canvas wrappers that
 * resolve CSS vars once per draw can re-render when the theme switches. The
 * rAF-driven pulse re-reads vars every frame and does not need this.
 */
export function useThemeTick(): number {
  const [tick, setTick] = useState(0)
  useEffect(() => {
    const mo = new MutationObserver(() => setTick((t) => t + 1))
    mo.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['data-theme'],
    })
    return () => mo.disconnect()
  }, [])
  return tick
}
