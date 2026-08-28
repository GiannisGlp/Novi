import { useEffect, useRef, useState } from 'react'
import type { ChatTurn, StreamingState } from '../hooks/useChat'
import { Turn } from './shared/Turn'

export interface ChatDrawerProps {
  open: boolean
  onCollapse: () => void
  turns: ChatTurn[]
  streaming: StreamingState | null
  onSend: (text: string, confidence: number) => void
  onListen?: () => void
  onStep?: () => void
  onClear?: () => void
  isStreaming?: boolean
  disabled?: boolean
}

/**
 * Right-side conversation drawer. Renders `turns` + the live streaming bubble,
 * with the legacy empty state. The optimistic user turn is added by the chat
 * hook; the `[heard]` prefix on user turns is stripped like the legacy console.
 */
export function ChatDrawer({
  open,
  onCollapse,
  turns,
  streaming,
  onSend,
  onListen,
  onStep,
  onClear,
  isStreaming = false,
  disabled = false,
}: ChatDrawerProps) {
  const [text, setText] = useState('')
  // Kept as a string like the legacy console so the numeric input never drifts
  // into float artifacts (0.9 → 0.8999999761...); parsed only on send.
  const [conf, setConf] = useState('0.9')
  const bodyRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const el = bodyRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [turns.length, streaming?.text, open])

  const submit = () => {
    const trimmed = text.trim()
    if (!trimmed || isStreaming) return
    onSend(trimmed, Number.parseFloat(conf))
    setText('')
  }

  const hasMessages = turns.length > 0 || streaming !== null

  return (
    <aside className={'chatdrawer' + (open ? ' open' : '')} id="chatdrawer">
      <div className="panel chatpanel" style={{ border: 'none', boxShadow: 'none', background: 'transparent' }}>
        <div className="phbar" style={{ padding: '0 6px 0 0' }}>
          <h3 style={{ border: 'none', background: 'transparent' }}>Conversation</h3>
          <button
            className="ghost"
            title="Collapse / expand chat"
            aria-label="Collapse or expand chat"
            onClick={onCollapse}
          >
            ▾
          </button>
        </div>
        <div className="chatbody" id="chat" aria-live="polite" ref={bodyRef}>
          {!hasMessages && (
            <div className="empty">
              <div className="ring" aria-hidden="true">
                ✦
              </div>
              <p className="headline">Novi is awake and listening.</p>
              <p>
                Say hello, or tell it something about the world —<br />
                e.g. &ldquo;alice moved the door&rdquo;.
              </p>
            </div>
          )}
          {turns.map((t, i) => (
            <Turn
              key={t.seq ?? i}
              turn={{
                role: t.role,
                text: t.role === 'user' ? t.text.replace(/^\s*\[heard\]\s*/i, '') : t.text,
                trace: t.trace,
              }}
            />
          ))}
          {streaming && (
            <div className="turn start">
              <div className="avat">N</div>
              <div className="box">
                <div className="who">novi</div>
                <div className="bubble">
                  {streaming.text || (
                    <>
                      <span className="spinner"></span> thinking…
                    </>
                  )}
                  {streaming.error && <span className="muted"> (error: {streaming.error})</span>}
                </div>
              </div>
            </div>
          )}
        </div>
        <div className="chatinput">
          <textarea
            id="say"
            placeholder='Talk to Novi — e.g. "alice moved the door"'
            rows={1}
            aria-label="Message Novi"
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                submit()
              }
            }}
            disabled={disabled}
          />
          <div className="row">
            <button id="sendBtn" className="primary" onClick={submit} disabled={disabled || !text.trim() || isStreaming}>
              Send
            </button>
            <button id="listenBtn" title="Record from the microphone and transcribe" onClick={onListen} disabled={disabled}>
              🎤 Listen
            </button>
            <button id="stepBtn" title="Advance the brain one manual cycle" onClick={onStep} disabled={disabled}>
              ⏭ Step once
            </button>
            <button id="clearBtn" title="Clear the conversation" onClick={onClear} disabled={disabled}>
              🗑 Clear
            </button>
            <label className="num" title="Confidence threshold fed to the brain with your message">
              conf
              <input
                type="number"
                id="conf"
                value={conf}
                step={0.05}
                min={0}
                max={1}
                onChange={(e) => setConf(e.target.value)}
              />
            </label>
            <span className="hint">Enter to send · Shift+Enter for newline</span>
          </div>
        </div>
      </div>
    </aside>
  )
}
