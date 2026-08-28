import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../api/client'

export interface ModelsData {
  models: string[]
  current: string | null
  setModel: (name: string) => Promise<void>
  refresh: () => Promise<void>
}

/** Loads the available chat/reasoning models once; setModel posts the switch. */
export function useModels(reportConnection: (ok: boolean) => void): ModelsData {
  const [models, setModels] = useState<string[]>([])
  const [current, setCurrent] = useState<string | null>(null)
  const reportRef = useRef(reportConnection)
  reportRef.current = reportConnection

  const refresh = useCallback(async () => {
    try {
      const m = await api.model()
      reportRef.current(true)
      setModels(m.available ?? [])
      setCurrent(m.current ?? null)
    } catch {
      reportRef.current(false)
    }
  }, [])

  const setModel = useCallback(async (name: string) => {
    try {
      await api.setModel(name)
      setCurrent(name)
    } catch (err) {
      reportRef.current(false)
      throw err
    }
  }, [])

  useEffect(() => {
    void refresh()
  }, [refresh])

  return { models, current, setModel, refresh }
}
