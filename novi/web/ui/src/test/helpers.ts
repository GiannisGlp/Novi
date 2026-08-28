import { vi } from 'vitest'

export function jsonResponse(body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  })
}

/** A fetch stub that returns a fresh Response per call (a Response body reads once). */
export function jsonFetch(body: unknown) {
  return vi.fn().mockImplementation(() => jsonResponse(body))
}

export function streamResponse(frames: string): Response {
  const enc = new TextEncoder()
  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      controller.enqueue(enc.encode(frames))
      controller.close()
    },
  })
  return new Response(stream, { status: 200 })
}

/** Minimal EventSource fake: trigger onopen/onmessage/onerror from tests. */
export class MockEventSource {
  static instances: MockEventSource[] = []
  static reset() {
    MockEventSource.instances = []
  }

  url: string
  onopen: (() => void) | null = null
  onmessage: ((e: MessageEvent) => void) | null = null
  onerror: (() => void) | null = null
  closed = false

  constructor(url: string) {
    this.url = url
    MockEventSource.instances.push(this)
  }

  close() {
    this.closed = true
  }

  emitOpen() {
    this.onopen?.()
  }

  emitMessage(data: string) {
    this.onmessage?.({ data } as MessageEvent)
  }

  emitError() {
    this.onerror?.()
  }
}
