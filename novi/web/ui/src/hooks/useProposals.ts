import { useCallback, useRef, useState } from 'react'
import { api } from '../api/client'
import type { RecognitionProposal } from '../api/types'
import { usePoll } from './usePoll'

export const PROPOSALS_POLL_MS = 3000

/**
 * Polls /api/recognition/proposals for novel objects awaiting a name (GAP-3).
 * Mirrors useRecognition: same poll cadence, same connection reporting, plus a
 * nameObject() action that binds a name and refreshes the list on success.
 */
export function useProposals(reportConnection: (ok: boolean) => void): {
  proposals: RecognitionProposal[] | null
  refresh: () => Promise<void>
  nameObject: (category: string, name: string) => Promise<string | null>
} {
  const [proposals, setProposals] = useState<RecognitionProposal[] | null>(null)
  const reportRef = useRef(reportConnection)
  reportRef.current = reportConnection

  const refresh = useCallback(async () => {
    try {
      const d = await api.proposals()
      reportRef.current(true)
      setProposals(d.result?.proposals ?? [])
    } catch {
      reportRef.current(false)
    }
  }, [])

  const nameObject = useCallback(
    async (category: string, name: string): Promise<string | null> => {
      try {
        const d = await api.nameObject({ category, name })
        if (d.result?.ok) {
          await refresh()
          return null
        }
        return d.result?.error ?? 'naming failed'
      } catch {
        return 'could not reach the server'
      }
    },
    [refresh],
  )

  usePoll(refresh, PROPOSALS_POLL_MS)
  return { proposals, refresh, nameObject }
}
