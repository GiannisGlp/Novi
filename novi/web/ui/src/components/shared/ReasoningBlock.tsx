import type { ReasoningTrace } from '../../api/types'
import { KV } from './KV'

export interface ReasoningBlockProps {
  trace?: ReasoningTrace
  lastDetections?: string[]
}

/** Latest reasoning summary — the KV readout set from refreshState(). */
export function ReasoningBlock({ trace, lastDetections }: ReasoningBlockProps) {
  if (!trace?.conclusion) {
    return <span className="muted">Novi hasn&apos;t reasoned yet — say hello to wake it up.</span>
  }
  const dets = (trace.detections ?? lastDetections ?? []).join(', ') || 'none'
  return (
    <>
      <KV k="conclusion" v={trace.conclusion} />
      <KV k="confidence" v={(trace.confidence || 0).toFixed(2)} />
      <KV
        k="approach"
        v={
          <>
            {trace.route}
            {trace.route_reason && <> · {trace.route_reason}</>}
          </>
        }
      />
      <KV k="action" v={trace.action} />
      <KV k="rationale" v={trace.rationale || '—'} />
      <KV k="recalled" v={`${trace.recalled || 0} memories`} />
      <KV k="detections" v={dets} />
    </>
  )
}
