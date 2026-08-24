---
name: diagram-design
description: Design clear technical diagrams in Mermaid — flowcharts, sequence diagrams, state machines, ER models, class diagrams, and architecture graphs. Covers choosing the right diagram type, node/edge styling, layout readability, and colorblind-safe labeling. Use when a message asks to draw, design, or turn a description into an architecture diagram, flowchart, sequence chart, ER model, or any structured visual.
license: MIT
kind: instruction
triggers: diagram, flowchart, sequence-diagram, er-diagram, architecture-diagram, mermaid, state-machine-diagram
metadata:
  origin: original Novi skill (authored for Novi)
---

# Novi usage

Original Novi-authored skill. Output Mermaid code blocks so diagrams render
directly in Markdown contexts; the brain's FORBIDDEN guard and dialogue rules
run AFTER any text this skill helps produce.

# Diagram Design

## Step 1 — choose the right diagram type

| The question being answered | Diagram type | Mermaid keyword |
|---|---|---|
| What steps happen, and in what order? Any branches? | flowchart | `flowchart TD` |
| How do parties exchange messages over time? | sequence diagram | `sequenceDiagram` |
| How does one object's behavior change with events? | state diagram | `stateDiagram-v2` |
| What data does a system store and how does it relate? | ER diagram | `erDiagram` |
| What are the entities and their structure? | class diagram | `classDiagram` |
| Which components exist and what talks to what? | architecture graph | `flowchart LR` |

Pick by question, not by habit. If two types fit, prefer the one whose
failure mode is clearer to the reader.

## Step 2 — structure before syntax

1. List the actors/components and the relationships in plain sentences first.
2. One sentence = one edge; each sentence's subject/object = nodes.
3. Name nodes by role, not implementation ("payment service", not
   "PaymentServiceV2Handler").
4. Decide direction: top-down (`TD`) for processes/hierarchies, left-right
   (`LR`) for pipelines and architectures — LR fits wide systems better.

## Step 3 — syntax essentials

````text
flowchart LR
    user[User] --> api[API]
    api --> db[(Database)]
    api -- on failure --> retry[Retry queue]
    subgraph cluster[Edge layer]
        lb[Load balancer]
    end
    lb --> api
````

- Shapes carry meaning: `[rect]` process, `([rounded])` start/end,
  `{diamond}` decision, `[(database)]`, `[[subroutine]]`.
- Label edges with the condition or action (`-- yes -->`), never leave a
  decision branch unlabeled.
- `subgraph` groups components that share a boundary (deployment zone, team,
  lifecycle). Don't nest more than one level.

Sequence:

````text
sequenceDiagram
    autonumber
    client->>api: POST /orders
    api->>db: insert order
    db-->>api: id
    api-->>client: 201 Created
````

- Solid arrow `->>` is a request; dashed `-->>` is a response. Always pair them.
- `autonumber` helps readers reference steps in discussion.

State & ER quick forms:

````text
stateDiagram-v2
    [*] --> idle
    idle --> running: start
    running --> idle: stop

erDiagram
    USER ||--o{ ORDER : places
    ORDER }o--|| PRODUCT : references
````

Cardinality reads as `<left> <relation> <right>`: `||` exactly one, `o|` zero-or-one, `}o` many.

## Readability rules

1. **Directional consistency**: don't mix TD and LR flows in one diagram.
2. **Under 15 nodes** per diagram; beyond that, split into overview +
   detail diagrams linked from the text.
3. **Colorblind-safe emphasis**: rely on shape and label first; use fill
   classes (`class nodeName className`) sparingly and never color-only meaning.
4. Edge labels ≤ 4 words; move long explanations to surrounding prose.
5. Every decision diamond has at least two labeled outgoing edges.
6. No orphan nodes: every node connects to at least one edge.

## Answering style

Return one fenced ```mermaid block, preceded by one sentence stating what the
diagram shows and followed by any assumption you had to make ("assumed the
retry queue sits behind the API"). If the request is ambiguous between two
types, produce the more likely one and offer the alternative.
