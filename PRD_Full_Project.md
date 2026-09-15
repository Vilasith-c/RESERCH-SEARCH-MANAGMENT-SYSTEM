# PRD: Recursive Influence Tracker — Citation-Aware Research Repository

**Course:** Database Management Systems (22AIE303)
**Team:** Team 6 — Elluru Ritesh Goud, Bhanu Vilasith Reddy Chika

## 1. Problem

Modern research is highly interconnected — papers reference other papers, share authors, draw from common datasets, and adopt overlapping methodologies. Yet this information is typically scattered across spreadsheets, folders of PDFs, and informal notes, with no structured system to store it as interconnected entities or answer relationship-based questions efficiently. Researchers cannot easily search systematically across papers, trace relationships (shared authors, common datasets, citation links), avoid duplicate/inconsistent records, or extract insights such as trends, most-cited work, or popular methods.

## 2. Motivation

A research group accumulates its own body of work over years but rarely tracks it as a connected system. Questions like *"which of our papers has influenced the most downstream work?"* or *"do we have circular citation chains from preprint corrections?"* go unanswered because the data lives in disconnected files rather than a queryable structure. A relational database — with normalized entities, constraints, and recursive traversal — is the natural fit for this kind of interconnected, relationship-heavy data, and gives the project a genuine reason to be database-centric rather than app-centric.

## 3. Objective

Design and implement a relational database system — the **Recursive Influence Tracker** — that:

1. Models papers, authors, venues, keywords, datasets, methodologies, and citations as interconnected entities.
2. Enforces data integrity and eliminates redundancy through normalization and constraints.
3. Automatically maintains derived statistics (citation counts, publication counts) via triggers.
4. Supports advanced analytical and recursive queries (citation-chain influence, cycle detection) beyond what simple joins can answer.
5. Guarantees atomicity for multi-table operations using transactions.
6. Provides a multi-field search layer (ID, title, keyword, author, year, venue, dataset, methodology, full-text, citation-aware) over the paper corpus, returning results with a clickable local file path and Google Scholar link.

## 4. Scope

### In scope
- CSV-based metadata ingestion for a corpus of research papers (see companion CSV PRD)
- Normalized relational schema in PostgreSQL
- ETL script (CSV → database) with transaction-wrapped multi-table inserts
- Triggers for auto-updating `citation_count` and `publication_count`
- Recursive CTE for citation-chain traversal with cycle-safety
- Cycle detection as a standalone demoable query
- Multi-field search queries (written and run in VS Code via SQLTools)
- Indexing on frequently searched columns; optional full-text search (`tsvector`/GIN)
- Output layer: query results including `local_path` (open PDF) and `scholar_url` (open Scholar page), viewable as an HTML export of query results

### Out of scope (future work)
- Full web frontend / FastAPI service (may be added later as a stretch goal)
- Recommendation system
- Citation-network visualization (graph rendering)
- Natural-language search over abstracts
- Bridge-paper detection across research clusters

## 5. System Design

A centralized relational database acts as the *active core* of the system rather than passive storage behind an application. Instead of treating each paper as an isolated document, the system captures relationships between papers and their authors, venues, keywords, datasets, methodologies, and citations, so this information can be queried and analyzed in a structured, consistent way.

**Planned stack:**
- **Database:** PostgreSQL
- **Backend (if built):** FastAPI (Python)
- **Frontend (if built):** HTML/CSS/JavaScript
- **Query/dev environment:** VS Code with SQLTools + PostgreSQL driver

## 6. Database Design

### Entities
| Entity | Key fields |
|---|---|
| `Paper` | paper_id (PK), title, year, doi, venue_id (FK), citation_count, local_path, scholar_url |
| `Author` | author_id (PK), name, affiliation, publication_count |
| `Venue` | venue_id (PK), name, type, year |
| `Keyword` | keyword_id (PK), keyword_name |
| `Dataset` | dataset_id (PK), name, domain |
| `Methodology` | method_id (PK), method_name, category |
| `Citation` | citing_paper_id (FK), cited_paper_id (FK) |

### Junction tables (many-to-many)
`Paper_Author`, `Paper_Keyword`, `Paper_Dataset`, `Paper_Method` — each with a composite primary key on its two foreign keys.

