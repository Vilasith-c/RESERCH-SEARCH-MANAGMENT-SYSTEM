# Recursive Influence Tracker — Citation-Aware Research Repository

**Course:** Database Management Systems (22AIE303)  
**Team 6:** Elluru Ritesh Goud, Bhanu Vilasith Reddy Chilka

---

## 📌 Project Overview
The **Recursive Influence Tracker** is a relational database system and research repository designed to store, manage, and analyze academic papers and their interconnected relationships (citations, authors, venues, datasets, and methodologies).

Unlike simple spreadsheet-based trackers or flat document stores, this system uses PostgreSQL to enforce 3NF normalization, transactional integrity, automated statistics maintenance via triggers, and advanced recursive CTE queries (citation-chain influence analysis and cycle detection). A Flask-based interactive web interface provides real-time multi-field search and citation tracking over the paper corpus.

---

## 🚀 Key Features

1. **Normalized Relational Schema (3NF):**
   - Entities: `Paper`, `Author`, `Venue`, `Keyword`, `Dataset`, `Methodology`, `Citation`, and their associative bridge tables.
   - Enforces referential integrity with foreign key constraints, `ON DELETE CASCADE`, and check constraints.

2. **Automated Statistics (PostgreSQL Triggers):**
   - Automatically maintains `Paper.citation_count` on citation insertions/deletions.
   - Automatically tracks author and venue publication statistics.

3. **Advanced Recursive Analytics:**
   - **Recursive CTE Influence Traversal:** Traverses multi-hop downstream citation chains with cycle prevention.
   - **Cycle Detection:** Identifies circular citation loops (e.g. `P004 -> P005 -> P007 -> P004`) using visited path tracking.

4. **Robust ETL Pipeline:**
   - `etl_load.py` parses `papers.csv`, normalizes metadata into multi-entity tables, and populates the database inside an ACID transaction block.

5. **Smart Search & Interactive Web UI:**
   - Full-featured Flask application with dark-mode glassmorphic UI.
   - Multi-field filters: Title, Author, Keyword, Venue, Year Range, Methodology, Dataset, and Full-Text Search.
   - Direct links to local PDF files (`data/*.pdf`) and Google Scholar entries.
   - Visual citation badge counters and relationship drill-downs.

---

## 📁 Repository Structure

```
├── data/                       # Local PDF documents for research papers
├── static/                     # Web UI frontend assets
│   ├── app.js                  # Frontend interactions & API bindings
│   ├── index.html              # Modern dashboard interface
│   └── style.css               # Responsive design & custom CSS
├── .env.example                # PostgreSQL credentials template
├── .gitignore                  # Git ignore rules for bytecode, secrets, and caches
├── .vscode/                    # VS Code database connection profiles (SQLTools)
│   └── settings.json
├── app.py                      # Flask API & dual-engine (PostgreSQL / In-Memory) backend
├── etl_load.py                 # Transactional ETL ingestion pipeline (CSV → PostgreSQL)
├── export_demo_html.py         # Static HTML report generator
├── generate_csv.py             # Dataset synthesis & validation script
├── papers.csv                  # Curated dataset of research papers & citation metadata
├── PRD_CSV_Data_Layer.md       # Product requirement document (CSV layer)
├── PRD_Full_Project.md         # Full project requirement document
├── queries.sql                 # 15 demonstration & analytics SQL queries (including Recursive CTEs)
├── research_db.session.sql     # SQL scratchpad / execution session
├── schema.sql                  # Complete DDL: tables, indexes, triggers, and views
├── test_smart_search.py        # Automated test suite for smart search engine
└── validate_csv.py             # Automated data integrity & cycle detection test suite
```

---

## ⚙️ Setup and Usage

### 1. Prerequisites
- Python 3.9+
- PostgreSQL 14+ (optional for database-backed queries)
- Required Python packages:
  ```bash
  pip install flask pandas psycopg2-binary
  ```

### 2. Verify Dataset Integrity
Run the CSV validation suite:
```bash
python validate_csv.py
```

### 3. Database Ingestion (PostgreSQL)
1. Create the database:
   ```sql
   CREATE DATABASE research_db;
   ```
2. Initialize schema:
   ```bash
   psql -U postgres -d research_db -f schema.sql
   ```
3. Run the ETL pipeline:
   ```bash
   python etl_load.py
   ```

### 4. Running the Web Application
Start the Flask server:
```bash
python app.py
```
Open [http://localhost:5000](http://localhost:5000) in your web browser.

---

## 👥 Authors
- **Elluru Ritesh Goud**
- **Bhanu Vilasith Reddy Chilka**
