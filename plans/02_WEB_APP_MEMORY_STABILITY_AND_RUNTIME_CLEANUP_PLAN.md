# Novi Web App — Memory Stability, Resource Cleanup, and Runtime Optimization Plan

**Status:** Planned / implementation-ready  
**Priority:** P0 — stability critical  
**Scope:** Novi web application, web runtime, event delivery, polling, preview streaming, lifecycle management, tests, observability, and soak validation  
**Primary objective:** Stop progressive memory growth and out-of-memory failures while preserving every existing Novi capability and API behavior unless a change is explicitly documented as an internal implementation improvement.

---

## 1. Executive Summary

The Novi web application currently exhibits a high-confidence server-side memory leak and several secondary sources of unnecessary allocation and runtime pressure.

The most important finding is the interaction between:

1. `novi/brain/engine.py` maintaining a compatibility `MacBrain.events` list.
2. `MacBrain._emit()` continuously appending events to that list.
3. `novi/web/server.py` running the brain in `auto_step` mode.
4. The auto-step loop calling `brain.step()` without calling the legacy `_drain()` path that historically trims the compatibility event list.

The result is that the compatibility event list can grow without a hard upper bound. Because events can contain nested payloads, traces, perception data, state information, and other structured objects, this is not merely a small list of integers. It can retain a substantial amount of memory for the entire lifetime of the process.

There is a second independent client-side growth problem in `useEvents.ts`: `renderedSeqRef` is an unbounded `Set<number>`. Events are added to it indefinitely while the visible event list is capped. Long-running sessions therefore retain sequence IDs forever.

There are also important sources of avoidable allocation and CPU/network pressure:

- preview polling runs globally even when the Camera page is not active;
- multiple application hooks are mounted globally instead of being demand-driven by the active page;
- preview frames are repeatedly transferred as base64 data URLs and decoded by the browser;
- event storage is duplicated between the authoritative bounded `EventBus` and the compatibility list;
- request/event/preview concurrency does not have sufficiently explicit resource budgets;
- there is not yet a dedicated long-running memory regression/soak test that proves RSS remains bounded.

The cleanup must **not** solve the problem by disabling perception, vision, identity, object recognition, memory, knowledge, reasoning, autonomous stepping, chat, events, camera support, audio, planning, safety, or any other Novi capability.

The correct solution is to introduce explicit ownership, bounded retention, lifecycle-aware subscriptions, latest-value semantics for high-frequency data, backpressure, and resource budgets.

---

# 2. Goals

## 2.1 Primary goals

- Eliminate unbounded backend event retention.
- Eliminate unbounded frontend event-sequence retention.
- Make event ownership explicit.
- Keep high-frequency data bounded to the latest useful value where historical accumulation is unnecessary.
- Stop background polling for pages/features that are not active.
- Reduce browser allocation and garbage-collection pressure.
- Reduce unnecessary HTTP traffic.
- Prevent slow consumers from accumulating unlimited work/data.
- Establish hard memory/resource budgets.
- Add regression tests so the leak cannot silently return.
- Add a long-running soak test with real camera operation and LLM activity.
- Preserve all existing capabilities and externally visible behavior.

## 2.2 Secondary goals

- Make shutdown deterministic.
- Make start/stop/restart idempotent.
- Ensure timers, intervals, subscriptions, SSE connections, and background loops are released.
- Make event delivery resilient to slow browser clients.
- Improve observability of memory growth.
- Make future Jetson deployment safer by preventing desktop-only assumptions about unlimited memory.

---

# 3. Non-Goals

This plan does **not**:

- remove Novi capabilities;
- remove the EventBus;
- remove perception;
- remove camera processing;
- remove identity/person recognition;
- remove object recognition;
- remove chat or local LLM reasoning;
- remove autonomous stepping;
- remove memory/knowledge systems;
- replace the current cognition architecture;
- change model selection;
- reduce model quality merely to hide memory problems;
- solve OOM by restarting the process periodically;
- add arbitrary garbage collection calls as the primary solution;
- hide memory growth by clearing state that Novi legitimately needs.

The objective is **bounded, intentional memory ownership**, not feature reduction.

---

# 4. Current Architecture Relevant to the Problem

The current architecture contains two event-retention paths:

