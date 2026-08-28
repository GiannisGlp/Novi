import { useState } from 'react'
import { api } from '../api/client'
import type { BrainState, KnowledgeTriple } from '../api/types'
import { Section } from '../components/Section'
import { KV } from '../components/shared/KV'
import { Panel } from '../components/shared/Panel'
import { SearchRow } from '../components/shared/SearchRow'
import { StatCard } from '../components/shared/StatCard'

export interface KnowledgePageProps {
  state: BrainState | null
}

function TripleRow({ t }: { t: KnowledgeTriple }) {
  const s = t.subject || t.s || ''
  const p = t.predicate || t.pred || t.relation || ''
  const o = t.object || t.o || ''
  return (
    <KV
      k={`${s} — ${p}`}
      v={o}
    />
  )
}

/** Knowledge — the graph statgrid, entity lookup, and what Novi has heard. */
export function KnowledgePage({ state }: KnowledgePageProps) {
  const [triples, setTriples] = useState<KnowledgeTriple[] | null>(null)
  const [meta, setMeta] = useState<string>('look up what Novi knows about an entity.')

  const lookup = async (q: string) => {
    if (!q.trim()) {
      setTriples(null)
      setMeta('look up what Novi knows about an entity.')
      return
    }
    setMeta('looking up…')
    try {
      const d = await api.knowledge(q, 10)
      setTriples(d.triples ?? [])
      setMeta(
        d.triples?.length
          ? ''
          : `no triples for ${q} (${d.counts?.triples || 0} total)`,
      )
    } catch {
      setTriples(null)
      setMeta('lookup failed — is the server reachable?')
    }
  }

  const kn = state?.knowledge ?? {}
  const heard = (state?.hearing ?? []).map((e) => e.event_type).join(', ') || 'silence'

  return (
    <>
      <Section eyebrow="Knowledge" title="What Novi knows" desc="The knowledge graph — entities, relations, and what's been heard." />

      <div className="statgrid">
        <StatCard k="facts" v={kn.triples || 0} s="things Novi knows" />
        <StatCard k="entities" v={kn.entities || 0} s="people &amp; things it tracks" />
        <StatCard k="conflicts" v={kn.contradicted || 0} s="contradicting beliefs" tone="warn" />
        <StatCard k="recently heard" v={heard} s="last audio events" />
      </div>

      <div className="grid cols-2">
        <Panel title="Entity Lookup">
          <SearchRow
            id="knowQuery"
            placeholder="entity, e.g. alice"
            label="Look up entity"
            buttonText="Lookup"
            onSearch={lookup}
          />
          <div className="muted" style={{ marginTop: 8 }}>
            {meta}
          </div>
          {triples && (
            <div style={{ display: 'flex', flexDirection: 'column', marginTop: 8 }}>
              {triples.map((t, i) => (
                <TripleRow key={i} t={t} />
              ))}
            </div>
          )}
        </Panel>
        <Panel title="Hearing">
          <KV k="triples" v={kn.triples || 0} />
          <KV k="entities" v={kn.entities || 0} />
          <KV k="contradicted" v={kn.contradicted || 0} />
          <KV k="memory.active" v={state?.memory?.active != null ? state?.memory?.active : '—'} />
          <KV k="heard" v={heard} />
        </Panel>
      </div>
    </>
  )
}
