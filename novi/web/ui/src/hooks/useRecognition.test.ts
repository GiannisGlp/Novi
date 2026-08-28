import { act, renderHook } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { jsonFetch } from '../test/helpers'
import { useRecognition } from './useRecognition'

describe('useRecognition', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('loads enrollments on mount', async () => {
    vi.stubGlobal('fetch', jsonFetch({ enrollments: [{ kind: 'face', label: 'alice' }] }))
    const { result } = renderHook(() => useRecognition(() => undefined))
    await act(async () => {})
    expect(result.current.recognition?.enrollments).toEqual([{ kind: 'face', label: 'alice' }])
  })
})
