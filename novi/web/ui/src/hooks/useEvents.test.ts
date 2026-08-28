import { act, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { jsonFetch } from '../test/helpers'
import { MockEventSource } from '../test/helpers'
import { useEvents } from './useEvents'

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
})
