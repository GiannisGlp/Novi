import { act, renderHook } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { jsonFetch, jsonResponse } from '../test/helpers'
import { usePreview } from './usePreview'

describe('usePreview', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
    vi.useRealTimers()
  })

  it('shows the frame when an image arrives', async () => {
    vi.stubGlobal('fetch', jsonFetch({ camera_health: 'healthy', image_data_url: 'data:image/jpeg;base64,abc' }))
    const { result } = renderHook(() => usePreview(() => undefined))
    await act(async () => {})
    expect(result.current.frame?.image_data_url).toBe('data:image/jpeg;base64,abc')
    expect(result.current.showImage).toBe(true)
  })

  it('hides the image after 3 consecutive empty polls', async () => {
    vi.useFakeTimers()
    const fetchMock = jsonFetch({ camera_health: 'offline' })
    vi.stubGlobal('fetch', fetchMock)
    const { result } = renderHook(() => usePreview(() => undefined))
    await act(async () => {})
    expect(result.current.showImage).toBe(false)

    act(() => vi.advanceTimersByTime(700))
    await act(async () => {})
    act(() => vi.advanceTimersByTime(700))
    await act(async () => {})
    act(() => vi.advanceTimersByTime(700))
    await act(async () => {})
    expect(result.current.showImage).toBe(false)

    // a frame with an image brings it back
    fetchMock.mockImplementation(() => jsonResponse({ image_data_url: 'data:image/jpeg;base64,xyz' }))
    act(() => vi.advanceTimersByTime(700))
    await act(async () => {})
    expect(result.current.showImage).toBe(true)
  })

  it('keeps the last frame on a fetch error without reporting disconnection', async () => {
    const fetchMock = jsonFetch({ image_data_url: 'data:image/jpeg;base64,abc' })
    vi.stubGlobal('fetch', fetchMock)
    const report = vi.fn()
    const { result } = renderHook(() => usePreview(report))
    await act(async () => {})
    expect(report).toHaveBeenLastCalledWith(true)

    fetchMock.mockImplementationOnce(() => new Response('boom', { status: 500 }))
    await act(async () => {
      await result.current.refresh()
    })
    expect(result.current.frame?.image_data_url).toBe('data:image/jpeg;base64,abc')
    expect(report).toHaveBeenLastCalledWith(true)
  })
})
