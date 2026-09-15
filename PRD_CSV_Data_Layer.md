# PRD: Research Paper Metadata CSV (Data Layer)

## 1. Overview

**Project:** Scholarly Knowledge Graph Modeling and Citation-Aware Research Repository
**Component:** Step 1 — Raw content layer (CSV)
**Owner:** Team 6 (Elluru Ritesh Goud, Bhanu Vilasith Reddy Chika)

The CSV is the single source of truth extracted from a set of research paper PDFs. It will later be loaded (via an ETL script) into a normalized relational database. Every downstream feature — search, triggers, recursive citation analysis, indexing — depends on this file being complete and consistent, so it should be built with as many meaningful, well-typed columns as can realistically be extracted from each PDF.

## 2. Goal

Produce one CSV file, `papers.csv`, with one row per research paper, containing every extractable metadata field needed to populate the relational schema (Paper, Author, Venue, Keyword, Dataset, Methodology, Citation) plus fields that power the search/output layer (local file path, Google Scholar link).

## 3. Non-Goals

- No database writes happen in this step — this is pure data collection/extraction.
- No deduplication logic across authors/venues/keywords yet — that happens in the ETL step.
- No full-text indexing or search implementation yet.

## 4. Input

A folder of research paper PDFs (one per row in the output CSV), e.g. `/papers/*.pdf`.

## 5. Output

A single file: `papers.csv`, UTF-8 encoded, comma-delimited, with a header row.

## 6. Column Specification

Multi-valued fields (authors, keywords, datasets, methods, citations) use `;` as the internal separator within a single CSV cell.

| # | Column | Type | Required | Description |
|---|---|---|---|---|
| 1 | `paper_id` | string | Yes | Unique ID per paper, e.g. `P001` |
| 2 | `title` | string | Yes | Full paper title |
| 3 | `authors` | string (`;`-separated) | Yes | e.g. `Ritesh Goud; Bhanu Chika` |
| 4 | `author_affiliations` | string (`;`-separated, aligned by position with `authors`) | No | e.g. `Amrita University; Amrita University` |
| 5 | `year` | integer | Yes | Publication year |
| 6 | `doi` | string | No | Digital Object Identifier |
| 7 | `venue_name` | string | Yes | Conference/journal name |
| 8 | `venue_type` | string | No | `conference` / `journal` / `workshop` / `preprint` |
| 9 | `venue_year` | integer | No | Year of that venue's edition (may differ from paper year) |
| 10 | `keywords` | string (`;`-separated) | Yes | e.g. `databases; recursion; indexing` |
| 11 | `abstract` | string | Yes | Full abstract text |
| 12 | `datasets_used` | string (`;`-separated) | No | e.g. `TPC-H; DBLP` |
| 13 | `dataset_domains` | string (`;`-separated, aligned with `datasets_used`) | No | e.g. `benchmarking; bibliographic` |
| 14 | `methodology` | string (`;`-separated) | No | e.g. `Benchmarking; Empirical study` |
| 15 | `methodology_category` | string (`;`-separated, aligned with `methodology`) | No | e.g. `Quantitative; Quantitative` |
| 16 | `cited_paper_ids` | string (`;`-separated `paper_id` values) | No | Papers *this* paper cites, restricted to IDs present in this CSV |
| 17 | `page_count` | integer | No | Total pages |
| 18 | `language` | string | No | e.g. `English` |
| 19 | `publisher` | string | No | e.g. `IEEE`, `ACM`, `Springer` |
| 20 | `isbn_issn` | string | No | If applicable |
| 21 | `pdf_filename` | string | Yes | Original filename, e.g. `paper_014.pdf` |
| 22 | `local_path` | string | Yes | Absolute/relative path to the PDF on disk |
| 23 | `file_size_kb` | integer | No | Size of the PDF file |
| 24 | `scholar_url` | string | No | Direct Google Scholar link if found; leave blank to auto-generate later from title |
| 25 | `date_added` | date (`YYYY-MM-DD`) | No | Date this row was added to the CSV |
| 26 | `notes` | string | No | Free-text notes (e.g. "duplicate of P004", "OCR quality poor") |

## 7. Sample Row

```
paper_id,title,authors,author_affiliations,year,doi,venue_name,venue_type,venue_year,keywords,abstract,datasets_used,dataset_domains,methodology,methodology_category,cited_paper_ids,page_count,language,publisher,isbn_issn,pdf_filename,local_path,file_size_kb,scholar_url,date_added,notes
P001,"Recursive Query Optimization in Relational Databases","A. Sharma; B. Rao","IIT Delhi; IIT Delhi",2023,10.1109/ICDE.2023.001,"ICDE",conference,2023,"databases; recursion; indexing","This paper explores...","TPC-H; DBLP","benchmarking; bibliographic","Benchmarking","Quantitative","P004;P012",10,English,IEEE,,paper_001.pdf,/papers/paper_001.pdf,842,,2025-09-01,
```

## 8. Data Quality Rules

- `paper_id` must be unique across all rows.
- Every ID listed in `cited_paper_ids` should ideally exist as a `paper_id` elsewhere in the same CSV (external citations outside the corpus can be left as free text or dropped — decide and note the convention).
- Multi-valued columns must use `;` consistently, with no trailing/leading whitespace around each value.
- `local_path` must point to a file that actually exists at the time of ETL load.
- `year` must be a 4-digit integer.

## 9. Deliverable & Acceptance Criteria

- [ ] `papers.csv` produced, one row per PDF in the source folder
- [ ] All "Required" columns populated for every row
- [ ] No duplicate `paper_id` values
- [ ] File opens cleanly in Excel/Google Sheets and in `pandas.read_csv()` without parsing errors
- [ ] At least 15–20 papers included (enough to make joins, aggregation, and recursive citation queries meaningful during demo)
- [ ] Citation links (`cited_paper_ids`) exist for at least a few papers, including at minimum one deliberately-planted citation cycle (A→B→C→A) to demo cycle detection

## 10. Next Step (out of scope for this PRD)

Once `papers.csv` passes the acceptance criteria above, the next step is the ETL script that loads this file into the normalized PostgreSQL schema (Paper, Author, Venue, Keyword, Dataset, Methodology, Citation, and junction tables).
