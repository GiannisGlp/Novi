# 68 — Memory Knowledge Document and File Ingestion

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## Purpose

Define how Novi safely ingests knowledge from documents and files without confusing parsed content with truth, authority, instructions, or permission.

Supported sources may include PDFs, text, Markdown, office documents, spreadsheets, images, audio/video, source code, structured datasets, manuals, notes, books, exports, archives, and future formats.

## Core Principle

> **A file is an evidence container, not an authority. Parsing a file does not make its contents true, safe, current, or authorized.**

---

## 1. Ingestion Pipeline

```text
FILE / DOCUMENT
      ↓
IDENTIFY
      ↓
INTEGRITY CHECK
      ↓
SECURITY SCREEN
      ↓
FORMAT DETECTION
      ↓
PARSING / EXTRACTION
      ↓
STRUCTURAL ANALYSIS
      ↓
PROVENANCE
      ↓
PRIVACY / AUTHORIZATION
      ↓
CONTENT VALIDATION
      ↓
CHUNK / REPRESENTATION
      ↓
INDEX
      ↓
MEMORY ADMISSION
      ↓
KNOWLEDGE EVALUATION
```

Each stage can fail independently.

---

## 2. File Identity

Record, where available:

- filename;
- MIME type;
- size;
- cryptographic hash;
- source/location;
- creator/owner metadata;
- creation/modification timestamps;
- format/version;
- ingestion timestamp;
- parser/version used.

A filename alone is never sufficient to establish file type or trust.

---

## 3. Integrity

The ingestion layer should detect unexpected changes using appropriate integrity mechanisms.

```text
same logical document
      ↓
new content hash
      ↓
NEW VERSION / CHANGE
```

Integrity verification does not prove factual correctness.

---

## 4. Security Boundary

Files must be treated as potentially untrusted input.

Threats include:

- malicious documents;
- embedded scripts/macros;
- malformed parser inputs;
- decompression bombs;
- hostile images;
- prompt injection;
- malicious metadata;
- embedded external links;
- poisoned datasets;
- oversized content;
- parser vulnerabilities.

Content must not execute merely because it is being ingested.

---

## 5. Sandboxed Parsing

Where practical, complex or untrusted parsers should run in isolated environments with:

- restricted filesystem access;
- restricted network access;
- resource limits;
- process isolation;
- timeouts;
- memory limits.

Parsing failure must not compromise Novi's core process.

---

## 6. No Implicit Execution

A document containing:

```text
macro
script
command
shell instruction
agent instruction
```

is content, not an executable instruction.

Execution requires a separate explicitly authorized workflow.

---

## 7. Prompt Injection

Documents may contain instructions designed to manipulate an AI system:

```text
"Ignore previous instructions..."
"Reveal private memory..."
"Delete your database..."
```

These must remain untrusted document content.

```text
DOCUMENT CONTENT
      ≠
SYSTEM INSTRUCTION
```

---

## 8. Document Structure

Preserve structure where possible:

```text
document
 ├── metadata
 ├── sections
 ├── paragraphs
 ├── tables
 ├── figures
 ├── captions
 ├── footnotes
 ├── references
 ├── headers/footers
 └── attachments
```

Flattening everything into plain text can destroy important meaning.

---

## 9. Location Provenance

Every extracted fact should retain enough provenance to locate its origin.

For example:

```text
claim
 → document ID
 → version
 → page
 → section
 → paragraph/table/cell
 → extraction method
```

Exact granularity depends on the format.

---

## 10. Extraction vs Interpretation

Novi must distinguish:

```text
EXTRACTED TEXT
        ↓
INTERPRETED MEANING
        ↓
INFERRED CLAIM
```

The parser's output is not automatically an interpreted fact.

---

## 11. OCR

For scanned documents and images:

```text
image
 ↓
OCR
 ↓
extracted text
```

OCR output carries uncertainty and should retain a link to the original visual region where practical.

