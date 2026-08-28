import { act, renderHook } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { jsonFetch } from '../test/helpers'
import { useModels } from './useModels'

describe('useModels', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('loads models on mount', async () => {
    vi.stubGlobal(
      'fetch',
      jsonFetch({ available: ['qwen3:8b', 'llama3.2'], current: 'qwen3:8b' }),
    )
    const { result } = renderHook(() => useModels(() => undefined))
    await act(async () => {})
    expect(result.current.models).toEqual(['qwen3:8b', 'llama3.2'])
    expect(result.current.current).toBe('qwen3:8b')
  })

  it('setModel posts the switch and updates current', async () => {
    const fetchMock = jsonFetch({ available: ['a'], current: 'a' })
    vi.stubGlobal('fetch', fetchMock)
    const { result } = renderHook(() => useModels(() => undefined))
    await act(async () => {})
    await act(async () => {
      await result.current.setModel('qwen3:8b')
    })
    expect(fetchMock).toHaveBeenLastCalledWith('/api/model', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model: 'qwen3:8b' }),
    })
    expect(result.current.current).toBe('qwen3:8b')
  })

  it('reports disconnected when the model fetch fails', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('boom', { status: 500 })))
    const report = vi.fn()
    renderHook(() => useModels(report))
    await act(async () => {})
    expect(report).toHaveBeenLastCalledWith(false)
  })
})