```text
Novi cognition / perception / runtime
        |
        v
   MacBrain._emit()
        |
        +----------------------+
        |                      |
        v                      v
 EventBus                 MacBrain.events
 bounded deque             compatibility list
 maxlen=4096               currently unbounded
        |                      |
        v                      v
 web/event consumers       legacy/server consumers
```

The EventBus already has a bounded queue and therefore represents the correct architectural direction.

The compatibility list should not become a second permanent event database.

The target architecture is:

```text
                         +----------------------+
                         |   Novi Brain Runtime |
                         +----------+-----------+
                                    |
                                    v
                             Authoritative
                              EventBus
                           bounded retention
                                    |
                 +------------------+------------------+
                 |                  |                  |
                 v                  v                  v
             Web API            SSE/stream          Internal
             snapshot           consumers           consumers
                 |                  |
                 v                  v
          bounded response    per-client cursor
```

Any compatibility representation must have a hard upper bound and must not become a second unbounded history.

---

# 5. Findings and Priority

| Priority | Finding | Impact | Required action |
|---|---|---|---|
| P0 | `MacBrain.events` can grow indefinitely in auto-step mode | Very high memory retention / likely direct OOM cause | Bound it independently of web draining |
| P0 | `useEvents.ts` keeps an unbounded `Set<number>` | Browser memory grows forever | Bound or eliminate the set |
| P1 | Preview polling runs globally | High allocation + CPU + network pressure | Make preview lifecycle/page aware |
| P1 | Most polling hooks mount globally | Persistent unnecessary work | Scope hooks to pages/features |
| P1 | Base64 preview frame churn | High temporary allocation and browser GC pressure | Latest-frame semantics and bounded payloads |
| P2 | Duplicate event stores | Avoidable memory duplication | EventBus becomes authoritative |
| P2 | No explicit web resource budgets | Future leaks can become catastrophic | Add configurable hard limits |
| P2 | No dedicated long-running memory regression | Leak can return unnoticed | Add soak test and RSS slope assertions |
| P3 | General frontend/runtime allocation cleanup | Performance improvement | Profile after P0/P1 fixes |

---

# 6. Phase 0 — Establish a Baseline Before Changing Behavior

## Step 0.1 — Record the exact current runtime configuration

Document:

- Python version.
- Node version.
- browser used for testing.
- operating system.
- Novi configuration.
- `auto_step` value.
- autonomous tick interval.
- perception cadence.
- camera FPS.
- preview interval.
- active local model.
- LLM context configuration.
- number of browser tabs.
- whether the camera is enabled.
- whether audio is enabled.
- whether identity/object recognition is enabled.

Do not modify these values for the baseline.

## Step 0.2 — Capture backend memory

Run the web application for controlled intervals:

- 1 minute;
- 5 minutes;
- 15 minutes;
- 30 minutes;
- 60 minutes.

Record:

- RSS;
- virtual memory;
- Python heap if available;
- event count;
- EventBus queue size;
- compatibility event-list size;
- active web clients;
- active background threads/tasks;
- request rate;
- preview request rate.

## Step 0.3 — Capture browser memory

Use browser tooling to record:

- JS heap size where available;
- DOM node count;
- event count displayed;
- size of client dedup state;
- preview update frequency;
- network request rate.

## Step 0.4 — Establish the failure signature

The test must determine whether memory follows this pattern:

```text
startup -> stable/low RSS
       -> autonomous runtime starts
       -> event count rises
       -> RSS rises
       -> browser traffic continues
       -> RSS eventually becomes excessive
       -> OOM
```

This baseline is important because fixes must be measured against the same workload.

---

# 7. Phase 1 — Fix the Backend Event Memory Leak

## Step 1.1 — Add an explicit event retention constant

Introduce a single authoritative configuration value for compatibility event retention.

Example concept:

```python
WEB_COMPAT_EVENT_HISTORY = 4096
```

The exact final constant should be configurable rather than hard-coded throughout the codebase.

Recommended default: approximately the same order of magnitude as the existing bounded EventBus history so the compatibility layer does not retain substantially more history than the authoritative store.

## Step 1.2 — Make `MacBrain.events` bounded

Do not rely on `_drain()` to keep this list bounded.

The brain itself must remain safe even when the web server is not consuming events.

Preferred implementation:

