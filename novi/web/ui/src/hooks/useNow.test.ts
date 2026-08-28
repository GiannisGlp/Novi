import { act, renderHook } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { useNow } from './useNow'

describe('useNow', () => {
  afterEach(() => {
    vi.useRealTimers()
  })

  it('returns the current timestamp and ticks on the interval', () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date(2026, 0, 1, 12, 0, 0))
    const { result } = renderHook(() => useNow())
    const start = result.current
    vi.setSystemTime(new Date(2026, 0, 1, 12, 0, 2))
    act(() => vi.advanceTimersByTime(2000))
    expect(result.current).toBeGreaterThan(start)
  })
})
