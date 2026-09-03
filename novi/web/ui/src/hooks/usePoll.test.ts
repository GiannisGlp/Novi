import { act, renderHook } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { jsonResponse } from '../test/helpers'
import { STATE_POLL_MS, useBrainState } from './useBrainState'
import { usePoll } from './usePoll'

describe('usePoll', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
    vi.useRealTimers()
  })

  it('runs immediately, then on the interval', async () => {
    vi.useFakeTimers()
    const cb = vi.fn().mockResolvedValue(undefined)
    renderHook(() => usePoll(cb, 1000))
    await act(async () => {})
    expect(cb).toHaveBeenCalledTimes(1)
    // One interval per flush, as in real time: synchronous back-to-back ticks
    // correctly count as overlap and are skipped by the in-flight guard.
    for (let i = 0; i < 3; i++) {
      act(() => {
        vi.advanceTimersByTime(1000)
      })
      await act(async () => {})
    }
    expect(cb).toHaveBeenCalledTimes(4)
  })

  it('skips ticks while the previous call is still in flight', async () => {
    vi.useFakeTimers()
    const fetchMock = vi
      .fn()
      .mockImplementation(() => new Promise<Response>(() => {})) // hangs forever
    vi.stubGlobal('fetch', fetchMock)
    renderHook(() => useBrainState(() => undefined))
    await act(async () => {})
    expect(fetchMock).toHaveBeenCalledTimes(1)
    // several intervals pass while the first request hangs: no pile-up
    act(() => {
      vi.advanceTimersByTime(STATE_POLL_MS * 5)
    })
    await act(async () => {})
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it('stops polling while the tab is hidden', async () => {
    vi.useFakeTimers()
    const vis = vi.spyOn(document, 'visibilityState', 'get').mockReturnValue('hidden')
    try {
      const fetchMock = vi.fn().mockImplementation(() => Promise.resolve(jsonResponse({})))
      vi.stubGlobal('fetch', fetchMock)
      renderHook(() => useBrainState(() => undefined))
      await act(async () => {})
      act(() => {
        vi.advanceTimersByTime(STATE_POLL_MS * 3)
      })
      await act(async () => {})
      expect(fetchMock).not.toHaveBeenCalled()
    } finally {
      vis.mockRestore()
    }
  })

  it('runs nothing when disabled', async () => {
    vi.useFakeTimers()
    const cb = vi.fn().mockResolvedValue(undefined)
    renderHook(() => usePoll(cb, 1000, false))
    await act(async () => {})
    act(() => {
      vi.advanceTimersByTime(5000)
    })
    await act(async () => {})
    expect(cb).not.toHaveBeenCalled()
  })
})
