import type { IdentityDetail, PreviewFrame, RecognitionList } from '../api/types'
import { Section } from '../components/Section'
import { Chips } from '../components/shared/Chips'
import { KV } from '../components/shared/KV'
import { Panel } from '../components/shared/Panel'
import { useRealIO } from '../hooks/useRealIO'
import { useRecognition } from '../hooks/useRecognition'

export interface PerceptionPageProps {
  reportConnection: (ok: boolean) => void
  frame: PreviewFrame | null
  showImage: boolean
  identity: IdentityDetail | null
}

type Enrollment = NonNullable<RecognitionList['enrollments']>[number]

/** Group enrollment rows per person — a person may appear as BOTH face + voice rows. */
function groupByPerson(rows: Enrollment[]): { k: string; v: string }[] {
  const byPerson = new Map<string, { name: string; kinds: Set<string> }>()
  for (const e of rows) {
    const key = (e.person_id ?? '').trim() || (e.label ?? '')
    if (!key) continue
    const group = byPerson.get(key) ?? { name: e.label ?? key, kinds: new Set<string>() }
    if (e.kind) group.kinds.add(e.kind)
    byPerson.set(key, group)
  }
  return [...byPerson.values()].slice(0, 20).map((g) => ({
    k: g.name,
    v: g.kinds.size > 1 ? [...g.kinds].sort().join('+') : '',
  }))
}

/** Perception — camera preview, identity, recognition enrollments, real-I/O devices. */
export function PerceptionPage({
  reportConnection,
  frame,
  showImage,
  identity,
}: PerceptionPageProps) {
  const { recognition } = useRecognition(reportConnection)
  const { status: realIO } = useRealIO(reportConnection)

  const health = frame?.camera_health || 'offline'
  const meta = [
    frame?.person ? `person: ${frame.person}${frame.tier ? ` (${frame.tier})` : ''}` : '',
    frame?.place ? `place: ${frame.place}` : '',
  ]
    .filter(Boolean)
    .join(' · ')

  const dets = Array.isArray(frame?.detections) ? frame.detections : []
  const cur = identity?.current
  const hist = identity?.snapshot?.history ?? identity?.snapshot?.identities ?? []

  return (
    <>
      <Section eyebrow="Perception" title="What Novi senses" desc="Camera, recognition, and the real I/O devices attached to the body." />

      <div className="grid cols-2" style={{ marginBottom: 16 }}>
        <Panel title="Camera" right={<span className="muted" style={{ fontSize: 11, paddingRight: 10, fontFamily: 'var(--mono)' }}>{health}</span>}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, alignItems: 'center' }}>
            {showImage && frame?.image_data_url ? (
              <img src={frame.image_data_url} className="cam-frame" alt="camera preview" />
            ) : (
              <span className="muted">preview off — start the brain with <b>--camera real</b></span>
            )}
            <div className="cam-meta">
              {meta ||
                (health === 'offline' ? (
                  <>
                    preview off — start the brain with <b>--camera real</b>
                  </>
                ) : (
                  'waiting for first frame…'
                ))}
            </div>
            <div className="chips cam-det">
              {dets.length === 0 ? (
                <span className="muted">no detections yet</span>
              ) : (
                dets.map((x, i) => (
                  <span key={i} className="entity-chip observed">
                    {x.label} <b>{(Number(x.confidence) || 0).toFixed(2)}</b>
                  </span>
                ))
              )}
            </div>
            <div className="muted" style={{ fontSize: 10 }}>
              live from the onboard camera ·{' '}
              <a href="/api/preview" target="_blank" style={{ color: 'var(--accent)' }}>
                api
              </a>
            </div>
          </div>
        </Panel>
        <Panel title="Identity">
          {identity === null ? (
            <span className="muted">…</span>
          ) : cur ? (
            <>
              <div className="ident">
                <span className="name">{cur.name || cur.person || 'person'}</span>
                <span className="tone">
                  {cur.tier || '?'} · {cur.confidence != null ? Number(cur.confidence).toFixed(2) : '—'}
                </span>
              </div>
              <div className="muted" style={{ marginTop: 4 }}>
                modality:{' '}
                {cur.evidence
                  ? Object.keys(cur.evidence).join(', ')
                  : cur.modality || '—'}
              </div>
            </>
          ) : (
            <span className="muted">
              No one observed yet — say hello so Novi can learn who you are.
            </span>
          )}
          {hist.length > 0 && (
            <div className="ctx-section">
              <div className="h">Recent</div>
              {hist.slice(-4).reverse().map((it, i) => (
                <KV
                  key={i}
                  k={it.name || it.person || 'person'}
                  v={
                    <>
                      {it.tier || ''}{' '}
                      {it.confidence != null ? Number(it.confidence).toFixed(2) : ''}
                    </>
                  }
                />
              ))}
            </div>
          )}
        </Panel>
      </div>

      <div className="grid cols-2">
        <Panel title="Recognition">
          {recognition === null ? (
            <span className="muted">…</span>
          ) : recognition.enrollments && recognition.enrollments.length > 0 ? (
            <Chips items={groupByPerson(recognition.enrollments)} />
          ) : (
            <span className="muted">
              No one enrolled yet — faces, voices, places, and sounds are stored here.
            </span>
          )}
        </Panel>
        <Panel title="Devices">
          {realIO === null ? (
            <span className="muted">…</span>
          ) : (
            <>
              <KV k="enabled" v={realIO.enabled ? 'yes' : 'no'} />
              <KV k="camera" v={realIO.devices?.camera ? 'on' : 'off'} />
              <KV k="microphone" v={realIO.devices?.mic ? 'on' : 'off'} />
              <KV k="speaker" v={realIO.devices?.speaker ? 'on' : 'off'} />
              <KV k="speak-back" v={realIO.speak_back ? 'on' : 'off'} />
            </>
          )}
        </Panel>
      </div>
    </>
  )
}
