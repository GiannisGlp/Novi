import type { ReactNode } from 'react'

export interface SectionProps {
  eyebrow: string
  title: string
  desc?: string
  children?: ReactNode
}

/** Page header — eyebrow + title + description, used at the top of every page. */
export function Section({ eyebrow, title, desc, children }: SectionProps) {
  return (
    <div className="page-head">
      <div>
        <div className="eyebrow">{eyebrow}</div>
        <h2>{title}</h2>
      </div>
      {desc && <div className="desc">{desc}</div>}
      {children}
    </div>
  )
}
