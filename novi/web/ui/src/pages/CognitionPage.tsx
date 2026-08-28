import { api } from '../api/client'
import type { AttentionSnapshot, BrainState, ContextResponse } from '../api/types'
import { PULSE_COLORS, hashStr } from '../canvas/cssVars'
import { RouterDonut } from '../components/RouterDonut'
import { Section } from '../components/Section'
import { AttentionBlock } from '../components/shared/AttentionBlock'
import { ContextBlock } from '../components/shared/ContextBlock'
import { KV } from '../components/shared/KV'
import { Panel } from '../components/shared/Panel'
import { ReasoningBlock } from '../components/shared/ReasoningBlock'

export interface CognitionPageProps {
  state: BrainState | null
  attention: AttentionSnapshot | null
  context: ContextResponse | null
  onAction?: () => void
}

const AUDIO_EVENTS: { hint: string | null; label: string }[] = [
  { hint: 'knock', label: '🔨 Knock' },
  { hint: 'alarm', label: '🚨 Alarm' },
  { hint: 'footstep', label: '👣 Footstep' },
  { hint: null, label: '✨ Unknown sound' },
]

const GOALS: [number, number][] = [
  [1, 1],
  [3, 0],
]

/** Cognition — reasoning trace, routing donut, attention/context, sleep cycle, action buttons. */
export function CognitionPage({ state, attention, context, onAction }: CognitionPageProps) {
  const router = state?.router ?? {}
  const donutData = router.route_counts_by_class
    ? Object.entries(router.route_counts_by_class).map(([k, v]) => ({
        label: k,
        value: v,
        color: PULSE_COLORS[Math.abs(hashStr(k)) % PULSE_COLORS.length],
      }))
    : []
  const sc = state?.sleep_cycle ?? {}

  return (
    <>
      <Section eyebrow="Cognition" title="How Novi thinks" desc="The reasoning trace, routing decisions, and what captures attention." />

      <div className="grid cols-2-1" style={{ marginBottom: 16 }}>
        <Panel title="Reasoning Trace">
          <ReasoningBlock trace={state?.reasoning_trace} lastDetections={state?.last_step?.detections} />
        </Panel>
        <Panel title="Routing">
          <div className="donut-wrap">
            <RouterDonut data={donutData} />
            <div className="donut-legend">
              {donutData.length === 0 ? (
                <span className="muted">No decisions made yet.</span>
              ) : (
                donutData.map((d, i) => (
                  <div key={i} className="dl">
                    <span className="sw" style={{ background: d.color }} />
                    <span className="n">{d.label}</span>
                    <span className="c">{d.value}</span>
                  </div>
                ))
              )}
            </div>
          </div>
          <div className="sect">
            <div className="h">Last approach</div>
            <div className="muted">
              {router.last_route ? (
                <>
                  {router.last_route}
                  {router.last_reason && <> · {router.last_reason}</>}
                </>
              ) : (
                '—'
              )}
            </div>
          </div>
        </Panel>
      </div>

      <div className="grid cols-2" style={{ marginBottom: 16 }}>
        <Panel title="Attention">
          <AttentionBlock snapshot={attention} />
        </Panel>
        <Panel title="Context">
          <ContextBlock response={context} />
        </Panel>
      </div>

      <div className="grid cols-2">
        <Panel title="Sleep Cycle">
          {state === null ? (
            <span className="muted">…</span>
          ) : sc.enabled ? (
            <>
              <KV k="cadence" v={'every ' + (sc.every_n_cycles ?? '?') + ' cycles'} />
              <KV k="phases run" v={sc.phases_run || 0} />
              {sc.last_phase && (
                <KV
                  k="last phase"
                  v={
                    <>
                      {sc.last_phase.phase}
                      {sc.last_phase.summary && <> · {sc.last_phase.summary.slice(0, 80)}</>}
                    </>
                  }
                />
              )}
            </>
          ) : (
            <span className="muted">sleep cycle not enabled</span>
          )}
        </Panel>
        <Panel title="Actions">
          <div className="actions" style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            <div className="group" style={{ flex: '1 1 100%', color: 'var(--text-mute)', font: '600 10px var(--mono)', textTransform: 'uppercase', letterSpacing: 1.4 }}>
              Audio events
            </div>
            {AUDIO_EVENTS.map((a) => (
              <button
                key={a.label}
                data-audio={a.hint ?? ''}
                onClick={async () => {
                  await api.audio(a.hint, 0.7, a.hint ? 0 : 0.9, 0.9)
                  onAction?.()
                }}
              >
                {a.label}
              </button>
            ))}
            <div className="group" style={{ flex: '1 1 100%', color: 'var(--text-mute)', font: '600 10px var(--mono)', textTransform: 'uppercase', letterSpacing: 1.4 }}>
              Goals
            </div>
            {GOALS.map(([x, y]) => (
              <button
                key={`${x},${y}`}
                data-goal={`${x},${y}`}
                onClick={async () => {
                  await api.goal(x, y, 60)
                  onAction?.()
                }}
              >
                Reach ({x},{y})
              </button>
            ))}
            <div className="group" style={{ flex: '1 1 100%', color: 'var(--text-mute)', font: '600 10px var(--mono)', textTransform: 'uppercase', letterSpacing: 1.4 }}>
              System
            </div>
            <button
              id="healthBtn"
              onClick={async () => {
                await api.health()
                onAction?.()
              }}
            >
              Run health check
            </button>
          </div>
        </Panel>
      </div>
    </>
  )
}
