# 08 — Memory Indexing and Embeddings

## Status

**DESIGN — V1 INDEXING ARCHITECTURE**

## Purpose

Define how Novi transforms canonical memory and knowledge into searchable derived indexes, how embeddings are generated and versioned, how exact and semantic retrieval coexist, how indexes are rebuilt, and how the entire system remains local-first and practical on the target **NVIDIA Jetson AGX Orin 64GB**.

This document deliberately separates **canonical memory** from **search infrastructure**. The database and artifact store preserve what Novi has deliberately admitted. Indexes make that information discoverable. Losing an index must never mean losing memory.

---

## 1. Executive Architecture

The V1 indexing system is a hybrid retrieval substrate:

```text
                         CANONICAL MEMORY
                                │
                    ┌───────────┴───────────┐
                    │                       │
              structured data          artifacts/text
                    │                       │
                    └───────────┬───────────┘
                                │
                         Indexing Pipeline
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
              ▼                 ▼                 ▼
          SQLite/SQL          FTS5           Embeddings
          structured        lexical index     semantic index
              │                 │                 │
              └─────────────────┼─────────────────┘
                                │
                       Hybrid Retrieval Layer
                                │
                   metadata + temporal filters
                                │
                         candidate fusion
                                │
                           reranking
                                │
                         context builder
                                │
                           cognition
```

The architecture is intentionally compatible with NVIDIA NeMo Retriever, but does not make NeMo mandatory. NVIDIA's current NeMo Retriever Library supports extraction, embedding generation and embedded LanceDB storage; its documented embedded path uses LanceDB and supports metadata filtering. A different vector backend can be used through an adapter when it benchmarks better for Novi. [NVIDIA NeMo Retriever — Vector Databases](https://docs.nvidia.com/nemo/retriever/latest/extraction/vdbs/) and [NVIDIA NeMo Retriever Library](https://docs.nvidia.com/nemo/retriever/latest/).

---

## 2. Core Principles

### 2.1 Canonical data is authoritative

Embeddings, FTS indexes, caches, ANN indexes and reranking artifacts are derived state.

```text
canonical record
      │
      ├── lexical index
      ├── embedding
      ├── vector index
      └── retrieval metadata
```

The derived objects can be deleted and regenerated.

### 2.2 Similarity is not truth

A high cosine similarity score means that two representations are close in embedding space. It does **not** establish:

- truth;
- authorization;
- identity;
- freshness;
- provenance;
- relevance to the current task;
- safety.

Semantic retrieval therefore produces candidates. The retrieval/ranking policy decides which candidates can enter context.

### 2.3 Exact and semantic retrieval are complementary

Exact retrieval is superior for identifiers, names, precise phrases, dates, codes and technical terms. Semantic retrieval is superior when wording differs while meaning is similar.

Novi therefore uses both.

### 2.4 Indexing must be local-first

The preferred embedding and indexing path is local on the development machine and ultimately on the robot. Cloud embedding APIs are exceptional dependencies and require an explicit architectural exception.

### 2.5 Models are replaceable

An embedding model is an implementation component, not a permanent memory contract. Every embedding is associated with its model identity, model version, dimension, preprocessing contract and content hash.

### 2.6 Reproducibility matters

Given the same canonical content, embedding model version and preprocessing configuration, Novi should be able to reproduce an embedding or explain why exact reproduction is not possible.

### 2.7 Indexing is asynchronous by default

Durable memory admission should not normally wait for a vector index update. Canonical persistence is the primary transaction; derived indexing can be queued and retried.

### 2.8 Retrieval must tolerate stale indexes

A record can exist canonically before it appears in a vector or FTS index. Retrieval must expose index freshness rather than pretending the index is perfectly synchronized.

---

## 3. Index Taxonomy

Novi should maintain several complementary index classes.

### 3.1 Relational indexes

SQLite B-tree indexes support structured filtering and joins:

- entity ID;
- memory type;
- status;
- timestamps;
- validity interval;
- privacy class;
- source;
- relationship predicates.

These should be the first filter whenever the query has structured constraints.

### 3.2 Full-text index

SQLite FTS5 is the initial lexical search candidate. It is appropriate for local exact/term-oriented retrieval and supports tokenization and prefix search.

FTS is derived state and must reference canonical IDs rather than become a second source of truth.

### 3.3 Dense vector index

Embeddings provide semantic retrieval. The initial implementation should prefer an embedded/local vector index to avoid introducing a network service solely for memory search.

Candidate technologies include:

- `sqlite-vec` for a SQLite-integrated local design;
- LanceDB for an embedded vector database;
- another mature local ANN implementation if benchmarks justify it.

