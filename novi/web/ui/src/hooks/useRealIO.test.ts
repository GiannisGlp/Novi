import { act, renderHook } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { jsonFetch } from '../test/helpers'
import { useRealIO } from './useRealIO'

describe('useRealIO', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('loads the real-I/O status on mount', async () => {
    vi.stubGlobal('fetch', jsonFetch({ enabled: true, devices: { camera: true, mic: true, speaker: false } }))
    const { result } = renderHook(() => useRealIO(() => undefined))
    await act(async () => {})
    expect(result.current.status?.enabled).toBe(true)
    expect(result.current.status?.devices?.camera).toBe(true)
  })
})
