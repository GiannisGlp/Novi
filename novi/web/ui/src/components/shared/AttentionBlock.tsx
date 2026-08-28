import type { AttentionSnapshot } from '../../api/types'
import { KV } from './KV'

export interface AttentionBlockProps {
  snapshot: AttentionSnapshot | null
}

/** Top attention candidates + typed situation — the refreshAttention() readout. */
export function AttentionBlock({ snapshot }: AttentionBlockProps) {
  if (!snapshot) return <span className="muted">…</span>
  const cands = snapshot.candidates ?? []
  const typed = snapshot.typed_cognition
  return (
    <>
      {typed?.situation && (
        <KV k="situation" v={typed.situation.salience || typed.situation.kind || ''} />
      )}
      {cands.length === 0 && (
        <span className="muted">Nothing is competing for attention right now.</span>
      )}
      {cands.length > 0 && (
        <div className="attn-list">
          {cands.slice(0, 6).map((a, i) => {
            const ent = a.entity_id || a.id || a.target || '?'
            const score = a.attention_score != null ? Number(a.attention_score) : a.score || 0
            const pct = Math.max(0, Math.min(1, score)) * 100
            const reason = a.reason || a.suggested_action || a.kind || ''
            return (
              <div key={i} className="attn-item">
                <div className="attn-head">
                  <b>{ent}</b>
                  <span>{Number(score).toFixed(2)}</span>
                </div>
                {reason && <div className="attn-meta">{reason}</div>}
                <div className="attn-bar">
                  <i style={{ width: pct.toFixed(1) + '%' }} />
                </div>
              </div>
            )
          })}
        </div>
      )}
      {snapshot.situations && snapshot.situations.length > 0 && (
        <div className="ctx-section">
          <div className="h">Situations</div>
          {snapshot.situations.slice(0, 3).map((s, i) => (
            <KV key={i} k={s.situation_id || s.kind || 'sit'} v={s.salience || s.kind || ''} />
          ))}
        </div>
      )}
    </>
  )
}
