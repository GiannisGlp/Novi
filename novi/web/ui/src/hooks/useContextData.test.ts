import { act, renderHook } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { jsonFetch } from '../test/helpers'
import { useContextData } from './useContextData'

describe('useContextData', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('loads the context package on mount', async () => {
    vi.stubGlobal(
      'fetch',
      jsonFetch({ package: { visible_entities: [{ entity_ref: 'alice', epistemic_status: 'observed' }] }, cycle: 3 }),
    )
    const { result } = renderHook(() => useContextData(() => undefined))
    await act(async () => {})
    expect(result.current.response?.package?.visible_entities?.[0]?.entity_ref).toBe('alice')
  })
})
