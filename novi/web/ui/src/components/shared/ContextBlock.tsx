import type { ContextResponse } from '../../api/types'
import { KV } from './KV'

export interface ContextBlockProps {
  response: ContextResponse | null
}

function chipClass(status: string): string {
  const st = status.toLowerCase()
  if (st.includes('contradict')) return 'contradicted'
  if (st.includes('predict')) return 'predicted'
  return 'observed'
}

/** World-model context — visible entities, relations, uncertainty — from refreshContext(). */
export function ContextBlock({ response }: ContextBlockProps) {
  if (!response) return <span className="muted">…</span>
  const pkg = response.package ?? {}
  const vis = pkg.visible_entities ?? pkg.entities ?? []
  const rels = pkg.relations ?? pkg.relationships ?? []
  const unc = pkg.uncertainty ?? pkg.contradictions ?? []
  return (
    <>
      {vis.length > 0 ? (
        <div className="ctx-section">
          <div className="h">Visible entities</div>
          <div className="entity-chips">
            {vis.slice(0, 12).map((e, i) => {
              const ref =
                typeof e === 'string' ? e : String(e.entity_ref || e.id || e.ref || '?')
              const st = typeof e === 'string' ? 'observed' : (e.epistemic_status || e.status || 'observed').toLowerCase()
              return (
                <span key={i} className={'entity-chip ' + chipClass(st)} title={st}>
                  {ref} · {st}
                </span>
              )
            })}
          </div>
        </div>
      ) : (
        <div className="muted">No context yet — tell Novi something about the world.</div>
      )}
      {rels.length > 0 && (
        <div className="ctx-section">
          <div className="h">Relations</div>
          {rels.slice(0, 4).map((r, i) => (
            <KV
              key={i}
              k={r.subject || r.a || ''}
              v={`${r.predicate || r.relation || ''} ${r.object || r.b || ''}`}
            />
          ))}
        </div>
      )}
      {unc.length > 0 && (
        <div className="ctx-section">
          <div className="h">Uncertainty</div>
          {unc.slice(0, 3).map((u, i) => (
            <KV key={i} k={u.entity || u.ref || ''} v={u.reason || u.status || ''} />
          ))}
        </div>
      )}
      {response.cycle != null && <div className="muted" style={{ marginTop: 6 }}>cycle {response.cycle}</div>}
    </>
  )
}
