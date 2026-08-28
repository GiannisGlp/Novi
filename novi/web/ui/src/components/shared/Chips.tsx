export interface Chip {
  k: string
  v: number | string
}

/** Small value chips (recognition enrollments, value dimensions). */
export function Chips({ items }: { items: Chip[] }) {
  return (
    <div className="chips">
      {items.map((it, i) => (
        <span key={i}>
          {it.k} <b>{typeof it.v === 'number' ? it.v.toFixed(2) : it.v}</b>
        </span>
      ))}
    </div>
  )
}
