import { act, renderHook } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { jsonFetch, jsonResponse } from '../test/helpers'
import { useProposals } from './useProposals'

const PROPOSAL = {
  entity_ref: 'object-unresolved-cup',
  category: 'cup',
  label: 'cup',
  place: 'kitchen',
  seen_at: '2026-08-29T00:00:00+00:00',
}

describe('useProposals', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('loads proposals on mount', async () => {
    vi.stubGlobal('fetch', jsonFetch({ result: { proposals: [PROPOSAL] } }))
    const { result } = renderHook(() => useProposals(() => undefined))
    await act(async () => {})
    expect(result.current.proposals).toEqual([PROPOSAL])
  })

  it('reports disconnected and keeps null on failure', async () => {
    vi.stubGlobal('fetch', () => new Response('boom', { status: 500 }))
    const report = vi.fn()
    const { result } = renderHook(() => useProposals(report))
    await act(async () => {})
    expect(report).toHaveBeenLastCalledWith(false)
    expect(result.current.proposals).toBeNull()
  })

  it('nameObject returns null on success and refreshes the list', async () => {
    const fetchMock = jsonFetch({ result: { proposals: [PROPOSAL] } })
    vi.stubGlobal('fetch', fetchMock)
    const { result } = renderHook(() => useProposals(() => undefined))
    await act(async () => {})
    expect(result.current.proposals?.length).toBe(1)

    fetchMock.mockImplementationOnce(() =>
      jsonResponse({ result: { ok: true, object_id: 'object-my-mug', rebound: 3 } }),
    )
    let err: string | null = 'unset'
    await act(async () => {
      err = await result.current.nameObject('cup', 'my-mug')
    })
    expect(err).toBeNull()
    // the success path re-polls the list
    expect(fetchMock.mock.calls.length).toBeGreaterThan(1)
  })

  it('nameObject surfaces the server error message on failure', async () => {
    vi.stubGlobal('fetch', jsonFetch({ result: { proposals: [] } }))
    const { result } = renderHook(() => useProposals(() => undefined))
    await act(async () => {})

    vi.stubGlobal(
      'fetch',
      jsonFetch({ result: { ok: false, error: 'embedding required — no recent sighting of cup' } }),
    )
    let err: string | null = null
    await act(async () => {
      err = await result.current.nameObject('cup', 'my-mug')
    })
    expect(err).toContain('embedding required')
  })
})
