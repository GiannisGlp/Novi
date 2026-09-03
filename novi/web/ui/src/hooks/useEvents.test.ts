import { act, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { jsonFetch } from '../test/helpers'
import { MockEventSource } from '../test/helpers'
import { EventDedup, useEvents } from './useEvents'

function chunk(after: number, events: unknown[]) {
  return JSON.stringify({ after, events })
}

describe('useEvents', () => {
  beforeEach(() => {
    MockEventSource.reset()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    vi.useRealTimers()
  })

  it('opens an EventSource for the stream', async () => {
    vi.stubGlobal('EventSource', MockEventSource)
    const { result } = renderHook(() => useEvents(() => undefined))
    await act(async () => {})
    expect(MockEventSource.instances).toHaveLength(1)
    expect(MockEventSource.instances[0].url).toBe('/api/events/stream?after=0')
    expect(result.current.events).toEqual([])
  })

  it('appends events from SSE chunks', async () => {
    vi.stubGlobal('EventSource', MockEventSource)
    const { result } = renderHook(() => useEvents(() => undefined))
    await act(async () => {})
    const es = MockEventSource.instances[0]
    act(() => {
      es.emitMessage(
        chunk(2, [{ seq: 1, ts: 100, event: { event_type: 'hear', cycle: 3 } }]),
      )
    })
    expect(result.current.events).toHaveLength(1)
    expect(result.current.events[0].event.event_type).toBe('hear')
    expect(result.current.evHist).toContain(1)
  })

  it('dedups events already rendered by seq', async () => {
    vi.stubGlobal('EventSource', MockEventSource)
    const { result } = renderHook(() => useEvents(() => undefined))
    await act(async () => {})
    const es = MockEventSource.instances[0]
    const payload = chunk(1, [{ seq: 1, ts: 100, event: { event_type: 'x' } }])
    act(() => es.emitMessage(payload))
    act(() => es.emitMessage(payload))
    expect(result.current.events).toHaveLength(1)
  })

  it('caps the event log at 500 entries', async () => {
    vi.stubGlobal('EventSource', MockEventSource)
    const { result } = renderHook(() => useEvents(() => undefined))
    await act(async () => {})
    const es = MockEventSource.instances[0]
    const many = Array.from({ length: 501 }, (_, i) => ({
      seq: i,
      ts: i,
      event: { event_type: 'e' + i },
    }))
    act(() => es.emitMessage(chunk(501, many)))
    expect(result.current.events).toHaveLength(500)
  })

  it('falls back to polling and reconnects after an SSE error', async () => {
    vi.useFakeTimers()
    vi.stubGlobal('EventSource', MockEventSource)
    const fetchMock = jsonFetch({ after: 0, events: [] })
    vi.stubGlobal('fetch', fetchMock)
    renderHook(() => useEvents(() => undefined))
    await act(async () => {})
    const es = MockEventSource.instances[0]

    act(() => es.emitError())
    // flush the immediate poll refresh so its guard is released before the interval fires
    await act(async () => {})
    const callsAfterError = fetchMock.mock.calls.length
    act(() => vi.advanceTimersByTime(1200))
    await act(async () => {})
    expect(fetchMock.mock.calls.length).toBeGreaterThan(callsAfterError)

    const instancesBeforeReconnect = MockEventSource.instances.length
    act(() => vi.advanceTimersByTime(5000))
    await act(async () => {})
    expect(MockEventSource.instances.length).toBeGreaterThan(instancesBeforeReconnect)
  })

  it('reports connection state from SSE open and error', async () => {
    vi.useFakeTimers()
    vi.stubGlobal('EventSource', MockEventSource)
    vi.stubGlobal('fetch', jsonFetch({ after: 0, events: [] }))
    const report = vi.fn()
    renderHook(() => useEvents(report))
    await act(async () => {})
    const es = MockEventSource.instances[0]
    act(() => es.emitOpen())
    expect(report).toHaveBeenLastCalledWith(true)
    act(() => es.emitError())
    expect(report).toHaveBeenLastCalledWith(false)
  })

  it('does not open SSE or poll when disabled', async () => {
    vi.useFakeTimers()
    vi.stubGlobal('EventSource', MockEventSource)
    const fetchMock = jsonFetch({ after: 0, events: [] })
    vi.stubGlobal('fetch', fetchMock)
    renderHook(() => useEvents(() => undefined, { enabled: false }))
    await act(async () => {})
    act(() => vi.advanceTimersByTime(10000))
    await act(async () => {})
    expect(MockEventSource.instances).toHaveLength(0)
    expect(fetchMock.mock.calls.length).toBe(0)
  })

  it('resyncs the local window on a server gap signal', async () => {
    vi.stubGlobal('EventSource', MockEventSource)
    const { result } = renderHook(() => useEvents(() => undefined))
    await act(async () => {})
    const es = MockEventSource.instances[0]
    act(() => {
      es.emitMessage(chunk(2, [{ seq: 1, ts: 1, event: { event_type: 'old' } }]))
    })
    expect(result.current.events).toHaveLength(1)
    act(() => {
      es.emitMessage(
        JSON.stringify({
          after: 9500,
          gap: true,
          events: [{ seq: 9500, ts: 2, event: { event_type: 'fresh' } }],
        }),
      )
    })
    expect(result.current.events).toHaveLength(1)
    expect(result.current.events[0].event.event_type).toBe('fresh')
  })

  it('resyncs when the server epoch changes (server restart)', async () => {
    vi.stubGlobal('EventSource', MockEventSource)
    const { result } = renderHook(() => useEvents(() => undefined))
    await act(async () => {})
    const es = MockEventSource.instances[0]
    act(() => {
      es.emitMessage(
        JSON.stringify({ after: 100, epoch: 'aaa', events: [{ seq: 100, ts: 1, event: { event_type: 'old' } }] }),
      )
    })
    expect(result.current.events).toHaveLength(1)
    // server restarted: seqs reset, epoch differs — old cursor must not
    // swallow the fresh stream, and the stale window is replaced
    act(() => {
      es.emitMessage(
        JSON.stringify({ after: 2, epoch: 'bbb', events: [{ seq: 2, ts: 2, event: { event_type: 'new' } }] }),
      )
    })
    expect(result.current.events).toHaveLength(1)
    expect(result.current.events[0].event.event_type).toBe('new')
    // same epoch afterwards: normal cursor delivery continues
    act(() => {
      es.emitMessage(
        JSON.stringify({ after: 3, epoch: 'bbb', events: [{ seq: 3, ts: 3, event: { event_type: 'newer' } }] }),
      )
    })
    expect(result.current.events).toHaveLength(2)
  })

  it('ignores stale re-deliveries after a gap resync', async () => {
    vi.stubGlobal('EventSource', MockEventSource)
    const { result } = renderHook(() => useEvents(() => undefined))
    await act(async () => {})
    const es = MockEventSource.instances[0]
    act(() => {
      es.emitMessage(
        JSON.stringify({
          after: 5000,
          gap: true,
          events: [{ seq: 5000, ts: 1, event: { event_type: 'snap' } }],
        }),
      )
    })
    act(() => {
      es.emitMessage(chunk(5000, [{ seq: 42, ts: 2, event: { event_type: 'stale' } }]))
    })
    expect(result.current.events).toHaveLength(1)
    expect(result.current.events[0].event.event_type).toBe('snap')
  })
})

describe('EventDedup', () => {
  it('renders 100k in-order events exactly once in O(1) state', () => {
    const d = new EventDedup()
    let rendered = 0
    for (let i = 1; i <= 100000; i++) {
      if (d.isFresh(i)) {
        d.remember(i)
        rendered++
      }
      // duplicate delivery of an older sequence is dropped
      if (i % 10 === 0) expect(d.isFresh(i - 5)).toBe(false)
    }
    expect(rendered).toBe(100000)
    expect(d.lastSeq).toBe(100000)
    // O(1) state: only the cursor, no per-sequence retention
    expect(Object.keys(d)).toHaveLength(1)
  })

  it('drops duplicates and stale below-cursor sequences', () => {
    const d = new EventDedup()
    for (const s of [1, 2, 3]) d.remember(s)
    expect(d.isFresh(2)).toBe(false)
    expect(d.isFresh(3)).toBe(false)
    expect(d.isFresh(1)).toBe(false)
    expect(d.isFresh(4)).toBe(true)
    // a never-seen sequence below the cursor is stale tail data, not news
    expect(d.isFresh(0)).toBe(false)
  })

  it('resync adopts the fresh snapshot cursor', () => {
    const d = new EventDedup()
    for (let i = 1; i <= 5000; i++) d.remember(i)
    d.resync(9000)
    expect(d.lastSeq).toBe(9000)
    expect(d.isFresh(8501)).toBe(false)
    expect(d.isFresh(9001)).toBe(true)
  })
})
