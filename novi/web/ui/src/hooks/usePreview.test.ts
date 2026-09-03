import { act, renderHook } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { jsonFetch, jsonResponse } from '../test/helpers'
import { PREVIEW_POLL_MS, usePreview } from './usePreview'

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

    act(() => vi.advanceTimersByTime(PREVIEW_POLL_MS))
    await act(async () => {})
    act(() => vi.advanceTimersByTime(PREVIEW_POLL_MS))
    await act(async () => {})
    act(() => vi.advanceTimersByTime(PREVIEW_POLL_MS))
    await act(async () => {})
    expect(result.current.showImage).toBe(false)

    // a frame with an image brings it back
    fetchMock.mockImplementation(() => jsonResponse({ image_data_url: 'data:image/jpeg;base64,xyz' }))
    act(() => vi.advanceTimersByTime(PREVIEW_POLL_MS))
    await act(async () => {})
    expect(result.current.showImage).toBe(true)
  })

  it('never runs overlapping requests while one is in flight', async () => {
    vi.useFakeTimers()
    let resolveFirst!: (r: Response) => void
    const fetchMock = vi.fn().mockImplementation(
      () =>
        new Promise<Response>((resolve) => {
          resolveFirst = resolve
        }),
    )
    vi.stubGlobal('fetch', fetchMock)
    renderHook(() => usePreview(() => undefined))
    await act(async () => {})
    expect(fetchMock).toHaveBeenCalledTimes(1)
    // several intervals pass while the first request hangs: no new requests
    act(() => vi.advanceTimersByTime(PREVIEW_POLL_MS * 5))
    await act(async () => {})
    expect(fetchMock).toHaveBeenCalledTimes(1)
    // once it resolves, polling resumes
    await act(async () => {
      resolveFirst(jsonResponse({ image_data_url: 'data:image/jpeg;base64,abc' }))
    })
    act(() => vi.advanceTimersByTime(PREVIEW_POLL_MS))
    await act(async () => {})
    expect(fetchMock.mock.calls.length).toBeGreaterThan(1)
  })

  it('aborts the in-flight request when disabled', async () => {
    const signals: AbortSignal[] = []
    const fetchMock = vi.fn().mockImplementation(
      (_url: string, init?: RequestInit) =>
        new Promise<Response>((_resolve, reject) => {
          const s = init?.signal
          if (s) {
            signals.push(s)
            s.addEventListener('abort', () => reject(new DOMException('aborted', 'AbortError')))
          }
        }),
    )
    vi.stubGlobal('fetch', fetchMock)
    const { rerender } = renderHook(({ enabled }: { enabled: boolean }) => usePreview(() => undefined, { enabled }), {
      initialProps: { enabled: true },
    })
    await act(async () => {})
    expect(fetchMock).toHaveBeenCalledTimes(1)
    expect(signals).toHaveLength(1)
    rerender({ enabled: false })
    await act(async () => {})
    expect(signals[0].aborted).toBe(true)
  })

  it('skips state updates for byte-identical frames', async () => {
    vi.useFakeTimers()
    const body = { camera_health: 'healthy', image_data_url: 'data:image/jpeg;base64,abc', detections: [] }
    vi.stubGlobal('fetch', jsonFetch(body))
    const { result } = renderHook(() => usePreview(() => undefined))
    await act(async () => {})
    const first = result.current.frame
    expect(first?.image_data_url).toBe('data:image/jpeg;base64,abc')
    // several identical polls: no new state object, no re-render trigger
    for (let i = 0; i < 4; i++) {
      act(() => vi.advanceTimersByTime(PREVIEW_POLL_MS))
      await act(async () => {})
    }
    expect(result.current.frame).toBe(first)
  })

  it('applies frames whose content actually changed', async () => {
    vi.useFakeTimers()
    const fetchMock = jsonFetch({ camera_health: 'healthy', image_data_url: 'data:image/jpeg;base64,abc' })
    vi.stubGlobal('fetch', fetchMock)
    const { result } = renderHook(() => usePreview(() => undefined))
    await act(async () => {})
    const first = result.current.frame
    fetchMock.mockImplementation(() =>
      jsonResponse({ camera_health: 'healthy', image_data_url: 'data:image/jpeg;base64,xyz' }),
    )
    act(() => vi.advanceTimersByTime(PREVIEW_POLL_MS))
    await act(async () => {})
    expect(result.current.frame).not.toBe(first)
    expect(result.current.frame?.image_data_url).toBe('data:image/jpeg;base64,xyz')
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
