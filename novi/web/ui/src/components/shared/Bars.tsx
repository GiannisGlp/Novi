export interface BarsProps {
  obj?: Record<string, number>
  cls?: string
}

/** Horizontal value bars for a flat dimension map (traits, affect). */
export function Bars({ obj, cls }: BarsProps) {
  return (
    <div className="bars">
      {Object.entries(obj ?? {}).map(([k, v]) => {
        const pct = Math.max(0, Math.min(1, Number(v) || 0)) * 100
        return (
          <div key={k} className={'bar-row ' + (cls ?? '')}>
            <span className="bl" title={k}>
              {k}
            </span>
            <span className="bt">
              <span className="bf" style={{ width: pct.toFixed(1) + '%' }} />
            </span>
            <span className="bv">{(Number(v) || 0).toFixed(2)}</span>
          </div>
        )
      })}
    </div>
  )
}
