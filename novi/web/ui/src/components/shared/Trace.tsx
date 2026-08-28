import type { ReasoningTrace } from '../../api/types'

export interface TraceProps {
  trace?: ReasoningTrace
}

function Row({ k, v }: { k: string; v?: React.ReactNode }) {
  if (v == null) return null
  return (
    <div className="row">
      <b>{k}:</b> {v}
    </div>
  )
}

/** Collapsible reasoning trace, faithful to the legacy traceHtml() row set. */
export function Trace({ trace }: TraceProps) {
  if (!trace) return null
  const route = trace.route || 'deterministic'
  const conf = (trace.confidence || 0).toFixed(2)

  return (
    <details className="trace">
      <summary>
        cognition
        <span className="ts">
          {route} · {conf} · cycle {trace.cycle}
        </span>
      </summary>
      <div className="rows">
        <Row k="conclusion" v={trace.conclusion} />
        <div className="row">
          <b>confidence:</b> {conf}{' '}
          <b>route:</b> <span className="route">{route}</span>
          {trace.route_reason && <> &mdash; {trace.route_reason}</>}
        </div>
        <Row k="action" v={trace.action} />
        <Row k="rationale" v={trace.rationale || '—'} />
        <div className="row">
          <b>recalled:</b> {trace.recalled || 0} memories &nbsp; <b>cycle:</b> {trace.cycle}
        </div>
        {trace.detections && trace.detections.length > 0 && (
          <Row k="seeing" v={trace.detections.join(', ')} />
        )}
        {trace.inferences && trace.inferences.length > 0 && (
          <Row k="inferred" v={trace.inferences.join(' · ')} />
        )}
        {trace.hypotheses && trace.hypotheses.length > 0 && (
          <Row k="hypotheses" v={trace.hypotheses.map((x) => x.hypothesis).join(' · ')} />
        )}
        {trace.deliberation?.analysis && (
          <Row k="deliberation" v={trace.deliberation.analysis} />
        )}
        {trace.deliberation?.decision?.rationale && (
          <Row k="chose" v={trace.deliberation.decision.rationale} />
        )}
        {trace.deliberation?.rounds && trace.deliberation.rounds.length > 0 && (
          <>
            <div className="row">
              <b>deliberation rounds:</b>
            </div>
            {trace.deliberation.rounds.map((r, i) => (
              <div key={i} className="row sub">
                <b>round {r.round}:</b> {r.analysis}
                {r.evaluation && (r.analysis ? ' — ' : '')}
                {r.evaluation && <i>{r.evaluation}</i>}
                {r.confirm && <span className="route"> [confirmed]</span>}
                {r.decision?.action && <> &rarr; {r.decision.action}</>}
              </div>
            ))}
          </>
        )}
      </div>
    </details>
  )
}
