import { act, renderHook } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { jsonFetch } from '../test/helpers'
import { useIdentity } from './useIdentity'

describe('useIdentity', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('loads the identity detail on mount', async () => {
    vi.stubGlobal(
      'fetch',
      jsonFetch({ current: { name: 'alice', tier: 'familiar', confidence: 0.92 } }),
    )
    const { result } = renderHook(() => useIdentity(() => undefined))
    await act(async () => {})
    expect(result.current.detail?.current?.name).toBe('alice')
    expect(result.current.detail?.current?.tier).toBe('familiar')
  })
})
