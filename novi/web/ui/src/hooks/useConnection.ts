import { useCallback, useState } from 'react'

/**
 * Whether the browser can currently reach the Novi server. Any successful fetch
 * reports true; any failure reports false. Drives the reconnect banner + statusbar.
 */
export function useConnection(): { connected: boolean; reportConnection: (ok: boolean) => void } {
  const [connected, setConnected] = useState(true)
  const reportConnection = useCallback((ok: boolean) => setConnected(ok), [])
  return { connected, reportConnection }
}
