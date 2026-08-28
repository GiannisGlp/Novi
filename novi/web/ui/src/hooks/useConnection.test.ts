import { act, renderHook } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { useConnection } from './useConnection'

describe('useConnection', () => {
  it('starts connected and reports changes', () => {
    const { result } = renderHook(() => useConnection())
    expect(result.current.connected).toBe(true)
    act(() => result.current.reportConnection(false))
    expect(result.current.connected).toBe(false)
    act(() => result.current.reportConnection(true))
    expect(result.current.connected).toBe(true)
  })
})