```python
from collections import deque

self.events = deque(maxlen=config.compat_event_history)
```

If changing the public type from `list` would break callers, use an internal bounded deque and expose a list-compatible snapshot API.

The important invariant is:

```text
len(MacBrain.events) <= configured maximum
```

under all runtime conditions.

## Step 1.3 — Audit all consumers of `brain.events`

Search the entire repository for:

```text
brain.events
self.events
.events[
.events[-
```

Classify every use:

1. historical compatibility read;
2. iteration;
3. append/write;
4. slicing;
5. testing;
6. web API response;
7. diagnostics.

Do not change behavior until every consumer is understood.

## Step 1.4 — Centralize compatibility-event insertion

Create one helper responsible for adding compatibility events.

Conceptually:

```python
def _append_compat_event(self, event: dict[str, Any]) -> None:
    self.events.append(event)
```

This creates one place where future retention policy can be enforced.

## Step 1.5 — Ensure event payloads do not retain unnecessary objects

Audit `_emit()` and event construction for:

- model objects;
- image objects;
- numpy arrays;
- tensors;
- embeddings;
- camera frame buffers;
- exceptions with large traceback/context chains;
- request objects;
- closures;
- mutable runtime objects.

Events should contain serializable summaries rather than references to large runtime objects.

Bad:

```python
{"frame": numpy_frame}
```

Preferred:

```python
{"frame_id": "...", "width": 640, "height": 480}
```

Bad:

```python
{"embedding": torch_tensor}
```

Preferred:

```python
{"embedding_id": "...", "dimension": 512}
```

If a consumer genuinely requires the data, it must retrieve it through an explicit bounded storage mechanism rather than having every event retain it.

## Step 1.6 — Fix `_drain()` semantics

The existing `_drain()` behavior must be reviewed even after bounding the underlying list.

The web server should not need to depend on a legacy trimming side effect.

`_drain()` should become a consumer/cursor operation rather than the mechanism that prevents OOM.

## Step 1.7 — Review auto-step behavior

Current behavior effectively allows:

```text
while running:
    brain.step()
```

without necessarily invoking the compatibility event drain path.

Do not simply insert `_drain()` everywhere as the primary fix.

First make event retention bounded at the source.

Then determine whether `_drain()` is still required for compatibility and invoke it only where semantically necessary.

## Step 1.8 — Add backend regression test

Create a test that emits substantially more events than the configured limit.

Example:

```text
limit = 4096
emit 100,000 events
assert len(events) <= 4096
assert newest event is retained
assert oldest retained event is within the expected window
```

The test must run with:

- auto-step enabled;
- auto-step disabled;
- web server absent;
- web server active.

The brain must remain bounded in all cases.

---

# 8. Phase 2 — Make the EventBus the Authoritative Event Store

## Step 2.1 — Define ownership

Document the rule:

> EventBus is the authoritative bounded event history and delivery mechanism. Compatibility event storage is only a bounded compatibility surface.

## Step 2.2 — Prevent duplicated long-term histories

Audit whether the same complete event payload is retained simultaneously in:

- EventBus;
- `MacBrain.events`;
- web server `_events`;
- client event state;
- browser dedup structures.

Where possible, keep only the minimum representation needed by each layer.

## Step 2.3 — Use sequence IDs/cursors

Event delivery should be cursor based:

```text
client has last_seq=N
request/stream asks for events after N
server returns bounded batch
client advances to newest seq
```

This is preferable to repeatedly transferring the same large history.

## Step 2.4 — Define behavior when a client falls behind

A client must not cause the server to retain an unlimited backlog.

If the requested sequence is older than the EventBus retention window:

```text
client cursor is stale
        |
        v
server reports history gap
        |
        v
client requests fresh bounded snapshot
        |
        v
client resumes from newest sequence
```

This preserves availability without requiring infinite retention.

---

# 9. Phase 3 — Fix Frontend `useEvents.ts` Memory Growth

## Step 3.1 — Identify the current leak

`useEvents.ts` maintains:

```typescript
const renderedSeqRef = useRef(new Set<number>())
```

Sequences are added as events arrive but the set is not bounded.

The displayed event collection may be limited to 500 items, but the sequence set can grow indefinitely.

## Step 3.2 — Preferred solution: cursor-based deduplication