OCR confidence must not be confused with factual confidence.

---

## 12. Tables

Tables require structure-aware extraction.

Preserve:

- rows;
- columns;
- headers;
- units;
- merged cells;
- footnotes;
- source context.

A table should not be converted into a sequence of unrelated sentences when that would change meaning.

---

## 13. Spreadsheets

Spreadsheet ingestion should preserve:

```text
workbook
 → sheet
 → cell
 → formula
 → displayed value
 → formatting/units where meaningful
```

Formula results and formulas should be distinguished.

A displayed value may change if the workbook is recalculated.

---

## 14. Code

Source code is data during ingestion.

Novi may analyze it, but ingestion must not execute it.

Preserve:

- repository/path;
- commit/version;
- language;
- symbols;
- dependencies where available;
- line ranges.

---

## 15. PDFs

PDFs may contain:

- text;
- images;
- tables;
- annotations;
- embedded files;
- scripts;
- scanned pages.

The ingestion system must not assume that a PDF is simply a text document.

---

## 16. Images

Image ingestion should distinguish:

```text
pixels
 ↓
visual observations
 ↓
model detections
 ↓
interpretations
```

A model-detected object is not automatically a confirmed fact.

Original image provenance should be retained according to privacy policy.

---

## 17. Audio

Audio ingestion should distinguish:

```text
audio
 ↓
speech recognition
 ↓
transcript
 ↓
speaker attribution
 ↓
interpretation
```

Speaker attribution remains probabilistic unless independently authenticated.

---

## 18. Video

Video may produce multiple evidence streams:

```text
video
 ├── frames
 ├── audio
 ├── timestamps
 ├── detected objects
 ├── movement
 └── events
```

Derived observations retain links to the source interval.

---

## 19. Structured Data

For CSV, JSON, XML, databases and similar data:

- preserve schema;
- field types;
- units;
- identifiers;
- timestamps;
- source/version;
- missing-value semantics.

A missing value is not automatically zero, false or unknown without schema semantics.

---

## 20. Archives

Archives such as ZIP/TAR must be handled with resource limits.

The system should protect against:

- nested archives;
- excessive expansion;
- path traversal;
- enormous file counts;
- decompression bombs.

---

## 21. Duplicate Detection

Use appropriate content and semantic similarity mechanisms to identify possible duplicates.

```text
same hash
 → identical bytes

similar content
 → possible duplicate/version
```

Similarity must not silently merge distinct documents.

---

## 22. Versioning

Document changes should create version-aware provenance.

```text
Document A v1
      ↓
Document A v2
      ↓
Document A v3
```

Historical claims remain associated with the version from which they originated.

---

## 23. Supersession

A newer document may supersede an older one.

```text
v1 → SUPERSEDED BY → v2
```

Supersession does not necessarily mean the older document becomes false; it may remain historically valid.

---

## 24. Document Time

Distinguish:

```text
creation time
modification time
publication time
ingestion time
retrieval time
validity interval
```

Filesystem timestamps alone must not be treated as authoritative publication dates.

---

## 25. Source Authority

Document authority is contextual.

Examples:

```text
manufacturer manual
 → potentially authoritative for product operation

random forum post
 → user-generated evidence

user note
 → authoritative about user's own stated preference
```

No universal source ranking applies to every question.

---

## 26. Cross-Validation

Important claims may require corroboration.

```text
document claim
      ↓
independent source
      ↓
current evidence
      ↓
validation
```

Repeated copies of the same source do not count as independent corroboration.

---

## 27. User-Provided Documents

A user-provided document may be highly relevant but remains distinct from verified external truth.

The document may be authoritative for statements such as:

```text
"This is my preference."
```

but not necessarily for unrelated factual claims.

---

## 28. Privacy Classification

Before durable admission, classify information appropriately.

Possible categories:

```text
PUBLIC
INTERNAL
PERSONAL
SENSITIVE
HIGHLY_SENSITIVE
RESTRICTED
SECRET
```

