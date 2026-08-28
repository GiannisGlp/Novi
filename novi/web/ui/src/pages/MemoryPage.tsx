import { useState } from 'react'
import { api } from '../api/client'
import type { BrainState, MemoryResult } from '../api/types'
import { Section } from '../components/Section'
import { KV } from '../components/shared/KV'
import { Panel } from '../components/shared/Panel'
import { SearchRow } from '../components/shared/SearchRow'

export interface MemoryPageProps {
  state: BrainState | null
}

function MemoryCard({ r }: { r: MemoryResult }) {
  return (
    <div
      style={{
        padding: '6px 9px',
        background: 'var(--panel-2)',
        border: '1px solid var(--border)',
        borderRadius: 6,
      }}
    >
      <div
        style={{
          font: '500 10.5px var(--mono)',
          color: 'var(--text-mute)',
          letterSpacing: '.3px',
        }}
      >
        {r.memory_type} · {(r.entity_refs ?? []).join(', ')} · {Number(r.confidence).toFixed(2)}
      </div>
      <div style={{ fontSize: '12.5px', color: 'var(--text)', whiteSpace: 'pre-wrap', marginTop: 2 }}>
        {(r.content ?? '').slice(0, 220)}
      </div>
    </div>
  )
}

/** Memory — search, recall engine, consolidated summaries, recent narrative. */
export function MemoryPage({ state }: MemoryPageProps) {
  const [results, setResults] = useState<MemoryResult[] | null>(null)
  const [meta, setMeta] = useState<string>('search consolidated memories by keyword.')
  const [status, setStatus] = useState<'idle' | 'searching' | 'done'>('idle')

  const search = async (q: string) => {
    if (!q.trim()) {
      setResults(null)
      setMeta('search consolidated memories by keyword.')
      setStatus('idle')
      return
    }
    setStatus('searching')
    setMeta('searching…')
    try {
      const d = await api.memory(q, 8)
      setResults(d.results ?? [])
      setMeta(
        d.results?.length
          ? ''
          : `no matches for ${q}` + (d.retrieval_state ? ` — retrieval: ${d.retrieval_state}` : ''),
      )
      setStatus('done')
    } catch {
      setResults(null)
      setMeta('search failed — is the server reachable?')
      setStatus('done')
    }
  }

  const emb = state?.memory?.embedder
  const summaries = state?.memory?.summaries ?? []
  const narrative = (state?.narrative ?? []).join(' ')

  return (
    <>
      <Section eyebrow="Memory" title="What Novi remembers" desc="Consolidated summaries, the running narrative, and searchable recall." />

      <div className="grid cols-2-1" style={{ marginBottom: 16 }}>
        <Panel title="Search">
          <SearchRow
            id="memQuery"
            placeholder="search memories, e.g. alice"
            label="Search memories"
            buttonText="Search"
            onSearch={search}
          />
          <div className="muted" style={{ marginTop: 8 }}>
            {meta}
          </div>
          {status === 'done' && results && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 8 }}>
              {results.map((r, i) => (
                <MemoryCard key={i} r={r} />
              ))}
            </div>
          )}
        </Panel>
        <Panel title="How recall works">
          {state === null ? (
            <span className="muted">…</span>
          ) : emb ? (
            <KV
              k="recall engine"
              v={
                <>
                  {emb.provider} {emb.dimension ? emb.dimension + 'd' : ''}
                  {emb.mode && <> · {emb.mode}</>}
                  {emb.available === false ? (
                    <span className="health-BAD"> [offline: {emb.error || ''}]</span>
                  ) : emb.provider === 'MiniLMEmbedding' ? (
                    <span className="health-GOOD"> [MPS]</span>
                  ) : null}
                </>
              }
            />
          ) : (
            <span className="muted">…</span>
          )}
        </Panel>
      </div>

      <div className="grid cols-2">
        <Panel title="Consolidated">
          {state === null ? (
            <span className="muted">…</span>
          ) : summaries.length > 0 ? (
            summaries.map((x, i) => (
              <KV
                key={i}
                k={(x.entity_refs ?? []).join(',') || 'summary'}
                v={x.content}
              />
            ))
          ) : (
            <span className="muted">
              Nothing consolidated yet — talk to Novi and it will start remembering.
            </span>
          )}
        </Panel>
        <Panel title="Recent Narrative">
          {state === null ? (
            <span className="muted">…</span>
          ) : narrative ? (
            <div className="v" style={{ fontWeight: 400 }}>{narrative}</div>
          ) : (
            <span className="muted">
              No story yet — once Novi experiences things, it will tell you what happened.
            </span>
          )}
        </Panel>
      </div>
    </>
  )
}