`sqlite-vec` is currently pre-v1 and explicitly warns that breaking changes are possible, so it is a candidate rather than a locked dependency. It supports float, int8 and binary vectors and runs wherever SQLite runs. [sqlite-vec](https://github.com/asg017/sqlite-vec)

NVIDIA currently documents LanceDB as the first-party embedded vector database path for NeMo Retriever Library. NVIDIA describes its LanceDB path as in-process and uses an IVF-HNSW-SQ index, combining approximate nearest-neighbor search with scalar quantization. [NVIDIA NeMo Retriever Vector Databases](https://docs.nvidia.com/nemo/retriever/latest/extraction/vdbs/)

### 3.4 Graph/relationship indexes

Relationship traversal is initially handled by relational tables and indexes. Novi should not introduce a graph database merely because it has relationships.

A graph engine becomes justified only when measured traversal workloads demonstrate that relational traversal is insufficient.

### 3.5 Artifact indexes

Artifacts have metadata indexes in SQLite and may have derived textual, visual or audio representations. The artifact itself remains canonical in managed storage.

---

## 4. Canonical-to-Index Pipeline

```text
Canonical memory admitted
        ↓
content normalization
        ↓
content hash
        ↓
index eligibility policy
        ↓
┌───────┼──────────┬────────────┐
│       │          │            │
SQL    FTS      embedding    artifact
index  update     generation   index
│       │          │            │
└───────┴──────────┴────────────┘
              ↓
        index manifest
              ↓
        index consistency
```

### Index eligibility

Not every memory should be embedded.

Embedding candidates should be evaluated using:

- memory type;
- text/semantic content availability;
- privacy class;
- expected retrieval value;
- size;
- duplication;
- expiration;
- access frequency;
- language/modality support;
- resource budget.

Examples:

- a short-lived sensor heartbeat → normally no embedding;
- a durable personal preference → likely embed;
- a large document → chunk and embed selected chunks;
- a binary image → use a multimodal embedding only if image retrieval is actually required;
- an audit event → normally relational/FTS only.

---

## 5. Content Normalization

Embedding quality depends on the representation supplied to the model.

Before embedding, Novi should construct a deterministic **embedding projection** rather than simply dumping an entire database row into the model.

Example:

```text
Memory:
  subject = coffee
  claim = prefers cold brew
  source = user-confirmed
  valid_from = 2026-08-01

Embedding projection:
  "User preference: coffee preference — cold brew."
```

Do not embed internal database identifiers unless they carry semantic value.

Do not include secrets, access tokens, internal policy text or unrelated private fields merely because they are present in the source record.

### Projection version

Every embedding must record:

```text
projection_id
projection_version
normalization_version
chunking_version
model_id
model_version
```

A change to any of these may require re-embedding.

---

## 6. Content Hashing

Every indexable object should have a canonical content hash.

```text
canonical content
      ↓
canonical serialization
      ↓
SHA-256 or approved content hash
      ↓
content_hash
```

The hash is used for:

- duplicate detection;
- idempotent indexing;
- stale embedding detection;
- migration verification;
- index rebuilds;
- integrity checks.

An embedding record is stale when:

```text
embedding.content_hash != current.content_hash
```

The system should not silently use stale embeddings when a current representation is available and the query requires freshness.

---

## 7. Embedding Record

The conceptual V1 embedding metadata record is:

```text
embedding_id
subject_type
subject_id
chunk_id
model_id
model_version
model_revision
projection_id
projection_version
normalization_version
modality
dimensions
embedding_type
encoding_format
content_hash
created_at
status
index_version
```

Optional metadata:

```text
language
privacy_class
source_type
valid_from
valid_until
```

The vector itself can be stored by the selected vector backend; the canonical metadata remains under Novi's control.

---

## 8. Model Selection

The embedding model must be selected independently from the primary reasoning model.

There is no requirement that Nemotron be used to generate embeddings.

Candidate selection criteria:

1. retrieval quality on Novi's data;
2. multilingual performance where required;
3. text vs multimodal capability;
4. embedding dimension;
5. memory footprint;
6. latency;
7. throughput;
8. CPU/GPU requirements;
9. licensing;
10. local deployment support;
11. quantization options;
12. maintainability;
13. model stability;
14. Jetson compatibility.

NVIDIA currently exposes NeMo Retriever Embedding NIM with an OpenAI-compatible embeddings API and model metadata, including model ID, input modality, embedding type and dimensions. The documented API also distinguishes `query` and `passage` input types for supported models. [NVIDIA NeMo Retriever Embedding NIM API](https://docs.nvidia.com/nim/nemo-retriever/text-embedding/latest/reference.html)

That distinction is important: if a model is trained with asymmetric query/document representations, Novi must preserve the correct input role rather than embedding both sides identically.

---

## 9. Embedding Model Registry

Novi should maintain an embedding model registry.

Conceptual record:

```text
embedding_model_id
provider
model_name
model_revision
license
modalities
languages
dimensions
max_input_tokens
query_instruction
passage_instruction
normalization
runtime
quantization
hardware_profile
status
benchmark_version
```

The registry must record enough information to reproduce the indexing configuration.

### Example states

```text
AVAILABLE
BENCHMARKING
ACTIVE
DEPRECATED
MIGRATING
RETIRED
```

Only one model/version should be the default for a particular index namespace unless an explicit multi-model strategy is configured.

---

## 10. One Embedding Space Is Not Enough

Novi should not assume that every modality belongs in one vector space.

Potential spaces include:

```text
text semantic space
image semantic space
text-image multimodal space
audio semantic space
code/technical space
```

A multimodal model may allow shared retrieval across modalities, but this must be validated empirically.

The index metadata must identify the embedding space/model so incompatible vectors cannot be compared accidentally.

```text
embedding_space_id
```

is therefore recommended.

---

## 11. Chunking

Documents and long memories require chunking before embedding.

Chunking should be semantic where possible rather than blindly splitting every N characters.

A chunk record should retain:

```text
chunk_id
parent_artifact_id
parent_memory_id
sequence_number
start_offset
end_offset
heading_path
content_hash
chunking_version
```

### Chunk requirements

A chunk should:

- contain enough context to stand alone during retrieval;
- be small enough to avoid wasting context budget;
- preserve document hierarchy;
- retain provenance to the parent artifact;
- avoid duplicating large amounts of neighboring text;
- be independently deletable when privacy policy requires it.

### Overlap

Overlap may improve retrieval continuity but increases index size and duplication. Overlap must therefore be benchmarked rather than chosen by convention.

---

## 12. Temporal Indexing

Memory is time-sensitive.

Vector similarity must not be the only mechanism for temporal retrieval.

The retrieval layer should combine vector similarity with relational temporal constraints:

```text
semantic similarity
        +
valid_from / valid_until
        +
observed_at
        +
last_confirmed_at
        +
current world state
```

For current-state questions, stale historical memories should not outrank authoritative current state merely because their embeddings are similar.

---

## 13. Privacy-Aware Indexing

Privacy classification must propagate to derived indexes.

```text
canonical memory
      ↓
privacy class
      ↓
FTS eligibility
embedding eligibility
vector metadata
artifact eligibility
```

A private record must not become retrievable through a derived index after its canonical access policy would have denied it.

### Deletion requirement

When a memory is purged:

1. mark canonical record for deletion;
2. delete or invalidate FTS entry;
3. delete vector entry;
4. delete chunk records;
5. remove artifact references where applicable;
6. invalidate caches;
7. record the operation in audit storage;
8. verify no retrievable derived copy remains within the applicable storage scope.

Backups are governed by the retention/deletion policy defined in the storage architecture.

---

## 14. Incremental Indexing

The normal path is incremental.

```text
new/changed memory
       ↓
index job
       ↓
only affected indexes updated
```

A memory update should not trigger a full rebuild.

Each index job should contain:

```text
job_id
subject_id
index_type
content_hash
model_version
attempt
created_at
status
error_code
```

Jobs must be idempotent.

---

## 15. Index Queue

A local durable queue should separate canonical persistence from derived indexing.

```text
memory transaction
      ↓
index event
      ↓
local queue
      ↓
worker
      ├── FTS
      ├── embedding
      └── vector index
```

The queue itself should have bounded growth and retry policy.

If the robot is offline from a cloud service, the queue must not block canonical local memory writes.

Because Novi is local-first, cloud unavailability should normally only delay an optional external index, not memory admission.

---

## 16. Embedding Generation Modes

### 16.1 Synchronous

Generate the embedding before returning from memory admission.

Use only when:

- retrieval must be immediately available;
- latency is acceptable;
- the workload is small.

### 16.2 Asynchronous

Persist memory first and generate embedding later.

This is the preferred default for the robot.

### 16.3 Deferred

Generate only when retrieval value becomes high enough to justify the resource cost.

Example:

```text
new memory
   ↓
not embedded yet
   ↓
frequently accessed / promoted
   ↓
embedding requested
```

This can reduce unnecessary GPU work.

---

## 17. Query Embeddings vs Passage Embeddings

Where the selected model supports asymmetric retrieval, Novi must distinguish:

```text
user/cognitive query → query embedding
memory/document      → passage embedding
```

NVIDIA's current embedding API explicitly exposes `input_type` values such as `query` and `passage` for supported models. [NVIDIA Embedding NIM API](https://docs.nvidia.com/nim/nemo-retriever/text-embedding/latest/reference.html)

The model registry must record whether a model requires this distinction.

---

## 18. Vector Precision and Compression

The V1 architecture must support more than one vector representation:

```text
float32
float16 / equivalent reduced precision
int8
binary
```

The correct choice depends on the embedding model and vector backend.

`sqlite-vec` currently documents support for float, int8 and binary vectors. NVIDIA's LanceDB path uses scalar quantization within its IVF-HNSW-SQ configuration. These are strong reasons to treat precision/quantization as a benchmark parameter rather than a fixed architectural assumption. [sqlite-vec](https://github.com/asg017/sqlite-vec) [NVIDIA NeMo Retriever Vector Databases](https://docs.nvidia.com/nemo/retriever/latest/extraction/vdbs/)

### Rule

Never quantize solely to save storage without measuring retrieval quality loss.

Benchmark:

- Recall@K;
- precision@K;
- ranking quality;
- memory consumption;
- latency;
- index build time.

---

## 19. Index Choice: Brute Force vs ANN

Approximate nearest-neighbor indexing is not automatically better.

For a small number of vectors, brute-force search can be simpler and fast enough.

As the corpus grows, ANN can reduce query cost at the expense of index complexity and sometimes recall.

The architecture should therefore support:

```text
small corpus → exact vector scan
large corpus → ANN index
```

The transition threshold must be benchmarked on Novi's actual workload.

This is consistent with local SQLite vector implementations that can use brute-force search for smaller datasets and specialized indexes for larger datasets. For example, current `sqlite-vec` implementations support multiple index strategies. [sqlite-vec](https://github.com/viant/sqlite-vec)

---

## 20. Candidate Vector Backends

### 20.1 SQLite-integrated vector search

**Candidate:** `sqlite-vec`.

Advantages:

- local;
- small deployment footprint;
- SQLite integration;
- no separate vector service;
- suitable for Mac and edge experimentation;
- supports multiple vector data types.

Risks:

- currently pre-v1;
- ecosystem maturity;
- ANN feature set and performance must be benchmarked;
- extension management becomes part of deployment.

### 20.2 LanceDB

**Candidate:** LanceDB.

Advantages:

- embedded/in-process;
- explicitly supported in NVIDIA NeMo Retriever Library;
- metadata filtering;
- ANN indexing;
- no separate vector database service for the embedded path.

Risks:

- additional storage subsystem beyond SQLite;
- operational/data-model complexity;
- must validate Jetson support and performance for Novi's exact runtime;
- canonical-memory integration must remain under Novi's control.

NVIDIA currently documents LanceDB as the validated embedded vector path for NeMo Retriever Library and describes its local retrieval stack using Lance format and IVF-HNSW-SQ. [NVIDIA NeMo Retriever Vector Databases](https://docs.nvidia.com/nemo/retriever/latest/extraction/vdbs/)

### 20.3 Other local vector stores

Other open-source local stores may be evaluated when benchmarks show a meaningful advantage.

No remote vector database is required for V1.

---

## 21. NVIDIA NeMo Retriever Integration

NVIDIA's current NeMo Retriever Library provides a pipeline that can extract content from multiple media types, generate embeddings, and upload them to a vector database. Its documented embedded vector path is LanceDB. [NVIDIA NeMo Retriever Library](https://docs.nvidia.com/nemo/retriever/latest/)

For Novi, the integration boundary should be:

```text
Novi Indexing API
       │
       ├── Native Local Indexer
       │
       └── NeMo Adapter
               │
        NeMo Retriever
               │
          LanceDB / selected backend
```

NeMo should not own the canonical memory database.

The adapter must map:

- Novi memory ID;
- chunk ID;
- provenance;
- privacy class;
- validity interval;
- embedding model metadata;
- canonical content hash;
- index version.

### Why this matters

If NVIDIA later provides a better embedding/retrieval implementation, Novi can adopt it without rewriting memory semantics.

If another open-source system proves better, Novi can replace the adapter.

---

## 22. Jetson AGX Orin 64GB Strategy

The Jetson target is not simply a smaller server. Indexing competes with perception, speech, vision, navigation, cognition and thermal/power budgets.

### Default policy

```text
real-time robot workloads
        ↓
highest priority

memory writes
        ↓
high priority

FTS/index maintenance
        ↓
medium priority

embedding generation
        ↓
background priority

large re-indexing
        ↓
lowest priority
```

### Resource-aware worker

The indexing worker should monitor:

- GPU availability;
- CPU utilization;
- RAM;
- storage capacity;
- storage I/O latency;
- thermal state;
- power mode;
- queue depth.

When resources are constrained:

```text
pause/reduce batch size
        ↓
prioritize current retrieval needs
        ↓
defer non-critical embeddings
        ↓
resume during idle windows
```

### Important architectural rule

The robot must never sacrifice safety-critical perception or autonomy simply to keep the vector index perfectly synchronized.

---

## 23. Mac Development Profile

Mac is the primary development/test environment before Jetson integration.

The Mac profile should support:

- full corpus indexing;
- benchmark datasets;
- embedding model comparison;
- FTS testing;
- vector backend comparison;
- migration tests;
- retrieval evaluation;
- deterministic replay.

The same `IndexingService` interface must be used on Mac and Jetson.

Only the implementation profile changes.

```text
             Indexing API
                  │
          ┌───────┴────────┐
          │                │
       macOS profile    Jetson profile
          │                │
      heavier jobs      resource-aware
```

---

## 24. Re-indexing

A full re-index is required when a fundamental indexing contract changes.

Examples:

- embedding model change;
- embedding dimension change;
- projection version change;
- chunking algorithm change;
- tokenizer/index configuration change;
- vector backend migration;
- corruption;
- privacy policy migration.

### Safe migration

```text
existing canonical data
        ↓
new index namespace
        ↓
build in background
        ↓
validate
        ↓
benchmark
        ↓
atomic activation
        ↓
retire old index
```

Never destroy the only working index before the replacement has been validated.

---

## 25. Index Namespaces

Indexes should be namespaced by semantic configuration.

Example:

```text
memory_semantic/
  model=nvidia-nemotron-embed-1b/
  revision=...
  projection=v3/
  dimensions=...
```

The exact physical naming is implementation-specific, but the conceptual namespace must exist.

This prevents accidental comparison of incompatible vector spaces.

---

## 26. Index Consistency States

Every derived index should expose a state:

```text
CURRENT
BUILDING
STALE
DEGRADED
CORRUPTED
REBUILD_REQUIRED
DISABLED
```

### CURRENT

Index reflects the relevant canonical data version.

### STALE

Some canonical updates are not indexed yet.

### DEGRADED

The index is usable but incomplete or operating under a fallback.

### CORRUPTED

Integrity verification failed.

### REBUILD_REQUIRED

The index cannot safely be incrementally repaired.

Cognition should be able to request retrieval while knowing which state it is using.

---

## 27. Hybrid Retrieval Contract

The indexing layer exposes candidate retrieval rather than final truth.

```text
retrieve(query)
    ↓
structured filters
    ↓
FTS candidates
    ↓
vector candidates
    ↓
candidate union
    ↓
deduplicate
    ↓
metadata/authorization filters
    ↓
validity filtering
    ↓
ranking/reranking
```

This connects directly to `05_MEMORY_RETRIEVAL_AND_RANKING.md`.

### Candidate metadata

Every candidate should expose:

```text
memory_id
retrieval_method
raw_score
normalized_score
index_version
model_version
freshness
provenance_ref
privacy_class
validity
```

The ranker should never have to guess where a candidate came from.

---

## 28. Score Normalization

Scores from different retrieval systems are not directly comparable.

For example:

```text
FTS score ≠ cosine similarity ≠ BM25-like score
```

The hybrid layer must normalize scores before fusion or use a learned/rule-based ranker that understands each score type.

Possible fusion strategies:

- weighted reciprocal rank;
- normalized weighted scores;
- learned ranker;
- rule-based priority followed by reranking.

V1 should begin with deterministic weighted/rank-fusion rules and introduce a learned reranker only after a benchmark demonstrates meaningful benefit.

---

## 29. Metadata Filtering Before Expensive Ranking

Cheap structured filters should be applied before expensive model-based reranking where possible.

Example:

```text
query
 ↓
privacy filter
 ↓
entity filter
 ↓
temporal filter
 ↓
memory type
 ↓
vector/FTS retrieval
 ↓
reranker
```

This reduces unnecessary computation and prevents unauthorized data from entering later stages.

NVIDIA's current NeMo Retriever documentation explicitly supports metadata filtering alongside semantic retrieval, reinforcing this architecture. [NVIDIA NeMo Retriever Vector Databases](https://docs.nvidia.com/nemo/retriever/latest/extraction/vdbs/)

---

## 30. Embedding Freshness

An embedding can become stale without the memory itself being stale.

Example:

```text
memory content updated
        ↓
old embedding remains
        ↓
index state = STALE
```

The system should expose:

```text
embedding_created_at
canonical_updated_at
embedding_age
content_hash_match
```

### Freshness policy

For ordinary conversational retrieval, slightly stale indexes may be acceptable.

For high-consequence or current-state retrieval, stale semantic indexes should be supplemented or bypassed with canonical structured retrieval.

---

## 31. Deduplication

Indexing should avoid embedding the same semantic content unnecessarily.

Deduplication signals:

- identical content hash;
- canonical memory relation;
- same artifact/chunk;
- explicit duplicate relation;
- high semantic similarity during consolidation.

Do not automatically merge semantically similar memories during indexing. Consolidation owns semantic merging.

The indexer only prevents obvious technical duplication.

---

## 32. Multilingual Indexing

Novi may encounter multiple languages.

The embedding benchmark must therefore include the languages expected in the robot's actual environment.

FTS tokenization and lexical behavior may differ by language, so multilingual semantic retrieval cannot be assumed to make FTS unnecessary.

Store language metadata per memory/chunk where detectable with sufficient confidence.

```text
language
language_confidence
```

The retrieval planner can then choose language-aware retrieval strategies.

---

## 33. Multimodal Embeddings

Novi eventually needs to index:

- text;
- images;
- audio/transcripts;
- video-derived representations;
- documents containing mixed modalities.

The first implementation should not embed every raw sensor frame.

Instead:

```text
raw sensor stream
       ↓
perception/event extraction
       ↓
meaningful artifact/event
       ↓
index eligibility
       ↓
multimodal embedding if justified
```

NVIDIA NeMo Retriever supports multimodal extraction and documents embedding workflows for multiple content types. [NVIDIA NeMo Retriever](https://docs.nvidia.com/nemo/retriever/latest/)

This supports the broader architecture of indexing meaningful experiences rather than indiscriminately embedding sensor data.

---

## 34. Audio and Voice Memory

For speech-related memories, the canonical representation should normally contain:

```text
source audio artifact
ASR transcript
speaker/identity reference where authorized
conversation/episode ID
timestamps
confidence
```

The transcript can be embedded for semantic retrieval.

The original audio remains an artifact and is subject to a separate retention/privacy policy.

Do not assume the transcript and audio have identical retrieval semantics.

---

## 35. Image and Vision Memory

For visual experiences:

```text
image/video artifact
      ↓
perception metadata
      ↓
objects/entities/events
      ↓
optional caption/summary
      ↓
optional multimodal embedding
```

The structured perception result should remain searchable independently of the embedding.

For example, an exact query such as:

> “When did I last see the red suitcase?”

may be better answered from structured entity/event records than from image-vector similarity alone.

---

## 36. Generated Knowledge and Embeddings

Novi can generate new structured data and files, but generated content must carry provenance.

A generated document should record:

```text
generated_by
model_id
model_version
prompt/task reference
source references
created_at
verification_state
content_hash
```

Its embedding is therefore derived from a generated artifact, not treated as independently verified knowledge.

A generated embedding cannot upgrade the epistemic state of the underlying content.

---

## 37. Security

Indexing introduces several security risks.

### 37.1 Retrieval poisoning

Malicious or incorrect content can be deliberately crafted to become highly retrievable.

Mitigations:

- preserve provenance;
- use trust/verification filters;
- prevent retrieved text from becoming instructions automatically;
- evaluate retrieval candidates before action;
- separate data from commands.

### 37.2 Cross-privacy retrieval

A vector index must not bypass canonical authorization.

Authorization should be applied using canonical metadata or trusted replicated metadata before the candidate is returned to cognition.

### 37.3 Embedding leakage

Embeddings can encode information about source content. Treat embeddings as derived sensitive data where the underlying source is sensitive.

### 37.4 Malicious index metadata

Model-generated metadata must be validated. The model must not control:

- physical index paths;
- arbitrary index names;
- extension loading;
- SQL execution;
- arbitrary filesystem writes.

---

## 38. Failure Handling

### Embedding model unavailable

```text
canonical write succeeds
       ↓
embedding job queued
       ↓
FTS/structured retrieval remains available
```

### Vector index unavailable

Fallback to:

- structured retrieval;
- FTS;
- alternative local index if configured.

### Corrupt vector index

```text
mark CORRUPTED
      ↓
remove from active retrieval
      ↓
rebuild from canonical records
      ↓
validate
      ↓
activate
```

### Disk pressure

Pause low-priority indexing and protect canonical data.

### GPU pressure

Reduce batch size, defer embedding jobs, or switch to a lower-resource embedding profile if validated.

---

## 39. Observability

Indexing metrics should include:

### Pipeline

- jobs queued;
- jobs completed;
- jobs failed;
- retry count;
- queue age;
- throughput.

### Embeddings

- embeddings generated;
- generation latency;
- tokens/items processed;
- batch size;
- model version;
- GPU/CPU utilization;
- memory usage.

### Index

- index size;
- vector count;
- FTS document count;
- stale count;
- rebuild duration;
- index freshness lag;
- corruption events.

### Retrieval quality

- Recall@K;
- Precision@K;
- MRR;
- nDCG;
- hit rate;
- latency;
- false-positive retrieval rate.

---

## 40. Benchmark Program

Technology selection must be benchmark-driven.

### Dataset categories

Create a representative Novi evaluation corpus containing:

- personal preferences;
- people/relationships;
- household knowledge;
- temporal memories;
- work/technical concepts;
- philosophy/general knowledge;
- documents;
- images;
- transcripts;
- contradictory claims;
- stale knowledge;
- multilingual examples;
- distractors.

### Query categories

Include:

- exact lookup;
- paraphrase;
- vague semantic query;
- temporal query;
- person-specific query;
- relationship query;
- current-state query;
- contradiction query;
- multilingual query;
- multimodal query.

### Compare

At minimum benchmark:

```text
FTS only
vector only
FTS + vector
FTS + vector + metadata filters
FTS + vector + reranking
```

Measure both retrieval quality and resource cost.

---

## 41. Embedding Model Benchmark

Every candidate embedding model must be evaluated on:

| Metric | Requirement |
|---|---|
| Retrieval quality | benchmark on Novi corpus |
| Recall@K | measure |
| MRR | measure |
| nDCG | measure |
| Latency | Mac + Jetson |
| Throughput | Mac + Jetson |
| RAM | measure |
| GPU memory | measure |
| Disk footprint | measure |
| Embedding dimension | record |
| Quantized quality | measure if supported |
| Multilingual quality | measure where relevant |
| License | verify |
| Local execution | required by default |
| Maintenance | assess |

No model is selected solely because it is from NVIDIA, Hugging Face, PyTorch, TensorFlow or another ecosystem.

---

## 42. Jetson-Specific Benchmark

The final embedding/index profile must be tested under representative concurrent robot load:

```text
camera inference
+ audio inference
+ autonomy
+ cognition
+ memory writes
+ embedding worker
+ vector retrieval
```

Measure:

- end-to-end latency;
- missed/deferred perception work;
- GPU utilization;
- CPU utilization;
- RAM;
- thermal behavior;
- power mode;
- storage I/O;
- retrieval latency;
- embedding throughput.

A faster embedding model is not better if it causes perception or autonomy latency to degrade.

---

## 43. Rebuild Scheduling

Rebuilds are background work.

Priority:

```text
safety/real-time workloads
        ↑
        │
canonical memory writes
        │
current retrieval maintenance
        │
normal embeddings
        │
bulk re-indexing
        │
benchmark/research indexing
        ↓
```

The robot should be able to postpone bulk re-indexing indefinitely when operating under sustained resource pressure.

---

## 44. Index Lifecycle

```text
NOT_CREATED
    ↓
BUILDING
    ↓
VALIDATING
    ↓
ACTIVE
    ↓
STALE
    ↓
REBUILDING
    ↓
ACTIVE
```

Failure branch:

```text
BUILDING / ACTIVE
       ↓
    CORRUPTED
       ↓
   DISABLED
       ↓
   REBUILDING
```

Old active indexes should remain available during replacement builds until the new index passes validation.

---

## 45. Data/Index Contract

The indexing subsystem should expose a typed contract similar to:

```text
IndexDocument
----------------
subject_id
content
content_hash
metadata
privacy_class
validity
provenance
projection_version

EmbeddingRequest
----------------
subject_id
content
model_id
model_version
input_type
modality

IndexStatus
-----------
index_id
index_type
model_version
index_version
state
freshness_lag
item_count
last_success
```

The implementation language can change without changing the semantic contract.

---

## 46. Relationship to Memory Lifecycle

Indexing follows memory lifecycle; it does not own it.

```text
ADMISSION
   ↓
DURABLE MEMORY
   ↓
INDEX ELIGIBILITY
   ↓
INDEX
   ↓
RETRIEVAL
   ↓
CONSOLIDATION
   ↓
MEMORY UPDATE
   ↓
REINDEX / INVALIDATE
```

When consolidation merges two memories:

1. canonical records are updated;
2. old embeddings become stale;
3. affected index records are invalidated;
4. the merged representation is embedded;
5. old vector entries are removed after safe activation.

---

## 47. Relationship to Provenance and Trust

Every retrieved vector must be traceable back to:

```text
vector
 ↓
embedding record
 ↓
canonical memory/chunk
 ↓
claim
 ↓
evidence
 ↓
source
```

A vector ID without provenance is insufficient for a trusted cognitive system.

---

## 48. Relationship to Cognition

Cognition should request retrieval through the Memory API rather than querying the vector backend directly.

```text
Cognition
   ↓
Memory API
   ↓
Retrieval Planner
   ↓
Hybrid Indexes
   ↓
Ranker
   ↓
Evidence Package
   ↓
Cognition
```

The model should receive structured evidence with metadata, not raw vector scores alone.

---

## 49. Decision Summary

| Area | V1 decision |
|---|---|
| Canonical memory | SQLite / managed artifacts |
| Lexical index | SQLite FTS5 candidate |
| Semantic index | local embedded vector backend |
| Default vector backend | benchmark `sqlite-vec` vs LanceDB |
| NVIDIA integration | NeMo Retriever adapter |
| Embedding model | independently benchmarked |
| Primary reasoning model | independent from embedding model |
| Embedding source of truth | canonical content + metadata |
| Vector source of truth | no; derived only |
| Index updates | asynchronous by default |
| Re-indexing | versioned background migration |
| Query retrieval | hybrid |
| Filtering | structured/authorization filters before expensive ranking |
| Multimodal | selective, not raw-frame embedding |
| Privacy | inherited and enforced on derived indexes |
| Jetson | resource-aware background indexing |
| Mac | full development/benchmark profile |
| Cloud | exception only |
| Vendor lock-in | prohibited |

---

## 50. Open Questions Before Implementation

The following must remain benchmark questions:

1. `sqlite-vec` vs LanceDB vs another local vector engine.
2. Exact embedding model for text.
3. Whether a single multilingual model is sufficient.
4. Whether multimodal embeddings should be shared or separated by modality.
5. Exact chunk size and overlap policy.
6. Brute-force to ANN transition threshold.
7. Vector precision/quantization.
8. Synchronous vs asynchronous embedding for specific memory classes.
9. Jetson embedding batch size.
10. Whether embedding generation should share the primary GPU or use a lower-priority execution profile.
11. Index rebuild scheduling under sustained robot load.
12. Whether FTS5 remains sufficient at projected multi-year scale.
13. Whether a separate graph index becomes necessary.
14. Whether NeMo Retriever provides enough measurable benefit to justify the additional dependency.

These decisions should be resolved through a repeatable benchmark suite rather than architectural preference.

---

## 51. Implementation Acceptance Criteria

`08_MEMORY_INDEXING_AND_EMBEDDINGS.md` is considered implementation-ready when:

- canonical/index boundaries are enforced;
- every embedding has complete model/projection metadata;
- embeddings are idempotently generated;
- stale embeddings are detectable;
- FTS and vector indexes can be rebuilt;
- privacy rules propagate to derived indexes;
- retrieval can fall back when vector search fails;
- model upgrades can create parallel index namespaces;
- old indexes remain available during migration;
- index corruption is detectable and recoverable;
- Jetson resource pressure can pause/defer background indexing;
- benchmark tooling measures retrieval quality and resource cost;
- NVIDIA and non-NVIDIA backends can be compared through the same interface.

---

## 52. References

### NVIDIA

- NVIDIA NeMo Retriever Library: https://docs.nvidia.com/nemo/retriever/latest/
- NVIDIA NeMo Retriever Vector Databases: https://docs.nvidia.com/nemo/retriever/latest/extraction/vdbs/
- NVIDIA NeMo Retriever Embedding NIM API: https://docs.nvidia.com/nim/nemo-retriever/text-embedding/latest/reference.html
- NVIDIA NeMo Retriever Python API: https://docs.nvidia.com/nemo/retriever/26.3.0/extraction/python-api-reference/index.html

### SQLite / local vector ecosystem

- SQLite FTS5: https://sqlite.org/fts5.html
- SQLite WAL: https://sqlite.org/wal.html
- sqlite-vec: https://github.com/asg017/sqlite-vec
- sqlite-vec alternative implementation/research: https://github.com/viant/sqlite-vec

### Novi internal architecture

- `07_MEMORY_SCHEMA_AND_STORAGE.md`
- `06_MEMORY_PROVENANCE_AND_TRUST.md`
- `05_MEMORY_RETRIEVAL_AND_RANKING.md`
- `04_MEMORY_CONSOLIDATION_AND_FORGETTING.md`
- `03_MEMORY_WRITE_AND_ADMISSION_POLICY.md`

## Final Design Rule

**Canonical memory is truth-bearing state. Indexes are disposable search machinery. Embeddings are representations, not beliefs. Retrieval is candidate generation, not authorization or truth determination.**

Novi should therefore be able to delete every vector index, rebuild it from canonical data, and continue operating with structured/lexical retrieval while the semantic index is reconstructed.