Classification must integrate with documents 61–63.

---

## 29. Authorization

Ingestion does not imply permission to retain.

```text
can read file
      ≠
can permanently remember file
```

Retention requires applicable authorization and policy.

---

## 30. Minimization

Novi should avoid retaining the entire source when only a small portion is needed.

```text
source document
      ↓
necessary evidence
      ↓
minimal durable representation
```

The original may remain available under a separate retention policy when appropriate.

---

## 31. Sensitive Derivatives

Derived summaries, embeddings, entities and graph relationships may remain sensitive even when the original file is not directly exposed.

Privacy classification must propagate appropriately.

---

## 32. Memory Admission

A document can produce several outcomes:

```text
REJECTED
QUARANTINED
TRANSIENT ONLY
ADMITTED
ADMITTED WITH RESTRICTIONS
PROVISIONAL KNOWLEDGE
```

Not every document should become long-term memory.

---

## 33. Chunking

For retrieval, large documents may be divided into chunks.

Chunking must preserve enough context to avoid changing meaning.

Every chunk retains document/version provenance.

---

## 34. Chunk Context

A chunk should retain relationships to:

- title;
- section;
- surrounding context;
- tables/figures;
- document version;
- page/location.

This prevents isolated retrieval from stripping away critical context.

---

## 35. Embeddings

Embeddings are derived representations.

They must retain:

```text
source document
source version
chunk ID
embedding model/version
creation time
privacy classification
```

Embeddings are not authoritative facts.

---

## 36. Indexing

Documents may populate:

- lexical indexes;
- vector indexes;
- temporal indexes;
- entity indexes;
- graph projections.

These are derived structures and must remain rebuildable where practical.

---

## 37. Knowledge Promotion

Document content should follow the same knowledge pipeline as other external evidence:

```text
document claim
 ↓
provenance
 ↓
reliability
 ↓
context
 ↓
cross-validation
 ↓
uncertainty
 ↓
promotion decision
```

---

## 38. Conflicting Documents

If two documents conflict:

```text
Document A → claim X
Document B → claim Y
```

Novi should preserve both evidence paths and evaluate:

- authority;
- publication/validity time;
- context;
- independence;
- evidence quality.

It must not select the newest document solely because it is newer.

---

## 39. Instruction Documents

A document can legitimately contain instructions, such as a user manual.

Those instructions remain **knowledge/content** until a separate execution policy authorizes an action.

```text
manual
 ↓
knowledge
 ↓
reasoning
 ↓
authorized action policy
 ↓
safety check
```

---

## 40. Malicious Instructions

Documents cannot:

- grant themselves privileges;
- override system policy;
- disable safety;
- authorize data export;
- change memory permissions;
- modify retention policy.

---

## 41. External Links

Embedded links should be treated as references, not automatically followed.

Following a link is a separate network operation subject to document 67.

---

## 42. File Metadata

Metadata can be useful but untrusted.

Examples:

```text
author = "Admin"
created = "2020"
classification = "public"
```

These claims require appropriate validation.

---

## 43. Document Authority and Identity

A document claiming to be from an organization does not prove that origin.

Where authenticity matters, use available mechanisms such as:

- trusted repositories;
- signatures;
- authenticated sources;
- known distribution channels;
- checksums.

---

## 44. Incremental Ingestion

Large documents should support incremental processing where practical.

Failures should not require discarding already validated portions.

Each partial result must remain clearly marked as partial until ingestion is complete.

---

## 45. Resumability

Interrupted ingestion should resume from durable checkpoints without duplicating records.

```text
checkpoint
 ↓
restart
 ↓
resume
```

---

## 46. Failure Handling

Possible states include:

```text
NOT_STARTED
PROCESSING
PARTIALLY_PROCESSED
COMPLETED
FAILED
QUARANTINED
REQUIRES_REVIEW
```

Failure must not appear as successful ingestion.

