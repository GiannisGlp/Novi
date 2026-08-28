import { useCallback, useEffect, useState } from 'react'

export type ThemeName = 'dark' | 'light' | 'nord'

const THEMES: readonly ThemeName[] = ['dark', 'light', 'nord']

function parseTheme(value: string | null): ThemeName {
  return THEMES.includes(value as ThemeName) ? (value as ThemeName) : 'dark'
}

/**
 * Theme state synced to <html data-theme> and localStorage('novi-theme').
 * Port of the legacy console's applyTheme().
 */
export function useTheme(): { theme: ThemeName; setTheme: (next: ThemeName) => void } {
  const [theme, setTheme] = useState<ThemeName>(() =>
    parseTheme(document.documentElement.getAttribute('data-theme') ?? localStorage.getItem('novi-theme')),
  )

  const applyTheme = useCallback((next: ThemeName) => {
    document.documentElement.setAttribute('data-theme', next)
    try {
      localStorage.setItem('novi-theme', next)
    } catch {
      /* private mode — theme just won't persist */
    }
    setTheme(next)
  }, [])

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
  }, [theme])

  return { theme, setTheme: applyTheme }
}
