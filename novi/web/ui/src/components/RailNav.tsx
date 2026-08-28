import { NavLink } from 'react-router-dom'

export interface RailNavProps {
  open?: boolean
  onNavigate?: () => void
}

const ITEMS = [
  { to: '/overview', ic: '◉', label: 'Overview' },
  { to: '/cognition', ic: '✦', label: 'Cognition' },
  { to: '/memory', ic: '▤', label: 'Memory' },
  { to: '/knowledge', ic: '◈', label: 'Knowledge' },
  { to: '/perception', ic: '◉', label: 'Perception' },
  { to: '/camera', ic: '▣', label: 'Camera' },
  { to: '/preview', ic: '▸', label: 'Preview' },
  { to: '/events', ic: '≋', label: 'Events' },
] as const

/** Left navigation rail. On narrow screens it collapses into an overlay. */
export function RailNav({ open = false, onNavigate }: RailNavProps) {
  return (
    <nav className={'rail' + (open ? ' open' : '')} aria-label="Sections">
      <div className="rail-label">Console</div>
      {ITEMS.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          className={({ isActive }) => 'navitem' + (isActive ? ' active' : '')}
          onClick={onNavigate}
        >
          <span className="ic">{item.ic}</span>
          {item.label}
        </NavLink>
      ))}
      <div className="rail-foot">
        novi brain console
        <br />
        local · offline-first
      </div>
    </nav>
  )
}
