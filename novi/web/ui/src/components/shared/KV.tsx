import type { ReactNode } from 'react'

export interface KVProps {
  k: string
  v: ReactNode
}

/** Key/value row — the console's most common readout line. */
export function KV({ k, v }: KVProps) {
  return (
    <div className="kv">
      <span className="k">{k}</span>
      <span className="v">{v}</span>
    </div>
  )
}
