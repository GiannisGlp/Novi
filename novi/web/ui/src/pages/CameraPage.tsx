import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../api/client'
import type { PreviewFrame, RealIOStatus } from '../api/types'
import { CameraOverlay } from '../components/CameraOverlay'
import { Section } from '../components/Section'
import { useRealIO } from '../hooks/useRealIO'

export interface CameraPageProps {
  reportConnection: (ok: boolean) => void
  frame: PreviewFrame | null
  showImage: boolean
}

interface TranscriptTurn {
  role: 'you' | 'novi' | 'sys'
  text: string
}

const MAX_TRANSCRIPT = 60

function healthBadgeCls(health: string): string {
  if (health === 'available') return 'ok'
  if (health === 'failed') return 'err'
  return 'warn'
}

/** Camera & voice — full live perception, talk/listen dialog (port of camera.html). */
export function CameraPage({ reportConnection, frame, showImage }: CameraPageProps) {
  const { status, refresh } = useRealIO(reportConnection)

  const [enabling, setEnabling] = useState(false)
  const [enableMsg, setEnableMsg] = useState('🎥 Enable camera + mic + speaker')
  const [listening, setListening] = useState(false)
  const [autoListen, setAutoListen] = useState(false)
  const [speakBack, setSpeakBackState] = useState(true)
  const [reply, setReply] = useState<{ heard: string; reply: string; spoken?: boolean } | null>(null)
  const [transcript, setTranscript] = useState<TranscriptTurn[]>([])
  const [typeInput, setTypeInput] = useState('')
  const [lastHeard, setLastHeard] = useState('—')

  const listeningRef = useRef(false)
  const autoRef = useRef(false)
  const speakBackRef = useRef(true)
  const autoTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const transcriptRef = useRef<HTMLDivElement>(null)

  const health = frame?.camera_health || 'offline'
  const dets = Array.isArray(frame?.detections) ? frame.detections : []
  const st = status as RealIOStatus | null
  const person = frame?.face?.person || frame?.person || (frame?.face?.proposal ? 'someone new!' : '—')
  const tier = frame?.face?.tier || frame?.tier || '—'

  const addTurn = useCallback((role: TranscriptTurn['role'], text: string) => {
    setTranscript((prev) => [...prev, { role, text }].slice(-MAX_TRANSCRIPT))
  }, [])

  useEffect(() => {
    const el = transcriptRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [transcript.length])

  const speak = useCallback(
    (text: string) => {
      if (!speakBackRef.current || !('speechSynthesis' in window)) return
      try {
        window.speechSynthesis.cancel()
        window.speechSynthesis.speak(new SpeechSynthesisUtterance(text))
      } catch {
        /* speech synthesis is best-effort */
      }
    },
    [],
  )

  const enableIO = async () => {
    setEnabling(true)
    setEnableMsg('Enabling…')
    try {
      const res = await api.realEnable()
      const r = (res.result ?? {}) as Record<string, unknown>
      setEnableMsg(
        [
          r.camera ? 'camera ✓' : 'camera ✗ ' + (r.camera_error || ''),
          r.mic ? 'mic ✓' : 'mic ✗',
          r.speaker ? 'speaker ✓' : 'speaker ✗',
        ].join(' · '),
      )
      void refresh()
    } catch {
      setEnableMsg('enable failed')
    }
    setEnabling(false)
  }

  const toggleListen = useCallback(async () => {
    if (listeningRef.current) return
    listeningRef.current = true
    setListening(true)
    try {
      const res = await api.voiceListen(3)
      const r = (res.result ?? res) as Record<string, unknown>
      const heard = String(r.text ?? '').trim()
      const replyText = String(r.reply ?? '').trim()
      setLastHeard(heard || '(silence)')
      if (!heard && !replyText) {
        addTurn('sys', "didn't catch that — try again a bit closer")
      } else {
        if (heard) addTurn('you', heard)
        if (replyText) {
          addTurn('novi', replyText)
          speak(replyText)
        }
        setReply({
          heard,
          reply: replyText,
          spoken: Boolean((r.spoken as Record<string, unknown> | undefined)?.spoken),
        })
        if (r.person) {
          /* person readout comes from the preview frame; the server syncs shortly */
        }
      }
    } catch (e) {
      addTurn('sys', 'error: ' + (e instanceof Error ? e.message : String(e)))
    }
    listeningRef.current = false
    setListening(false)
    if (autoRef.current) {
      autoTimerRef.current = setTimeout(() => {
        void toggleListen()
      }, 400)
    }
  }, [addTurn, speak])

  const toggleAuto = (on: boolean) => {
    setAutoListen(on)
    autoRef.current = on
    if (autoTimerRef.current) {
      clearTimeout(autoTimerRef.current)
      autoTimerRef.current = null
    }
    if (on && !listeningRef.current) void toggleListen()
  }

  useEffect(() => () => {
    if (autoTimerRef.current) clearTimeout(autoTimerRef.current)
  }, [])

  const toggleSpeakBack = async (v: boolean) => {
    setSpeakBackState(v)
    speakBackRef.current = v
    try {
      await api.realSpeakback(v)
    } catch {
      /* sync on next poll */
    }
  }

  const sendTyped = async () => {
    const text = typeInput.trim()
    if (!text || listeningRef.current) return
    setTypeInput('')
    addTurn('you', text)
    try {
      const res = await api.voiceTurn(text)
      const r = (res.result ?? res) as Record<string, unknown>
      if (r.reply) {
        addTurn('novi', String(r.reply))
        speak(String(r.reply))
      }
    } catch (e) {
      addTurn('sys', 'error: ' + (e instanceof Error ? e.message : String(e)))
    }
  }

  return (
    <>
      <Section eyebrow="Camera" title="Camera &amp; voice" desc="Novi sees you, hears you, talks back." />
      <div className="cam-grid">
        <div className="cam-card">
          <h2 className="cam-cardtitle">Camera · what Novi sees</h2>
          <CameraOverlay
            frame={frame}
            showImage={showImage}
            badges={
              <>
                <span className={'badge ' + healthBadgeCls(health)}>{health}</span>
                {frame?.face && (frame.face.person || frame.face.proposal) && (
                  <span className="badge ok">
                    {frame.face.person
                      ? `${frame.face.person} (${frame.face.tier})`
                      : 'new person — say hi!'}
                  </span>
                )}
                {st?.devices?.camera && <span className="badge ok">live</span>}
              </>
            }
            placeholder={
              <>
                camera off
                <br />
                <span style={{ fontSize: 12 }}>
                  press enable below — Novi starts watching for people and objects
                </span>
              </>
            }
          />
          <button id="enableBtn" onClick={enableIO} disabled={enabling}>
            {enableMsg}
          </button>

          <div style={{ marginTop: 16 }}>
            <h2 className="cam-cardtitle">Detections · objects &amp; faces (live)</h2>
            <ul className="det">
              {dets.length === 0 ? (
                <li className="muted">none yet</li>
              ) : (
                dets.map((x, i) =>
                  typeof x === 'string' ? (
                    <li key={i}>{x}</li>
                  ) : (
                    <li key={i}>
                      {x.label}{' '}
                      <span className="muted">{Math.round((x.confidence || 0) * 100)}%</span>
                    </li>
                  ),
                )
              )}
            </ul>
            <div className="row-kv">
              <span className="k">Person present</span>
              <span className="v">{person}</span>
            </div>
            <div className="row-kv">
              <span className="k">Identity tier</span>
              <span className="v">{tier}</span>
            </div>
            <div className="row-kv">
              <span className="k">Place</span>
              <span className="v">{frame?.place || '—'}</span>
            </div>
            <div className="row-kv">
              <span className="k">Vision backend</span>
              <span className="v">
                {frame?.detector_backend || '?'} · {frame?.faces_backend || '?'}
              </span>
            </div>
            <div className="row-kv">
              <span className="k">Camera health</span>
              <span className="v">
                {health}
                {frame?.stale ? ' · stale' : ''}
              </span>
            </div>
          </div>

        </div>

        <div className="cam-card">
          <h2 className="cam-cardtitle">Talk with Novi</h2>
          <button
            id="micBtn"
            className={'primary' + (listening ? ' listening' : '')}
            onClick={toggleListen}
          >
            {listening ? '🎙 Listening… (speak now)' : '🎙 Hold to talk — press once, speak ~3s'}
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
            <label className="tog">
              <input
                type="checkbox"
                checked={autoListen}
                onChange={(e) => toggleAuto(e.target.checked)}
              />
              continuous conversation
            </label>
          </div>
          <div id="reply" className="cam-reply">
            {reply ? (
              <>
                <div className="muted">You said:</div>
                {reply.heard || <span className="muted">(silence)</span>}
                {reply.reply && (
                  <>
                    <div className="muted" style={{ marginTop: 6 }}>
                      Novi replied{reply.spoken ? ' (spoken aloud)' : ''}:
                    </div>
                    {reply.reply}
                  </>
                )}
              </>
            ) : (
              <span className="muted">
                Press the mic and say hello — Novi answers out loud and here.
              </span>
            )}
          </div>
          <div id="transcript" className="cam-transcript" ref={transcriptRef} aria-live="polite">
            {transcript.map((t, i) => (
              <div key={i} className={'t-turn t-' + t.role}>
                {t.role === 'sys' ? (
                  t.text
                ) : (
                  <>
                    <div className="who">{t.role === 'you' ? 'you' : 'novi'}</div>
                    {t.text}
                  </>
                )}
              </div>
            ))}
          </div>

          <h2 className="cam-cardtitle" style={{ marginTop: 16 }}>
            Type instead
          </h2>
          <div className="enrollrow">
            <input
              type="text"
              value={typeInput}
              placeholder="type to Novi…"
              aria-label="Message Novi"
              onChange={(e) => setTypeInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') void sendTyped()
              }}
            />
            <button onClick={sendTyped}>Send</button>
          </div>

          <h2 className="cam-cardtitle" style={{ marginTop: 16 }}>
            Voice status
          </h2>
          <div className="row-kv">
            <span className="k">Mic enabled</span>
            <span className="v">{st?.devices?.mic ? 'on' : 'off'}</span>
          </div>
          <div className="row-kv">
            <span className="k">Speaker enabled</span>
            <span className="v">{st?.devices?.speaker ? 'on' : 'off'}</span>
          </div>
          <div className="row-kv">
            <span className="k">Last heard</span>
            <span className="v">{lastHeard}</span>
          </div>
        </div>
      </div>
    </>
  )
}
