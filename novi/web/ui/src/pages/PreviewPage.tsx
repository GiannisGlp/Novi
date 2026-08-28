import { useState } from 'react'
import { api } from '../api/client'
import type { PreviewFrame, RealIOStatus } from '../api/types'
import { CameraOverlay } from '../components/CameraOverlay'
import { Section } from '../components/Section'
import { useRealIO } from '../hooks/useRealIO'

export interface PreviewPageProps {
  reportConnection: (ok: boolean) => void
  frame: PreviewFrame | null
  showImage: boolean
}

function healthBadgeCls(health: string): string {
  if (health === 'available') return 'ok'
  if (health === 'failed') return 'err'
  return 'warn'
}

/** Perception preview — live camera, talk to Novi out loud (port of preview.html). */
export function PreviewPage({ reportConnection, frame, showImage }: PreviewPageProps) {
  const { status, refresh } = useRealIO(reportConnection)
  const [enabling, setEnabling] = useState(false)
  const [enableMsg, setEnableMsg] = useState('🎥 Enable camera + mic + speaker')
  const [listening, setListening] = useState(false)
  const [speakBack, setSpeakBack] = useState(true)
  const [reply, setReply] = useState<{ heard: string; reply: string; spoken?: boolean } | null>(null)
  const [err, setErr] = useState<string | null>(null)

  const health = frame?.camera_health || 'offline'
  const dets = Array.isArray(frame?.detections) ? frame.detections : []

  const enableIO = async () => {
    setEnabling(true)
    setEnableMsg('Enabling…')
    try {
      const res = await api.realEnable()
      const r = (res.result ?? {}) as Record<string, unknown>
      const parts = [
        r.camera ? 'camera ✓' : 'camera ✗ ' + (r.camera_error || ''),
        r.mic ? 'mic ✓' : 'mic ✗',
        r.speaker ? 'speaker ✓' : 'speaker ✗',
      ]
      setEnableMsg(parts.join(' · '))
      void refresh()
    } catch {
      setEnableMsg('enable failed')
    }
    setEnabling(false)
  }

  const toggleListen = async () => {
    if (listening) return
    setListening(true)
    setErr(null)
    try {
      const res = await api.voiceListen(3)
      const r = (res.result ?? res) as Record<string, unknown>
      const heard = String(r.text ?? '').trim()
      const replyText = String(r.reply ?? '').trim()
      setReply({
        heard,
        reply: replyText,
        spoken: Boolean((r.spoken as Record<string, unknown> | undefined)?.spoken),
      })
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e))
    }
    setListening(false)
  }

  const toggleSpeakBack = async (v: boolean) => {
    setSpeakBack(v)
    try {
      await api.realSpeakback(v)
    } catch {
      /* keep the checkbox state; the server syncs on next poll */
    }
  }

  const st = status as RealIOStatus | null

  return (
    <>
      <Section eyebrow="Preview" title="Perception preview" desc="Live camera · talk to Novi · it answers out loud." />
      <div className="preview-grid">
        <div>
          <div className="cam-card">
            <h2 className="cam-cardtitle">Camera</h2>
            <CameraOverlay
              frame={frame}
              showImage={showImage}
              showOverlay={false}
              badges={
                <>
                  <span className={'badge ' + healthBadgeCls(health)}>{health}</span>
                  {frame?.person && (
                    <span className="badge ok">
                      {frame.person} ({frame.tier})
                    </span>
                  )}
                  {frame?.place && <span className="badge ok">{frame.place}</span>}
                  {st?.devices?.camera && <span className="badge ok">live</span>}
                </>
              }
              placeholder={
                <>
                  camera off
                  <br />
                  <span style={{ fontSize: 12 }}>enable real I/O below to start the stream</span>
                </>
              }
            />
            <button id="enableBtn" onClick={enableIO} disabled={enabling}>
              {enableMsg}
            </button>
          </div>
        </div>
        <div>
          <div className="cam-card">
            <h2 className="cam-cardtitle">Talk to Novi</h2>
            <button
              id="micBtn"
              className={'primary' + (listening ? ' listening' : '')}
              onClick={toggleListen}
            >
              {listening ? '🎙 Listening…' : '🎙 Start listening — speak for ~3s'}
            </button>
            <div className="toggles">
              <label className="tog">
                <input
                  type="checkbox"
                  checked={speakBack}
                  onChange={(e) => toggleSpeakBack(e.target.checked)}
                />
                Novi speaks replies aloud
              </label>
            </div>
            <div id="reply" className="cam-reply">
              {err ? (
                <span className="muted">error: {err}</span>
              ) : reply ? (
                <>
                  <div className="muted">You said:</div>
                  {reply.heard || <span className="muted">(silence)</span>}
                  {reply.reply && (
                    <>
                      <div className="muted" style={{ marginTop: 6 }}>
                        Novi{reply.spoken ? ' (spoken aloud)' : ''}:
                      </div>
                      {reply.reply}
                    </>
                  )}
                </>
              ) : (
                <span className="muted">Replies appear here and are spoken when enabled.</span>
              )}
            </div>

            <h2 className="cam-cardtitle" style={{ marginTop: 16 }}>
              Recognition state
            </h2>
            <div className="row-kv">
              <span className="k">Person</span>
              <span className="v">{frame?.person || '—'}</span>
            </div>
            <div className="row-kv">
              <span className="k">Identity tier</span>
              <span className="v">{frame?.tier || '—'}</span>
            </div>
            <div className="row-kv">
              <span className="k">Place</span>
              <span className="v">{frame?.place || '—'}</span>
            </div>
            <div className="row-kv">
              <span className="k">Camera health</span>
              <span className="v">{health}</span>
            </div>

            <h2 className="cam-cardtitle" style={{ marginTop: 16 }}>
              Detections · live
            </h2>
            <ul className="det">
              {dets.length === 0 ? (
                <li className="muted">none yet</li>
              ) : (
                dets.map((x, i) =>
                  typeof x === 'string' ? (
                    <li key={i}>{x}</li>
                  ) : (
                    <li key={i}>
                      {x.label} <span className="muted">{Math.round((x.confidence || 0) * 100)}%</span>
                    </li>
                  ),
                )
              )}
            </ul>
          </div>
        </div>
      </div>
    </>
  )
}