Where the event stream/API guarantees monotonic sequence numbers, replace indefinite deduplication with a cursor:

```text
lastProcessedSeq
```

Only process events newer than the cursor.

This reduces memory from:

```text
O(number of events ever received)
```

to:

```text
O(1)
```

## Step 3.3 — Handle reconnects safely

The client must preserve the latest sequence cursor across reconnects.

On reconnect:

```text
request events after lastProcessedSeq
```

If the server reports that the cursor is too old:

```text
clear local event window
request current bounded snapshot
set cursor = newest sequence
```

## Step 3.4 — Fallback if a Set is still required

If some event sources can legitimately deliver out-of-order or duplicate sequences, use a bounded rolling Set.

Example policy:

```text
MAX_RENDERED_SEQUENCE_IDS = 1000
```

When the size exceeds the limit:

- remove the oldest sequence IDs;
- preserve the newest IDs;
- never allow indefinite growth.

## Step 3.5 — Add frontend regression test

Simulate at least 100,000 events.

Verify:

- rendered event window remains capped;
- dedup state remains bounded;
- no duplicate event rendering occurs;
- reconnect works;
- stale cursor recovery works.

---

# 10. Phase 4 — Stop Global Polling

## Step 4.1 — Audit `App.tsx`

The current application initializes many hooks globally, including functionality for:

- brain state;
- models;
- chat;
- preview;
- events;
- attention;
- context data;
- identity;
- current time.

This means pages that do not need a feature can still run its timers/network requests.

## Step 4.2 — Define page ownership

Create an explicit feature matrix.

| Feature | Overview | Chat | Camera | Events | Memory/Knowledge | Settings |
|---|---:|---:|---:|---:|---:|---:|
| Brain state | Yes | Optional | Optional | No | No | No |
| Chat | Optional | Yes | No | No | No | No |
| Preview | No | No | Yes | No | No | No |
| Events | Limited | No | Optional | Yes | No | No |
| Identity | Optional summary | No | Yes | No | Yes | No |
| Context | Summary | No | Yes | No | Yes | No |
| Attention | Yes | Optional | Yes | No | No | No |
| Models | Settings/status | Yes if needed | No | No | Yes if needed | Yes |

The final matrix must reflect actual routes in the codebase.

## Step 4.3 — Move hooks down the component tree

Instead of:

```text
App
 ├─ usePreview
 ├─ useIdentity
 ├─ useEvents
 ├─ useChat
 └─ ...
```

prefer:

```text
App
 └─ Router/Page shell
      ├─ OverviewPage -> state/attention
      ├─ ChatPage -> chat
      ├─ CameraPage -> preview/perception
      ├─ EventsPage -> events
      └─ MemoryPage -> memory/knowledge
```

This ensures unmounted pages release timers and subscriptions.

## Step 4.4 — Preserve shared state without shared polling

If multiple pages need the same information, use a shared cache/store with one controlled producer rather than one polling timer per consumer.

The rule is:

```text
shared data != globally active polling
```

## Step 4.5 — Verify cleanup on navigation

Navigate repeatedly:

```text
Overview -> Camera -> Events -> Chat -> Memory -> Overview
```

At every transition verify:

- old interval is cleared;
- old subscription is removed;
- old request is aborted where possible;
- old SSE connection is closed;
- no duplicate poller starts.

---

# 11. Phase 5 — Optimize Camera Preview Delivery

## Step 5.1 — Make preview demand-driven

Preview processing should run when there is an active consumer.

Do not continuously transfer preview frames to the browser when the Camera page is not visible.

## Step 5.2 — Use latest-frame semantics

Preview is a real-time value, not a historical event stream.

Never queue every frame.

The intended model is:

```text
camera produces frame 1
camera produces frame 2
camera produces frame 3
      |
      v
keep newest frame
      |
      v
browser consumes newest available frame
```

If the browser is slow, old frames should be discarded rather than accumulated.

## Step 5.3 — Bound preview size

Introduce configuration for:

- maximum width;
- maximum height;
- JPEG quality;
- maximum encoded bytes;
- maximum FPS.

Example conceptual defaults:

```text
WEB_PREVIEW_MAX_WIDTH
WEB_PREVIEW_MAX_HEIGHT
WEB_PREVIEW_JPEG_QUALITY
WEB_PREVIEW_MAX_BYTES
WEB_PREVIEW_FPS
```

