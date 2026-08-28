import type { ReactNode } from 'react'
import type { ChatTurn } from '../../hooks/useChat'
import { Trace } from './Trace'

export interface TurnProps {
  turn: Pick<ChatTurn, 'role' | 'text' | 'trace'>
  children?: ReactNode
}

/** Chat bubble: avatar + who + bubble text + optional reasoning trace. */
export function Turn({ turn, children }: TurnProps) {
  const user = turn.role === 'user'
  return (
    <div className={'turn ' + (user ? 'end' : 'start')}>
      <div className="avat">{user ? 'U' : 'N'}</div>
      <div className="box">
        <div className="who">{user ? 'you' : 'novi'}</div>
        <div className="bubble">{children ?? turn.text}</div>
        {turn.trace && <Trace trace={turn.trace} />}
      </div>
    </div>
  )
}
