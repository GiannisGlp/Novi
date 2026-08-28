import { afterEach, describe, expect, it, vi } from 'vitest'
import { api, streamChat } from './client'
import type { StreamEvent } from './types'

function jsonResponse(body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  })
}

function streamResponse(frames: string): Response {
  const enc = new TextEncoder()
  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      controller.enqueue(enc.encode(frames))
      controller.close()
    },
  })
  return new Response(stream, { status: 200 })
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('api request helpers', () => {
  it('GETs a path and parses JSON', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ cycle: 12, run_id: 'abc' }))
    vi.stubGlobal('fetch', fetchMock)
    const state = await api.state()
    expect(fetchMock).toHaveBeenCalledWith('/api/state', undefined)
    expect(state.cycle).toBe(12)
    expect(state.run_id).toBe('abc')
  })

  it('appends query params to events', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ after: 5, events: [] }))
    vi.stubGlobal('fetch', fetchMock)
    await api.events(5)
    expect(fetchMock).toHaveBeenCalledWith('/api/events?after=5', undefined)
  })

  it('URL-encodes memory and knowledge queries', async () => {
    // fresh Response per call — the same Response cannot be JSON-parsed twice
    const fetchMock = vi.fn().mockImplementation(() => jsonResponse({ results: [], counts: {} }))
    vi.stubGlobal('fetch', fetchMock)
    await api.memory('alice & bob', 8)
    await api.knowledge('door', 10)
    expect(fetchMock).toHaveBeenNthCalledWith(1, '/api/memory?query=alice%20%26%20bob&limit=8', undefined)
    expect(fetchMock).toHaveBeenNthCalledWith(2, '/api/knowledge?entity=door&limit=10', undefined)
  })

  it('POSTs JSON bodies with Content-Type', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ ok: true }))
    vi.stubGlobal('fetch', fetchMock)
    await api.setModel('qwen3:8b')
    expect(fetchMock).toHaveBeenCalledWith('/api/model', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model: 'qwen3:8b' }),
    })
  })

  it('throws on non-ok responses', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('boom', { status: 500 })))
    await expect(api.state()).rejects.toThrow()
  })
})

describe('streamChat — SSE data frame parser', () => {
  it('emits token, then done with final text and trace', async () => {
    const frames = [
      'data: ' + JSON.stringify({ token: 'hello ' }),
      'data: ' + JSON.stringify({ token: 'world' }),
      'data: ' + JSON.stringify({ done: true, after: 7, user: { seq: 1 }, novi: { seq: 2, text: 'hello world', trace: { route: 'reasoner', confidence: 0.9 } } }),
    ].join('\n\n') + '\n\n'
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(streamResponse(frames)))
    const events: string[] = []
    await streamChat('hi', 0.9, (e) => events.push(e.kind))
    expect(events).toEqual(['token', 'token', 'done'])
  })

  it('surfaces the done event payload', async () => {
    const frames = 'data: ' + JSON.stringify({ done: true, after: 9, novi: { seq: 3, text: 'ok' } }) + '\n\n'
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(streamResponse(frames)))
    const seen: unknown[] = []
    await streamChat('hi', 0.9, (e) => seen.push(e))
    expect(seen).toHaveLength(1)
    const done = seen[0] as { kind: string; after: number; text: string; noviSeq: number }
    expect(done.kind).toBe('done')
    expect(done.after).toBe(9)
    expect(done.text).toBe('ok')
    expect(done.noviSeq).toBe(3)
  })

  it('reports deduplicated and error frames', async () => {
    const frames =
      'data: ' + JSON.stringify({ deduplicated: true, after: 4, novi: { seq: 5 } }) + '\n\n' +
      'data: ' + JSON.stringify({ error: 'ollama unreachable' }) + '\n\n'
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(streamResponse(frames)))
    const seen: StreamEvent[] = []
    await streamChat('hi', 0.9, (e) => seen.push(e))
    expect(seen[0]).toEqual({ kind: 'deduplicated', after: 4, noviSeq: 5 })
    expect(seen[1]).toEqual({ kind: 'error', error: 'ollama unreachable' })
  })

  it('handles a frame split across chunks with partial lines', async () => {
    const enc = new TextEncoder()
    const full = 'data: ' + JSON.stringify({ token: 'x' }) + '\n\ndata: ' + JSON.stringify({ done: true, after: 1, novi: { seq: 9, text: 'x' } }) + '\n\n'
    const mid = Math.floor(full.length / 2)
    const stream = new ReadableStream<Uint8Array>({
      start(controller) {
        controller.enqueue(enc.encode(full.slice(0, mid)))
        controller.enqueue(enc.encode(full.slice(mid)))
        controller.close()
      },
    })
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(stream, { status: 200 })))
    const events: string[] = []
    await streamChat('hi', 0.9, (e) => events.push(e.kind))
    expect(events).toEqual(['token', 'done'])
  })

  it('skips non-data lines and malformed JSON', async () => {
    const frames = ': ping\n\n' + 'data: {not json}\n\n' + 'data: ' + JSON.stringify({ done: true, after: 0, novi: { seq: 0, text: '' } }) + '\n\n'
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(streamResponse(frames)))
    const events: string[] = []
    await streamChat('hi', 0.9, (e) => events.push(e.kind))
    expect(events).toEqual(['done'])
  })

  it('throws when the response has no body', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(null, { status: 200 })))
    await expect(streamChat('hi', 0.9, () => undefined)).rejects.toThrow()
  })
})