Final values should be determined by profiling rather than arbitrarily reducing image quality.

## Step 5.4 — Avoid unnecessary base64 copies

Audit the current `/api/preview` path for:

```text
camera bytes
 -> encoded bytes
 -> base64 string
 -> JSON string
 -> React state
 -> image decode
```

This can create multiple simultaneous copies.

Prefer a streaming/binary/latest-frame approach if compatible with the existing frontend architecture.

If the API must remain JSON/base64 for compatibility, enforce strict payload limits and ensure only one current frame is retained.

## Step 5.5 — Abort stale preview requests

If a preview request is still in flight when a new one is scheduled:

- abort it where supported;
- do not queue another unlimited request;
- ensure only the latest result can update UI state.

## Step 5.6 — Prevent overlapping polling

A 300 ms interval must not create concurrent requests if the previous request is still running.

Use one of:

```text
request -> wait for completion -> schedule next
```

or an explicit in-flight guard.

Never allow:

```text
request 1 pending
request 2 pending
request 3 pending
...
```

---

# 12. Phase 6 — Add Explicit Web Resource Budgets

Introduce a central web-runtime resource budget configuration.

Recommended categories:

```text
WEB_MAX_EVENTS
WEB_MAX_CHAT_TURNS
WEB_MAX_PREVIEW_BYTES
WEB_PREVIEW_FPS
WEB_MAX_CONCURRENT_REQUESTS
WEB_MAX_SSE_CLIENTS
WEB_MAX_HISTORY
WEB_REQUEST_TIMEOUT
WEB_EVENT_BATCH_SIZE
WEB_MAX_EVENT_PAYLOAD_BYTES
```

## 12.1 Event budget

No API response should return an unbounded number of events.

## 12.2 Chat budget

The existing chat history is already bounded; preserve this behavior and make the limit explicit/configurable.

Do not retain complete conversation histories in the web process unless explicitly required by the cognition/memory system.

## 12.3 SSE budget

Each browser connection must have:

- a bounded queue;
- heartbeat behavior;
- disconnect detection;
- cleanup on disconnect;
- a maximum client count.

## 12.4 Request budget

Prevent unlimited concurrent requests from one browser or all browsers combined.

## 12.5 Payload budget

Reject or truncate oversized event payloads at the web boundary where appropriate.

Do not silently truncate data required by core cognition; instead use references/summaries for web presentation.

---

# 13. Phase 7 — Lifecycle and Shutdown Hardening

## Step 7.1 — Audit all background loops

Search for:

```text
Thread
threading
Timer
asyncio.create_task
create_task
setInterval
setTimeout
EventSource
WebSocket
subscribe
while ...
```

For every loop record:

- owner;
- start condition;
- stop condition;
- cancellation mechanism;
- resources retained;
- cleanup behavior.

## Step 7.2 — Make every worker owned by a lifecycle object

Each worker must have a clear:

```text
start()
stop()
join/cancel()
```

lifecycle.

## Step 7.3 — Make stop idempotent

Calling stop twice must be safe.

## Step 7.4 — Make start idempotent

Calling start twice must not create two background loops.

## Step 7.5 — Test repeated restarts

Run:

```text
start
stop
start
stop
```

at least 100 times in an automated test.

Verify thread/task counts return to baseline.

---

# 14. Phase 8 — Audit Event Payload Size and Object Retention

The number of events is only one dimension of memory usage. Event size matters equally.

## Step 8.1 — Inventory high-volume event types

Measure counts for:

- perception events;
- camera events;
- identity events;
- object events;
- attention events;
- reasoning events;
- planning events;
- action events;
- verification events;
- diagnostics;
- health metrics;
- chat events.

## Step 8.2 — Measure average and maximum serialized size

For each event type record:

```text
count/minute
average bytes
p95 bytes
p99 bytes
maximum bytes
```

## Step 8.3 — Remove accidental payload duplication

Look for repeated inclusion of:

- full world state;
- full conversation context;
- complete traces;
- embeddings;
- image data;
- large nested dictionaries.

Replace with IDs/references/summaries where appropriate.

## Step 8.4 — Preserve provenance