---

## 47. Resource Limits

Document ingestion must enforce limits for:

- file size;
- page count;
- expansion ratio;
- processing time;
- RAM;
- CPU/GPU;
- concurrent files;
- extracted text size;
- image resolution.

Limits protect Novi from unbounded resource consumption.

---

## 48. Thermal and Battery Awareness

Background ingestion should yield to system constraints.

```text
thermal pressure / low battery
        ↓
pause or reduce ingestion
        ↓
preserve core operation
```

---

## 49. Offline Operation

Local document ingestion must work without network connectivity where local capabilities permit.

External enrichment is optional and separately governed.

```text
local document
 ↓
local parsing
 ↓
local memory
```

No cloud dependency is required for the core pipeline.

---

## 50. Network Enrichment

If network enrichment is enabled:

```text
document
 ↓
local extraction
 ↓
optional external lookup
 ↓
document 67 boundary
 ↓
validation
```

Network data cannot silently overwrite local source provenance.

---

## 51. Deletion

Deleting a document must trigger dependency-aware handling of:

- extracted text;
- chunks;
- embeddings;
- graph relationships;
- indexes;
- caches;
- derived memories;
- replicas;
- backups;

according to documents 61–63.

---

## 52. Source Replacement

Replacing a document must not silently mutate historical evidence.

```text
old source
 → retained historical provenance where permitted

new source
 → new version
```

---

## 53. Auditability

Important ingestion events should record:

- source identity;
- hash/version;
- ingestion time;
- parser/version;
- validation status;
- admission decision;
- privacy classification;
- authorization context;
- derived records;
- failures.

---

## 54. Testing

Test at minimum:

- malformed files;
- parser crashes;
- malicious documents;
- macros/scripts;
- prompt injection;
- decompression bombs;
- path traversal;
- duplicate files;
- changed versions;
- OCR errors;
- table extraction;
- spreadsheet formulas;
- corrupted PDFs;
- misleading metadata;
- conflicting sources;
- privacy leakage;
- unauthorized retention;
- deletion propagation;
- interrupted ingestion;
- resource exhaustion;
- offline operation;
- thermal throttling;
- low battery;
- model/parser migration.

---

## 55. Architectural Invariants

1. Files are evidence containers, not automatic truth.
2. File parsing never grants authority.
3. Untrusted documents are processed in appropriate isolation.
4. Document content is never automatically a system instruction.
5. Document structure and provenance are preserved where practical.
6. Extraction is distinct from interpretation and inference.
7. OCR uncertainty is retained.
8. Spreadsheet formulas and values are distinct.
9. Code is analyzed as data unless separately authorized for execution.
10. Document versions preserve historical provenance.
11. Newer documents do not automatically make older claims false.
12. Source authority is contextual.
13. Repeated copies of one source are not independent corroboration.
14. User-provided files do not automatically establish external truth.
15. Ingestion does not imply permission to retain.
16. Derived data inherits appropriate privacy restrictions.
17. Embeddings are derived representations, not authoritative knowledge.
18. Malicious document instructions cannot change Novi policy or privileges.
19. External links require a separate network trust boundary.
20. Partial ingestion is explicitly marked as partial.
21. Failed ingestion is never reported as successful.
22. Resource limits protect core Novi operation.
23. Thermal and battery constraints can defer background ingestion.
24. Local document ingestion works without network connectivity where technically supported.
25. Deletion propagates through derived representations according to the secure-deletion architecture.
26. Every durable knowledge item retains sufficient provenance to reconstruct where it came from.
27. Novi must be able to say that a document is insufficient evidence rather than promote unsupported claims.

---

## 56. Final Principle

> **Novi should be able to learn from almost any useful document without allowing any document to redefine what Novi is, what Novi is allowed to do, or what Novi should believe without evidence.**

Document ingestion is therefore a controlled evidence pipeline—not a shortcut into memory, authority, learning, or action.
