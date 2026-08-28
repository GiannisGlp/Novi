import { act, renderHook } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { jsonFetch } from '../test/helpers'
import { HISTORY_CAP, useBrainState } from './useBrainState'

describe('useBrainState', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
    vi.useRealTimers()
  })

  it('loads state on mount and records the chart histories', async () => {
    vi.stubGlobal(
      'fetch',
      jsonFetch({ cycle: 12, run_id: 'abc', reasoning_trace: { confidence: 0.9 }, knowledge: { triples: 4 } }),
    )
    const report = vi.fn()
    const { result } = renderHook(() => useBrainState(report))
    await act(async () => {})
    expect(result.current.state?.cycle).toBe(12)
    expect(result.current.state?.run_id).toBe('abc')
    expect(result.current.confHist).toEqual([0.9])
    expect(result.current.memHist).toEqual([4])
    expect(report).toHaveBeenCalledWith(true)
  })

  it('polls on the 1s interval', async () => {
    vi.useFakeTimers()
    const fetchMock = jsonFetch({ cycle: 1 })
    vi.stubGlobal('fetch', fetchMock)
    const { result } = renderHook(() => useBrainState(() => undefined))
    await act(async () => {})
    const initialCalls = fetchMock.mock.calls.length
    act(() => vi.advanceTimersByTime(1000))
    await act(async () => {})
    expect(fetchMock.mock.calls.length).toBeGreaterThan(initialCalls)
    expect(result.current.state?.cycle).toBe(1)
  })

  it('keeps the last good state and reports disconnected on failure', async () => {
    const fetchMock = jsonFetch({ cycle: 5 })
    vi.stubGlobal('fetch', fetchMock)
    const report = vi.fn()
    const { result } = renderHook(() => useBrainState(report))
    await act(async () => {})
    expect(result.current.state?.cycle).toBe(5)

    fetchMock.mockImplementationOnce(() => new Response('boom', { status: 500 }))
    await act(async () => {
      await result.current.refresh()
    })
    expect(result.current.state?.cycle).toBe(5)
    expect(report).toHaveBeenLastCalledWith(false)
  })

  it('caps the histories at 60 samples', async () => {
    vi.useFakeTimers()
    const fetchMock = jsonFetch({ cycle: 1, reasoning_trace: { confidence: 0.5 }, knowledge: { triples: 2 } })
    vi.stubGlobal('fetch', fetchMock)
    const { result } = renderHook(() => useBrainState(() => undefined))
    await act(async () => {})
    act(() => vi.advanceTimersByTime(60000))
    await act(async () => {})
    expect(fetchMock.mock.calls.length).toBeGreaterThan(HISTORY_CAP)
    expect(result.current.confHist.length).toBeLessThanOrEqual(HISTORY_CAP)
    expect(result.current.memHist.length).toBeLessThanOrEqual(HISTORY_CAP)
  })
})