### Relationships
- `Paper` ↔ `Author` / `Keyword` / `Dataset` / `Methodology` → many-to-many via junction tables
- `Paper` → `Venue` → many-to-one
- `Paper` ↔ `Paper` (via `Citation`) → many-to-many, self-referencing

*(See the ER diagram delivered separately.)*

## 7. DBMS Concepts Demonstrated

| Concept | Where it's used |
|---|---|
| Normalization | Venue, keyword, and dataset details stored once, referenced via FKs |
| Constraints | `NOT NULL`, `UNIQUE`, `CHECK` (e.g. `citing_paper_id != cited_paper_id`) |
| Transactions | Multi-table paper insert (paper + authors + keywords + datasets) wrapped atomically |
| Triggers | Auto-update `citation_count` on `Paper` and `publication_count` on `Author` |
| Recursive CTE | Citation-chain traversal (direct + indirect citers), with cycle-safety |
| Joins | Combining paper + authors + venue in a single query |
| Aggregation | `COUNT`, `AVG`, `GROUP BY` for publication/keyword statistics |
| Indexing | B-tree on `paper_id`/`year`; optional GIN index for full-text search |
| ETL / data loading | CSV → normalized relational tables |

## 8. SQL Demonstration (Query Set)

1. Basic retrieval — papers published after a given year
2. Filtering — papers by keyword
3. Join — paper title + authors + venue
4. Aggregation — number of papers per author / per keyword
5. Top-N — most frequently used datasets
6. Nested query — authors above average publication count
7. **Recursive query** — full citation-influence chain for a paper
8. **Cycle detection** — identify any A→B→C→A citation loops
9. **Live trigger demo** — insert a new citation, show `citation_count` update instantly
10. **Multi-field search** — ID / title / keyword / author / year-range / venue / dataset / methodology, combinable
11. (Stretch) **Full-text search** — ranked search over title + abstract using `tsvector`/`ts_rank`
12. (Stretch) **Citation-aware search** — papers that cite a given paper, or that cite any paper by a given author

## 9. Output / Demo Layer

Each search query returns, at minimum: `paper_id`, `title`, `authors`, `year`, `venue`, `local_path`, `scholar_url`. Queries are authored and run in VS Code (SQLTools), verified in the results grid, and — for demo purposes — exported to HTML so that `local_path` and `scholar_url` render as clickable links (open PDF locally / open Google Scholar page).

## 10. Build Priority (Sequencing)

**Phase 1 — Core (must complete):**
1. CSV data layer (see companion PRD)
2. Schema + ETL load (transactions)
3. Triggers for auto-updating counts
4. Recursive CTE for citation chains (with cycle-safety)

**Phase 2 — Search & polish:**
5. Multi-field search query set
6. Indexing + basic `EXPLAIN ANALYZE` benchmark
7. HTML export for clickable output

**Phase 3 — Stretch (only if time allows):**
8. Views for reusable analytics (`top_cited_papers`, `author_productivity`, etc.)
9. Full-text search (`tsvector`/GIN)
10. Bridge-paper / community-overlap query

## 11. Outcome

A working relational database that models a research group's scholarly output as an interconnected, queryable system — demonstrating not just storage but active enforcement of integrity (keys/constraints), consistency (triggers, transactions), and insight (joins, aggregation, recursive traversal) beyond what a flat file or spreadsheet could offer. The multi-field search layer with clickable local/Scholar links makes the system tangibly usable, not just a schema exercise.

## 12. Future Scope

- Recommendation system (related papers/authors via shared keywords or citation proximity)
- Citation-network visualization (graph rendering of influence chains)
- Natural-language search over abstracts/titles
- Bridge-paper detection across research clusters
- Full FastAPI + web frontend around the existing query layer

## 13. Viva Defense Notes (for team reference)

- **Trigger vs. app-level logic:** A trigger keeps `citation_count` correct regardless of which entry point inserts data (SQL, API, bulk import) — enforcement lives at the data layer, not duplicated across every application path. Tradeoff: hidden control flow makes debugging harder, acceptable here for the consistency guarantee.
- **Recursive CTE vs. iterative traversal:** A recursive CTE does the citation-graph traversal inside the database in one round trip, letting the query planner optimize it; cycle-safety is handled via `UNION` (dedup) or a depth/visited-set guard, not left to the application to loop and check.
- **Transactions:** A multi-table paper insert either fully succeeds (paper + all its links) or fully rolls back — preventing a half-written, silently corrupted record.
