import { act, render } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { StatusBar } from './StatusBar'

describe('StatusBar', () => {
  afterEach(() => {
    vi.useRealTimers()
  })

  it('ticks the updated label locally', () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-01-01T00:00:00Z'))
    const { container } = render(<StatusBar connected lastUpdatedAt={Date.now()} />)
    expect(container.querySelector('#sbUpdated')?.textContent).toBe('updated just now')
    act(() => {
      vi.advanceTimersByTime(5000)
    })
    expect(container.querySelector('#sbUpdated')?.textContent).toBe('updated 5s ago')
  })

  it('shows a dash with no timestamp', () => {
    const { container } = render(<StatusBar connected lastUpdatedAt={null} />)
    expect(container.querySelector('#sbUpdated')?.textContent).toBe('updated —')
  })
})
