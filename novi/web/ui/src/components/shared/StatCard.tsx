import type { ReactNode } from 'react'

export interface StatCardProps {
  k: string
  v: ReactNode
  s: string
  tone?: 'good' | 'warn' | 'bad'
}

/** Statgrid cell — a big value over a caption, with an optional semantic tone. */
export function StatCard({ k, v, s, tone }: StatCardProps) {
  return (
    <div className={'statcard' + (tone ? ' ' + tone : '')}>
      <span className="k">{k}</span>
      <span className="v">{v}</span>
      <span className="s">{s}</span>
    </div>
  )
}