Optimization must not remove provenance, confidence, timestamps, sequence IDs, source identifiers, or safety-critical metadata needed by cognition/debugging.

The optimization is:

```text
large payload -> compact reference
```

not:

```text
large payload -> delete useful information
```

---

# 15. Phase 9 — Memory Profiling and Instrumentation

Add lightweight runtime metrics.

## 15.1 Backend metrics

Expose or log:

```text
process_rss_bytes
python_heap_bytes
compat_event_count
eventbus_queue_size
active_sse_clients
active_requests
preview_frame_bytes
worker_count
```

## 15.2 Frontend metrics

Where practical record:

```text
active_pollers
event_window_size
dedup_window_size
preview_updates_per_minute
inflight_preview_requests
active_event_connections
```

## 15.3 Growth-rate detection

Calculate RSS slope over a moving window.

Example interpretation:

```text
RSS stable around baseline -> healthy
small bounded oscillation -> healthy
continuous positive slope -> investigate
rapid positive slope -> fail soak test
```

The goal is not zero allocation. Normal applications allocate and release memory.

The target is **bounded long-term memory usage**.

---

# 16. Phase 10 — Automated Regression Tests

Create a dedicated web-runtime stability test suite.

## Test A — Event retention bound

Emit 100,000 events.

Expected:

```text
compatibility events <= configured limit
EventBus <= configured limit
```

## Test B — Auto-step event retention

Run autonomous stepping for a simulated long duration.

Expected:

```text
memory remains bounded
```

## Test C — Event reconnect

Connect client, receive events, disconnect, reconnect.

Expected:

- no duplicate accumulation;
- cursor resumes correctly;
- stale cursor is recovered correctly.

## Test D — Preview backpressure

Simulate a camera producing frames faster than the browser consumes them.

Expected:

```text
buffer size remains <= 1/latest-frame budget
```

## Test E — Preview cancellation

Start a preview request, navigate away, and cancel.

Expected:

- request is aborted or safely ignored;
- no state update after unmount;
- no retained response closure.

## Test F — Page navigation lifecycle

Perform thousands of page switches.

Expected:

```text
poller count returns to expected baseline
subscription count returns to expected baseline
```

## Test G — Server restart

Repeatedly start and stop the web server.

Expected:

- no accumulating threads;
- no accumulating tasks;
- no stale ports/resources;
- no duplicate loops.

## Test H — Large event payload

Inject oversized event payloads.

Expected:

- controlled handling;
- no unlimited memory retention;
- appropriate rejection/summarization.

---

# 17. Phase 11 — 30–60 Minute Realistic Soak Test

This is the acceptance test for the complete cleanup.

## Workload

Run Novi with:

- autonomous stepping enabled;
- real camera enabled;
- real neural perception enabled;
- identity/object recognition enabled where normally configured;
- local LLM enabled;
- web UI open;
- Camera page active for part of the test;
- Events page active for part of the test;
- Chat page active for part of the test;
- repeated page navigation;
- normal user interactions.

## Test sequence

```text
00:00 start Novi
00:02 open Overview
00:05 open Camera
00:10 open Events
00:15 send chat messages
00:20 navigate between pages
00:30 leave Camera
00:35 return to Camera
00:40 interact with chat
00:45 inspect events
00:50 return to Overview
01:00 stop
```

Record memory every 10–30 seconds.

## Acceptance criteria

The final thresholds must be calibrated against the machine, but the required properties are:

1. no unbounded event-list growth;
2. no unbounded frontend dedup growth;
3. no increasing number of background workers after navigation;
4. no increasing number of SSE clients after reconnects;
5. preview does not queue historical frames;
6. RSS reaches a bounded operating range;
7. RSS does not show a persistent runaway slope;
8. no OOM;
9. no capability regression;
10. no data-integrity regression.

---

# 18. Phase 12 — Capability Preservation Matrix

Every cleanup PR must explicitly verify that the following remain functional.

| Capability | Must remain |
|---|---|
| Local LLM reasoning | Yes |
| Chat | Yes |
| Autonomous brain stepping | Yes |
| Neural perception | Yes |
| Camera preview | Yes |
| Identity/person recognition | Yes |
| Object recognition | Yes |
| Attention | Yes |
| Working memory | Yes |
| Long-term memory | Yes |
| Knowledge graph | Yes |
| Planning | Yes |
| Action execution boundary | Yes |
| Verification | Yes |
| Safety interruption/recovery | Yes |
| Audio | Yes |
| EventBus | Yes |
| Event history | Yes, bounded |
| Diagnostics/metrics | Yes |
| Persistence | Yes |
| Web chat/state APIs | Yes unless explicitly versioned |
| Restart/recovery | Yes |

