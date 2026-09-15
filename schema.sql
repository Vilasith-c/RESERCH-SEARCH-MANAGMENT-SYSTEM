-- ====================================================================
-- Recursive Influence Tracker — Database Schema
-- Course: Database Management Systems (22AIE303)
-- Database: PostgreSQL 18 (research_db)
-- ====================================================================

-- Clean slate: drop tables if they already exist (cascade to handle FK dependencies)
DROP TABLE IF EXISTS Paper_Method CASCADE;
DROP TABLE IF EXISTS Paper_Dataset CASCADE;
DROP TABLE IF EXISTS Paper_Keyword CASCADE;
DROP TABLE IF EXISTS Paper_Author CASCADE;
DROP TABLE IF EXISTS Citation CASCADE;
DROP TABLE IF EXISTS Paper CASCADE;
DROP TABLE IF EXISTS Methodology CASCADE;
DROP TABLE IF EXISTS Dataset CASCADE;
DROP TABLE IF EXISTS Keyword CASCADE;
DROP TABLE IF EXISTS Author CASCADE;
DROP TABLE IF EXISTS Venue CASCADE;

-- --------------------------------------------------------------------
-- 1. ENTITY TABLES
-- --------------------------------------------------------------------

-- Venue entity: conferences, journals, workshops, books
CREATE TABLE Venue (
    venue_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) CHECK (type IN ('conference', 'journal', 'workshop', 'preprint', 'book')),
    year INT CHECK (year >= 1900 AND year <= 2100),
    CONSTRAINT uq_venue UNIQUE (name, year)
);

-- Author entity: researchers with affiliations and tracked publication count
CREATE TABLE Author (
    author_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    affiliation TEXT,
    publication_count INT NOT NULL DEFAULT 0,
    CONSTRAINT uq_author UNIQUE (name, affiliation)
);

-- Keyword entity: normalized index terms and research subjects
CREATE TABLE Keyword (
    keyword_id SERIAL PRIMARY KEY,
    keyword_name VARCHAR(100) NOT NULL UNIQUE
);

-- Dataset entity: benchmarks, corpora, and real-world collections
CREATE TABLE Dataset (
    dataset_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(255),
    CONSTRAINT uq_dataset UNIQUE (name)
);

-- Methodology entity: algorithmic techniques, paradigms, and evaluation approaches
CREATE TABLE Methodology (
    method_id SERIAL PRIMARY KEY,
    method_name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    CONSTRAINT uq_methodology UNIQUE (method_name)
);

-- Paper entity: core scholarly work
CREATE TABLE Paper (
    paper_id VARCHAR(10) PRIMARY KEY,
    title TEXT NOT NULL,
    year INT NOT NULL CHECK (year >= 1900 AND year <= 2100),
    doi VARCHAR(255),
    venue_id INT REFERENCES Venue(venue_id) ON DELETE SET NULL,
    citation_count INT NOT NULL DEFAULT 0,
    abstract TEXT NOT NULL,
    page_count INT,
    language VARCHAR(50) DEFAULT 'English',
    publisher VARCHAR(100),
    isbn_issn VARCHAR(100),
    pdf_filename VARCHAR(255) NOT NULL,
    local_path TEXT NOT NULL,
    file_size_kb INT,
    scholar_url TEXT,
    date_added DATE DEFAULT CURRENT_DATE,
    notes TEXT
);

-- --------------------------------------------------------------------
-- 2. CITATION GRAPH (Self-referential many-to-many relationship)
-- --------------------------------------------------------------------
CREATE TABLE Citation (
    citing_paper_id VARCHAR(10) NOT NULL REFERENCES Paper(paper_id) ON DELETE CASCADE,
    cited_paper_id VARCHAR(10) NOT NULL REFERENCES Paper(paper_id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (citing_paper_id, cited_paper_id),
    CONSTRAINT chk_no_self_citation CHECK (citing_paper_id != cited_paper_id)
);

-- --------------------------------------------------------------------
-- 3. JUNCTION TABLES (Many-to-Many Relationships)
-- --------------------------------------------------------------------

-- Paper <-> Author
CREATE TABLE Paper_Author (
    paper_id VARCHAR(10) NOT NULL REFERENCES Paper(paper_id) ON DELETE CASCADE,
    author_id INT NOT NULL REFERENCES Author(author_id) ON DELETE CASCADE,
    PRIMARY KEY (paper_id, author_id)
);

-- Paper <-> Keyword
CREATE TABLE Paper_Keyword (
    paper_id VARCHAR(10) NOT NULL REFERENCES Paper(paper_id) ON DELETE CASCADE,
    keyword_id INT NOT NULL REFERENCES Keyword(keyword_id) ON DELETE CASCADE,
    PRIMARY KEY (paper_id, keyword_id)
);

-- Paper <-> Dataset
CREATE TABLE Paper_Dataset (
    paper_id VARCHAR(10) NOT NULL REFERENCES Paper(paper_id) ON DELETE CASCADE,
    dataset_id INT NOT NULL REFERENCES Dataset(dataset_id) ON DELETE CASCADE,
    PRIMARY KEY (paper_id, dataset_id)
);

-- Paper <-> Methodology
CREATE TABLE Paper_Method (
    paper_id VARCHAR(10) NOT NULL REFERENCES Paper(paper_id) ON DELETE CASCADE,
    method_id INT NOT NULL REFERENCES Methodology(method_id) ON DELETE CASCADE,
    PRIMARY KEY (paper_id, method_id)
);

-- --------------------------------------------------------------------
-- 4. PERFORMANCE INDEXES
-- --------------------------------------------------------------------
CREATE INDEX idx_paper_year ON Paper(year);
CREATE INDEX idx_paper_title ON Paper(title);
CREATE INDEX idx_citation_cited ON Citation(cited_paper_id);
CREATE INDEX idx_citation_citing ON Citation(citing_paper_id);
CREATE INDEX idx_paper_author_author ON Paper_Author(author_id);
CREATE INDEX idx_paper_keyword_keyword ON Paper_Keyword(keyword_id);

-- Full-text search index on Title and Abstract (tsvector / GIN)
CREATE INDEX idx_paper_fts ON Paper USING GIN (to_tsvector('english', title || ' ' || abstract));

-- --------------------------------------------------------------------
-- 5. TRIGGERS FOR DATA INTEGRITY AND DERIVED STATISTICS
-- --------------------------------------------------------------------

-- Trigger 1: Auto-update Paper.citation_count upon Citation INSERT / DELETE
CREATE OR REPLACE FUNCTION update_citation_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE Paper
        SET citation_count = citation_count + 1
        WHERE paper_id = NEW.cited_paper_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE Paper
        SET citation_count = GREATEST(0, citation_count - 1)
        WHERE paper_id = OLD.cited_paper_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_citation_count
AFTER INSERT OR DELETE ON Citation
FOR EACH ROW
EXECUTE FUNCTION update_citation_count();

-- Trigger 2: Auto-update Author.publication_count upon Paper_Author INSERT / DELETE
CREATE OR REPLACE FUNCTION update_publication_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE Author
        SET publication_count = publication_count + 1
        WHERE author_id = NEW.author_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE Author
        SET publication_count = GREATEST(0, publication_count - 1)
        WHERE author_id = OLD.author_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_author_publication_count
AFTER INSERT OR DELETE ON Paper_Author
FOR EACH ROW
EXECUTE FUNCTION update_publication_count();
