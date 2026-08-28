import type { BrainEvent } from '../api/types'
import { Section } from '../components/Section'
import { EventLog } from '../components/shared/EventLog'
import { Panel } from '../components/shared/Panel'

export interface EventsPageProps {
  events: BrainEvent[]
}

/** Events — the filterable brain event log. */
export function EventsPage({ events }: EventsPageProps) {
  return (
    <>
      <Section eyebrow="Events" title="Event log" desc="Everything the brain has processed, filterable by kind or cycle." />
      <Panel title="Log">
        <EventLog events={events} />
      </Panel>
    </>
  )
}