The distinction is critical:

> **Bounded history is not removed capability.**

Novi can still expose recent events and retrieve durable information through the correct subsystem without retaining every event forever in RAM.

---

# 19. Implementation Order

Do not implement these changes in random order.

## PR/commit 1 — Backend event safety

Implement:

1. event retention configuration;
2. bounded compatibility event storage;
3. `_emit()` audit;
4. payload retention audit;
5. event-bound regression tests.

Expected result: the highest-confidence OOM source is eliminated.

## PR/commit 2 — EventBus authority

Implement:

1. explicit event ownership;
2. cursor-based consumption;
3. stale cursor handling;
4. bounded API batches;
5. duplicate-history reduction.

## PR/commit 3 — Frontend event cleanup

Implement:

1. bounded/eliminated `renderedSeqRef`;
2. monotonic cursor;
3. reconnect handling;
4. event-window tests.

## PR/commit 4 — Page-local polling

Implement:

1. move hooks from `App.tsx` into owning pages;
2. preserve shared state where required;
3. verify unmount cleanup;
4. navigation tests.

## PR/commit 5 — Preview runtime

Implement:

1. active-page gating;
2. latest-frame semantics;
3. request cancellation;
4. no overlapping requests;
5. payload limits;
6. preview tests.

## PR/commit 6 — Resource budgets and lifecycle hardening

Implement:

1. web limits;
2. SSE limits;
3. request limits;
4. lifecycle ownership;
5. repeated start/stop tests.

## PR/commit 7 — Profiling and soak validation

Implement:

1. runtime metrics;
2. memory test harness;
3. 30–60 minute soak test;
4. capability regression suite;
5. final documentation.

---

# 20. Detailed Repository Audit Checklist

Before considering the work complete, search the repository for all of the following.

## Python

```text
append(
list[
dict[
deque
Queue
queue.Queue
asyncio.Queue
threading.Thread
Timer
create_task
EventSource
SSE
while True
while not
sleep(
```

## TypeScript/React

```text
useEffect
useRef
useState
setInterval
setTimeout
EventSource
WebSocket
fetch(
axios
subscribe
new Set
new Map
Array.push
```

For every occurrence, determine whether the lifetime is bounded.

---

# 21. Rules for Future Novi Web Development

These rules should become architectural constraints.

## Rule 1 — Every collection needs an ownership policy

Every long-lived list, map, set, queue, cache, or buffer must answer:

- Who owns it?
- What is its maximum size?
- When is it cleared?
- What happens when it reaches capacity?
- Does it contain references to large objects?

## Rule 2 — Real-time streams use latest-value semantics unless history is required

Camera frames, current sensor state, current preview, and similar data should not accumulate historically in RAM.

## Rule 3 — Events are bounded

No in-memory event collection may grow without a configured maximum.

## Rule 4 — Browser subscriptions are lifecycle scoped

A page that is not active should not continue polling merely because the application root is mounted.

## Rule 5 — Slow clients must not cause server memory growth

Backpressure and bounded queues are mandatory.

## Rule 6 — Persistent memory belongs in the appropriate persistence subsystem

RAM is not a substitute for durable memory.

## Rule 7 — Do not fix leaks by disabling features

When memory grows, identify the ownership/retention problem first.

## Rule 8 — Every new background worker requires a shutdown path

No worker may be created without an explicit owner and cancellation mechanism.

## Rule 9 — Every new cache requires a maximum

If an unlimited cache is genuinely required, its persistence/storage architecture must be explicit and justified rather than silently residing in process RAM.

## Rule 10 — Every high-frequency endpoint requires a rate and payload budget

This includes camera, sensor, event, metrics, and telemetry endpoints.

---

# 22. Failure Modes to Avoid

## Do not simply call `gc.collect()`

Garbage collection cannot free objects that are still strongly referenced by an unbounded list/set.

## Do not restart Novi periodically

