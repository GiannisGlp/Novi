import type { ReactNode } from 'react'

export interface PanelProps {
  title: string
  right?: ReactNode
  className?: string
  children?: ReactNode
}

/** Panel with a header bar (`phbar`) and a body — the core layout unit of every page. */
export function Panel({ title, right, className, children }: PanelProps) {
  return (
    <div className={'panel' + (className ? ' ' + className : '')}>
      <div className="phbar">
        <h3>{title}</h3>
        {right}
      </div>
      <div className="body">{children}</div>
    </div>
  )
}
