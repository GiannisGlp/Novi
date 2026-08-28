import type { AttentionSnapshot, BrainState } from '../api/types'
import { ActivityChart } from '../components/ActivityChart'
import { PulseCanvas } from '../components/PulseCanvas'
import { Section } from '../components/Section'
import { AttentionBlock } from '../components/shared/AttentionBlock'
import { Bars } from '../components/shared/Bars'
import { Chips } from '../components/shared/Chips'
import { KV } from '../components/shared/KV'
import { Panel } from '../components/shared/Panel'
import { ReasoningBlock } from '../components/shared/ReasoningBlock'
import { StatCard } from '../components/shared/StatCard'
import { FloorMap } from '../components/FloorMap'

export interface OverviewPageProps {
  state: BrainState | null
  confHist: number[]
  memHist: number[]
  evHist: number[]
  attention: AttentionSnapshot | null
}

/** Overview — the pulse hero, statgrid, personality/attention, activity, position, reasoning. */
export function OverviewPage({ state, confHist, memHist, evHist, attention }: OverviewPageProps) {
  const rt = state?.reasoning_trace ?? {}
  const confidence = rt.confidence ?? 0

  // dominant affect dimension (max |v − 0.5|), like the legacy pulse derivation
  const aff = state?.soul?.affect ?? {}
  const affEntries = Object.entries(aff)
  let affect = 0.5
  let affectName = 'neutral'
  if (affEntries.length) {
    const top = [...affEntries].sort((a, b) => Math.abs(b[1] - 0.5) - Math.abs(a[1] - 0.5))[0]
    affectName = top[0]
    affect = Math.max(0, Math.min(1, Number(top[1]) || 0.5))
  }

  const cands = attention?.candidates ?? []
  const focus = cands.length
    ? cands[0].entity_id || cands[0].id || cands[0].target || '?'
    : state?.router?.last_route ?? '—'

  const so = state?.soul ?? {}
  const status = state?.health?.status ?? 'UNKNOWN'
  const activeMem = state?.memory?.active

  return (
    <>
      <Section
        eyebrow="Overview"
        title="How Novi is doing right now"
        desc="A live window into the mind — attention, feeling, memory, and motion."
      />

      <div className="pulse-hero">
        <div className="pulse-hero-canvas">
          <PulseCanvas affect={affect} confidence={confidence} cycle={state?.cycle ?? null} />
        </div>
        <div className="pulse-hero-side">
          <div className="pulse-eyebrow">Cognitive Pulse</div>
          <div className="pulse-title">Awake and listening</div>
          <div className="pulse-sub">
            The core beats once per cognitive cycle. The rings show what Novi is attending to and how it feels.
          </div>
          <div className="pulse-readouts">
            <div className="pulse-focus">
              <span className="pf-label">attending</span>
              <span className="pf-val">{focus}</span>
            </div>
            <div className="pulse-affect">
              <span className="pf-label">affect</span>
              <span className="pf-val">{affectName}</span>
            </div>
            <div className="pulse-meter soul">
              <i style={{ width: (affect * 100).toFixed(0) + '%' }} />
            </div>
            <div className="pulse-focus">
              <span className="pf-label">confidence</span>
              <span className="pf-val" style={{ color: 'var(--text)' }}>
                {confidence.toFixed(2)}
              </span>
            </div>
            <div className="pulse-meter">
              <i style={{ width: (confidence * 100).toFixed(0) + '%' }} />
            </div>
          </div>
        </div>
      </div>

      <div className="statgrid">
        <StatCard k="cycle" v={state?.cycle ?? 0} s="cognitive cycles run" />
        <StatCard
          k="health"
          v={status}
          s="system status"
          tone={status === 'OK' || status === 'GOOD' ? 'good' : status === 'BAD' ? 'bad' : undefined}
        />
        <StatCard k="memories" v={activeMem != null ? activeMem : 0} s="active memory records" />
        <StatCard k="knowledge" v={state?.knowledge?.triples ?? 0} s="facts in the graph" tone="warn" />
      </div>

      <div className="grid cols-2" style={{ marginBottom: 16 }}>
        <Panel title="Personality">
          {state === null ? (
            <span className="muted">…</span>
          ) : (
            <>
              <div className="ident">
                <span className="name">{so.identity || 'Novi'}</span>
                <span className="persona">{so.persona || ''}</span>
                <span className="tone">{so.tone || 'neutral'}</span>
              </div>
              {so.traits && Object.keys(so.traits).length > 0 && (
                <div className="sect">
                  <div className="h">Traits · stable personality</div>
                  <Bars obj={so.traits} cls="bar-trait" />
                </div>
              )}
              {so.affect && Object.keys(so.affect).length > 0 && (
                <div className="sect">
                  <div className="h">Affect · right now</div>
                  <Bars obj={so.affect} cls="bar-affect" />
                </div>
              )}
              {so.values && Object.keys(so.values).length > 0 && (
                <div className="sect">
                  <div className="h">Values</div>
                  <Chips items={Object.entries(so.values).map(([k, v]) => ({ k, v }))} />
                </div>
              )}
            </>
          )}
        </Panel>
        <Panel title="Attention">
          <AttentionBlock snapshot={attention} />
        </Panel>
      </div>

      <div className="grid cols-2" style={{ marginBottom: 16 }}>
        <Panel title="Activity">
          <div className="chart-legend">
            <span className="lg">
              <span className="sw" style={{ background: 'var(--warn)' }} />
              events / sec
            </span>
            <span className="lg">
              <span className="sw" style={{ background: 'var(--accent)' }} />
              confidence
            </span>
            <span className="lg">
              <span className="sw" style={{ background: 'var(--good)' }} />
              knowledge (triples)
            </span>
          </div>
          <ActivityChart
            series={[
              { data: evHist, color: '--warn' },
              { data: confHist, color: '--accent' },
              { data: memHist, color: '--good' },
            ]}
          />
        </Panel>
        <Panel title="Position &amp; Goal">
          {state === null ? (
            <span className="muted">…</span>
          ) : (
            <>
              {state.active_goal ? (
                <>
                  <KV
                    k="active"
                    v={
                      <>
                        {state.active_goal.kind} &rarr; {state.active_goal.target}
                      </>
                    }
                  />
                  <KV k="status" v={state.active_goal.status} />
                  <KV k="steps" v={state.active_goal.steps_taken} />
                  {state.active_goal.distance_to_goal != null && (
                    <KV k="distance" v={state.active_goal.distance_to_goal + ' m'} />
                  )}
                  {state.plan?.steps && state.plan.steps.length > 0 && (
                    <KV
                      k="plan"
                      v={state.plan.steps
                        .map((st) => st.action + (st.done ? ' ✓' : ''))
                        .join(' → ')}
                    />
                  )}
                </>
              ) : (
                <KV k="active" v="none" />
              )}
              <KV
                k="history"
                v={
                  (state.goals_history ?? [])
                    .map((x) => x.kind + ':' + x.status)
                    .slice(-3)
                    .join(' | ') || 'none'
                }
              />
              <FloorMap state={{ body: state.body, active_goal: state.active_goal }} />
            </>
          )}
        </Panel>
      </div>

      <Panel title="Reasoning">
        <ReasoningBlock trace={state?.reasoning_trace} lastDetections={state?.last_step?.detections} />
      </Panel>
    </>
  )
}