Process restarts hide the symptom and destroy continuity. They are not a memory-management solution.

## Do not clear all events every few seconds

That would break debugging, observability, and event consumers.

Instead retain a bounded recent history and use durable storage where historical data is actually required.

## Do not disable camera/perception

This would hide allocation pressure by removing a core Novi capability.

## Do not reduce the LLM context as the first solution

The identified web/event retention problems must be fixed before changing cognition/model behavior.

## Do not remove the EventBus

It already provides bounded queue semantics and is the correct foundation.

## Do not globally increase browser polling intervals without understanding lifecycle

Lower frequency reduces pressure but does not fix an unbounded lifecycle or retention bug.

---

# 23. Definition of Done

The work is complete only when all of the following are true.

### Backend

- [ ] `MacBrain.events` has a hard maximum.
- [ ] EventBus has a hard maximum.
- [ ] No event producer can create an unbounded in-memory history.
- [ ] Event payloads do not accidentally retain large runtime objects.
- [ ] Auto-step cannot bypass memory safety.
- [ ] Event regression tests pass.

### Frontend

- [ ] `renderedSeqRef` is bounded or removed.
- [ ] Event cursor/reconnect logic is correct.
- [ ] Event display remains bounded.
- [ ] Preview does not run globally.
- [ ] Preview requests cannot overlap indefinitely.
- [ ] Preview retains only the latest useful frame.
- [ ] Page-local pollers stop on unmount.
- [ ] SSE/WebSocket connections close correctly.

### Lifecycle

- [ ] All background loops have owners.
- [ ] All workers have stop/cancel behavior.
- [ ] Start is idempotent.
- [ ] Stop is idempotent.
- [ ] Repeated restart tests pass.

### Resource budgets

- [ ] Event limits are configurable.
- [ ] Preview limits are configurable.
- [ ] Request concurrency is bounded.
- [ ] SSE clients are bounded.
- [ ] Payload sizes are bounded.

### Validation

- [ ] Unit tests pass.
- [ ] Integration tests pass.
- [ ] Frontend tests pass.
- [ ] Full existing test suite passes.
- [ ] Browser navigation test passes.
- [ ] Real camera test passes.
- [ ] Local LLM test passes.
- [ ] 30–60 minute soak test passes.
- [ ] No OOM occurs.
- [ ] Memory reaches a bounded steady operating range.
- [ ] All capability-preservation checks pass.

---

# 24. Expected Final Architecture

After implementation, the web runtime should follow these principles:

```text
                         +----------------+
                         |   Novi Brain   |
                         +-------+--------+
                                 |
                    +------------+------------+
                    |                         |
                    v                         v
              Current state             EventBus
              latest-value              bounded ring
                    |                         |
                    |                 +-------+-------+
                    |                 |               |
                    v                 v               v
                Web API            SSE client       API cursor
                    |
                    v
             Page-local hooks
                    |
        +-----------+-----------+
        |           |           |
        v           v           v
     Overview     Camera      Events
                    |
                    v
             Latest preview
                 frame only
```

Memory ownership becomes explicit:

```text
Persistent memory       -> persistence layer
Recent events            -> bounded EventBus
Compatibility events    -> bounded compatibility window
Current sensor state    -> latest-value state
Current preview          -> latest frame
Browser event history   -> bounded UI window
Event deduplication      -> cursor / bounded rolling window
Background workers       -> lifecycle owner
```

This architecture is appropriate not only for the current Mac web application but also for future resource-constrained Jetson deployment.

---

# 25. Final Engineering Principle

The central rule for this cleanup is:

> **Novi must be capable of running indefinitely without memory consumption increasing simply because time has passed.**

A long-running autonomous brain necessarily generates events, perceptions, observations, actions, conversations, metrics, and state transitions. The solution is not to stop generating useful information. The solution is to distinguish:

- transient data;
- latest state;
- bounded recent history;
- durable memory;
- stream delivery;
- diagnostics;
- large artifacts.

Each category must have an appropriate storage and lifecycle policy.

The web application should therefore become a **bounded, demand-driven presentation layer over the Novi brain**, rather than an additional uncontrolled memory store.

Once these changes are implemented and validated, Novi should retain its current capabilities while being substantially more suitable for continuous autonomous operation and eventual migration to Jetson-class hardware.
