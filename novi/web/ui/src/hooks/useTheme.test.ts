import { act, renderHook } from '@testing-library/react'
import { beforeEach, describe, expect, it } from 'vitest'
import { useTheme } from './useTheme'

describe('useTheme', () => {
  beforeEach(() => {
    document.documentElement.removeAttribute('data-theme')
    localStorage.clear()
  })

  it('defaults to dark and syncs <html data-theme>', () => {
    const { result } = renderHook(() => useTheme())
    expect(result.current.theme).toBe('dark')
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
  })

  it('reads a persisted theme from localStorage', () => {
    localStorage.setItem('novi-theme', 'nord')
    const { result } = renderHook(() => useTheme())
    expect(result.current.theme).toBe('nord')
    expect(document.documentElement.getAttribute('data-theme')).toBe('nord')
  })

  it('applies setTheme to <html> and localStorage', () => {
    const { result } = renderHook(() => useTheme())
    act(() => result.current.setTheme('light'))
    expect(result.current.theme).toBe('light')
    expect(document.documentElement.getAttribute('data-theme')).toBe('light')
    expect(localStorage.getItem('novi-theme')).toBe('light')
  })

  it('ignores an unknown persisted value and falls back to dark', () => {
    localStorage.setItem('novi-theme', 'pink')
    const { result } = renderHook(() => useTheme())
    expect(result.current.theme).toBe('dark')
  })
})
