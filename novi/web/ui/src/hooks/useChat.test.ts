import { act, renderHook } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { jsonResponse, streamResponse } from '../test/helpers'
import { MAX_RENDERED_SEQS, pruneRenderedSeqs, useChat } from './useChat'

/** Routes by URL: /api/chat/stream returns the given frames, everything else JSON. */
function routedFetch(frames: string, extra?: Record<string, unknown>) {
  return vi.fn((url: string) => {
    if (url === '/api/chat/stream') return Promise.resolve(streamResponse(frames))
    if (url === '/api/chat?after=0') return Promise.resolve(jsonResponse({ after: 0, entries: [] }))
    return Promise.resolve(jsonResponse(extra ?? { ok: true }))
  })
}

describe('useChat', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
    vi.useRealTimers()
  })

  it('loads history on mount', async () => {
    const fetchMock = vi.fn((url: string) => {
      if (url === '/api/chat?after=0') {
        return Promise.resolve(
          jsonResponse({ after: 1, entries: [{ seq: 1, role: 'novi', text: 'hello' }] }),
        )
      }
      return Promise.resolve(jsonResponse({ ok: true }))
    })
    vi.stubGlobal('fetch', fetchMock)
    const { result } = renderHook(() => useChat(() => undefined))
    await act(async () => {})
    expect(result.current.turns).toEqual([{ seq: 1, role: 'novi', text: 'hello' }])
  })

  it('streams tokens into the bubble and appends the final novi turn on done', async () => {
    const frames =
      'data: ' + JSON.stringify({ token: 'hel' }) + '\n\n' +
      'data: ' + JSON.stringify({ token: 'lo' }) + '\n\n' +
      'data: ' + JSON.stringify({ done: true, after: 7, user: { seq: 1 }, novi: { seq: 2, text: 'hello', trace: { route: 'reasoner' } } }) + '\n\n'
    vi.stubGlobal('fetch', routedFetch(frames))
    const { result } = renderHook(() => useChat(() => undefined))
    await act(async () => {})
    expect(result.current.isStreaming).toBe(false)

    await act(async () => {
      await result.current.send('hi', 0.9)
    })
    // optimistic user turn + final novi turn
    expect(result.current.turns).toEqual([
      { role: 'user', text: 'hi' },
      { seq: 2, role: 'novi', text: 'hello', trace: { route: 'reasoner' } },
    ])
    expect(result.current.streaming).toBeNull()
    expect(result.current.isStreaming).toBe(false)
  })

  it('removes the optimistic turn when the server reports a duplicate', async () => {
    const frames =
      'data: ' + JSON.stringify({ deduplicated: true, after: 4, novi: { seq: 5 } }) + '\n\n'
    vi.stubGlobal('fetch', routedFetch(frames))
    const { result } = renderHook(() => useChat(() => undefined))
    await act(async () => {})
    await act(async () => {
      await result.current.send('hi', 0.9)
    })
    expect(result.current.turns).toEqual([])
    expect(result.current.streaming).toBeNull()
    expect(result.current.isStreaming).toBe(false)
  })

  it('leaves an error bubble when the stream reports an error', async () => {
    const frames = 'data: ' + JSON.stringify({ error: 'ollama unreachable' }) + '\n\n'
    vi.stubGlobal('fetch', routedFetch(frames))
    const { result } = renderHook(() => useChat(() => undefined))
    await act(async () => {})
    await act(async () => {
      await result.current.send('hi', 0.9)
    })
    expect(result.current.streaming?.error).toBe('ollama unreachable')
    expect(result.current.isStreaming).toBe(false)
    // the optimistic user turn stays, like the legacy console
    expect(result.current.turns).toEqual([{ role: 'user', text: 'hi' }])
  })

  it('ignores a duplicate send within the 15s window', async () => {
    const frames =
      'data: ' + JSON.stringify({ done: true, after: 1, novi: { seq: 2, text: 'ok' } }) + '\n\n'
    const fetchMock = routedFetch(frames)
    vi.stubGlobal('fetch', fetchMock)
    const { result } = renderHook(() => useChat(() => undefined))
    await act(async () => {})
    await act(async () => {
      await result.current.send('hi', 0.9)
    })
    const streamCallsAfterFirst = fetchMock.mock.calls.filter((c) => c[0] === '/api/chat/stream').length
    await act(async () => {
      await result.current.send('hi', 0.9)
    })
    const streamCallsAfterSecond = fetchMock.mock.calls.filter((c) => c[0] === '/api/chat/stream').length
    expect(streamCallsAfterSecond).toBe(streamCallsAfterFirst)
  })

  it('appends a timed-out turn when the stream aborts', async () => {
    vi.useFakeTimers()
    const fetchMock = vi.fn((url: string, init?: RequestInit) => {
      if (url === '/api/chat/stream') {
        return new Promise((_resolve, reject) => {
          init?.signal?.addEventListener('abort', () =>
            reject(new DOMException('Aborted', 'AbortError')),
          )
        })
      }
      return Promise.resolve(jsonResponse({ after: 0, entries: [] }))
    })
    vi.stubGlobal('fetch', fetchMock)
    const report = vi.fn()
    const { result } = renderHook(() => useChat(report, () => 'qwen3:8b'))
    await act(async () => {})
    const sendPromise = result.current.send('hi', 0.9)
    act(() => vi.advanceTimersByTime(125000))
    await act(async () => {
      await sendPromise
    })
    expect(result.current.turns).toContainEqual({
      role: 'novi',
      text: '(timed out — is Ollama/qwen3:8b reachable?)',
    })
    expect(report).toHaveBeenCalledWith(false)
  })

  it('falls back to POST /api/chat when the stream fails without an abort', async () => {
    const fetchMock = vi.fn((url: string) => {
      if (url === '/api/chat/stream') return Promise.reject(new Error('network down'))
      if (url === '/api/chat') return Promise.resolve(jsonResponse({ ok: true }))
      return Promise.resolve(jsonResponse({ after: 0, entries: [] }))
    })
    vi.stubGlobal('fetch', fetchMock)
    const report = vi.fn()
    const { result } = renderHook(() => useChat(report))
    await act(async () => {})
    await act(async () => {
      await result.current.send('hi', 0.9)
    })
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/chat',
      expect.objectContaining({ method: 'POST', body: JSON.stringify({ text: 'hi', confidence: 0.9 }) }),
    )
    expect(report).toHaveBeenLastCalledWith(true)
  })

  it('keeps the optimistic turn and adds a notice when the stream resolves empty', async () => {
    // Server accepted the stream (HTTP 200) but closed it without a token, done,
    // or error frame — the user's message was never recorded server-side.
    const fetchMock = vi.fn((url: string) => {
      if (url === '/api/chat/stream') return Promise.resolve(streamResponse(''))
      return Promise.resolve(jsonResponse({ after: 0, entries: [] }))
    })
    vi.stubGlobal('fetch', fetchMock)
    const { result } = renderHook(() => useChat(() => undefined))
    await act(async () => {})
    await act(async () => {
      await result.current.send('hi', 0.9)
    })
    expect(result.current.turns).toEqual([
      { role: 'user', text: 'hi' },
      { role: 'novi', text: '(no response received — the model may still be loading; try again)' },
    ])
    expect(result.current.streaming).toBeNull()
    expect(result.current.isStreaming).toBe(false)
  })

  it('adds a reply-interrupted notice when the stream drops after partial tokens', async () => {
    // Tokens arrived (proving the model is reachable) but the connection closed
    // before the done frame, so the reply was never recorded server-side.
    const frames = 'data: ' + JSON.stringify({ token: 'hel' }) + '\n\n'
    const fetchMock = vi.fn((url: string) => {
      if (url === '/api/chat/stream') return Promise.resolve(streamResponse(frames))
      return Promise.resolve(jsonResponse({ after: 0, entries: [] }))
    })
    vi.stubGlobal('fetch', fetchMock)
    const { result } = renderHook(() => useChat(() => undefined))
    await act(async () => {})
    await act(async () => {
      await result.current.send('hi', 0.9)
    })
    expect(result.current.turns).toEqual([
      { role: 'user', text: 'hi' },
      { role: 'novi', text: '(reply interrupted — the connection dropped mid-reply)' },
    ])
    expect(result.current.streaming).toBeNull()
    expect(result.current.isStreaming).toBe(false)
  })

  it('appends a failure turn when the fallback also fails', async () => {
    const fetchMock = vi.fn((url: string) => {
      if (url === '/api/chat/stream') return Promise.reject(new Error('network down'))
      if (url === '/api/chat') return Promise.reject(new Error('still down'))
      return Promise.resolve(jsonResponse({ after: 0, entries: [] }))
    })
    vi.stubGlobal('fetch', fetchMock)
    const { result } = renderHook(() => useChat(() => undefined))
    await act(async () => {})
    await act(async () => {
      await result.current.send('hi', 0.9)
    })
    expect(result.current.turns).toContainEqual({
      role: 'novi',
      text: '(reply failed — is the model reachable?)',
    })
  })

  it('clear posts /api/chat/clear and empties the conversation', async () => {
    const fetchMock = vi.fn((url: string) => {
      if (url === '/api/chat?after=0') {
        return Promise.resolve(
          jsonResponse({ after: 1, entries: [{ seq: 1, role: 'novi', text: 'hello' }] }),
        )
      }
      if (url === '/api/chat/clear') return Promise.resolve(jsonResponse({ ok: true }))
      return Promise.resolve(jsonResponse({ ok: true }))
    })
    vi.stubGlobal('fetch', fetchMock)
    const { result } = renderHook(() => useChat(() => undefined))
    await act(async () => {})
    expect(result.current.turns).toHaveLength(1)
    await act(async () => {
      await result.current.clear()
    })
    expect(fetchMock).toHaveBeenCalledWith('/api/chat/clear', expect.objectContaining({ method: 'POST' }))
    expect(result.current.turns).toEqual([])
  })

  it('refresh does not duplicate entries already rendered', async () => {
    const entry = { seq: 1, role: 'novi', text: 'a' } as const
    const fetchMock = vi.fn((url: string) => {
      if (url === '/api/chat?after=0') return Promise.resolve(jsonResponse({ after: 1, entries: [entry] }))
      if (url === '/api/chat?after=1') return Promise.resolve(jsonResponse({ after: 1, entries: [entry] }))
      return Promise.resolve(jsonResponse({ ok: true }))
    })
    vi.stubGlobal('fetch', fetchMock)
    const { result } = renderHook(() => useChat(() => undefined))
    await act(async () => {})
    expect(result.current.turns).toHaveLength(1)
    await act(async () => {
      await result.current.refresh()
    })
    expect(result.current.turns).toHaveLength(1)
  })

  it('notice appends a novi turn without a seq', async () => {
    vi.stubGlobal('fetch', routedFetch(''))
    const { result } = renderHook(() => useChat(() => undefined))
    await act(async () => {})
    act(() => result.current.notice('switched model → qwen3:8b'))
    expect(result.current.turns).toEqual([{ role: 'novi', text: 'switched model → qwen3:8b' }])
  })

  it('step posts /api/step', async () => {
    const fetchMock = vi.fn((url: string) => {
      if (url === '/api/chat?after=0') return Promise.resolve(jsonResponse({ after: 0, entries: [] }))
      return Promise.resolve(jsonResponse({ ok: true }))
    })
    vi.stubGlobal('fetch', fetchMock)
    const { result } = renderHook(() => useChat(() => undefined))
    await act(async () => {})
    await act(async () => {
      await result.current.step()
    })
    expect(fetchMock).toHaveBeenCalledWith('/api/step', expect.objectContaining({ method: 'POST' }))
  })

  it('pruneRenderedSeqs drops stale seqs but keeps the visible window', () => {
    const seen = new Set([1, 2, 3, 4, 5])
    const out = pruneRenderedSeqs(seen, new Set([4, 5]), 3, 500)
    expect(out.has(4)).toBe(true)
    expect(out.has(5)).toBe(true)
    expect(out.has(1)).toBe(false)
    expect(out.has(2)).toBe(false)
    // input is not mutated
    expect(seen.size).toBe(5)
  })

  it('pruneRenderedSeqs hard-caps at the newest entries', () => {
    const seen = new Set(Array.from({ length: MAX_RENDERED_SEQS + 50 }, (_, i) => i + 1))
    const out = pruneRenderedSeqs(seen, new Set(), 0)
    expect(out.size).toBe(MAX_RENDERED_SEQS)
    expect(out.has(1)).toBe(false)
    expect(out.has(MAX_RENDERED_SEQS + 50)).toBe(true)
  })

  it('dedup still filters re-delivered entries after heavy traffic', async () => {
    // 600 seqs flow through refresh: the visible window caps at MAX_TURNS and
    // the dedup set must stay bounded without re-accepting old seqs.
    const total = 600
    const fetchMock = vi.fn((url: string) => {
      const m = /after=(\d+)/.exec(url)
      const after = m ? Number(m[1]) : 0
      const next = Math.min(after + 100, total)
      const entries = Array.from({ length: next - after }, (_, i) => ({
        seq: after + i + 1,
        role: 'novi',
        text: `m${after + i + 1}`,
      }))
      return Promise.resolve(jsonResponse({ after: next, entries }))
    })
    vi.stubGlobal('fetch', fetchMock)
    const { result } = renderHook(() => useChat(() => undefined, undefined, { enabled: false }))
    await act(async () => {})
    for (let i = 0; i < 6; i++) {
      await act(async () => {
        await result.current.refresh()
      })
    }
    expect(result.current.turns.length).toBeLessThanOrEqual(90)
    // re-polling the tail re-delivers nothing new: no duplicates appended
    const before = result.current.turns.length
    await act(async () => {
      await result.current.refresh()
    })
    expect(result.current.turns.length).toBe(before)
  })

  it('listen reports nothing-heard when no audio arrives', async () => {
    const fetchMock = vi.fn((url: string) => {
      if (url === '/api/chat?after=0') return Promise.resolve(jsonResponse({ after: 0, entries: [] }))
      if (url === '/api/listen') return Promise.resolve(jsonResponse({ result: { heard: false } }))
      return Promise.resolve(jsonResponse({ ok: true }))
    })
    vi.stubGlobal('fetch', fetchMock)
    const { result } = renderHook(() => useChat(() => undefined))
    await act(async () => {})
    await act(async () => {
      await result.current.listen()
    })
    expect(result.current.turns).toContainEqual({ role: 'novi', text: '(nothing heard)' })
  })
})
