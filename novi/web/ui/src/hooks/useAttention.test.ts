import { act, renderHook } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { jsonFetch } from '../test/helpers'
import { useAttention } from './useAttention'

describe('useAttention', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
    vi.useRealTimers()
  })

  it('loads the attention snapshot on mount', async () => {
    vi.stubGlobal('fetch', jsonFetch({ candidates: [{ id: 'alice', attention_score: 0.8 }] }))
    const { result } = renderHook(() => useAttention(() => undefined))
    await act(async () => {})
    expect(result.current.snapshot?.candidates?.[0]?.id).toBe('alice')
  })

  it('polls on the interval and keeps the last snapshot on failure', async () => {
    vi.useFakeTimers()
    const fetchMock = jsonFetch({ candidates: [{ id: 'bob', attention_score: 0.4 }] })
    vi.stubGlobal('fetch', fetchMock)
    const report = vi.fn()
    const { result } = renderHook(() => useAttention(report))
    await act(async () => {})
    expect(result.current.snapshot).toEqual({ candidates: [{ id: 'bob', attention_score: 0.4 }] })

    fetchMock.mockImplementationOnce(() => new Response('boom', { status: 500 }))
    act(() => vi.advanceTimersByTime(1100))
    await act(async () => {})
    expect(result.current.snapshot?.candidates?.[0]?.id).toBe('bob')
    expect(report).toHaveBeenLastCalledWith(false)
  })
})
