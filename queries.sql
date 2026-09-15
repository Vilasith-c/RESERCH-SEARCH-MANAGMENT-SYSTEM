-- ====================================================================
-- Recursive Influence Tracker — Demonstration & Analytical Query Set
-- Course: Database Management Systems (22AIE303)
-- Team: Team 6 (Elluru Ritesh Goud, Bhanu Vilasith Reddy Chika)
-- Tested in: VS Code SQLTools / PostgreSQL 18 (research_db)
-- ====================================================================

-- --------------------------------------------------------------------
-- QUERY 1: Basic Retrieval
-- Goal: Retrieve papers published in or after 2005 with basic attributes.
-- --------------------------------------------------------------------
SELECT 
    p.paper_id,
    p.title,
    p.year,
    p.citation_count,
    p.publisher
FROM Paper p
WHERE p.year >= 2005
ORDER BY p.year DESC, p.paper_id ASC;


-- --------------------------------------------------------------------
-- QUERY 2: Filtering by Keyword
-- Goal: Find all papers associated with 'query optimization' or 'indexing'.
-- --------------------------------------------------------------------
SELECT 
    p.paper_id,
    p.title,
    p.year,
    k.keyword_name
FROM Paper p
JOIN Paper_Keyword pk ON p.paper_id = pk.paper_id
JOIN Keyword k ON pk.keyword_id = k.keyword_id
WHERE k.keyword_name ILIKE '%query optimization%' OR k.keyword_name ILIKE '%indexing%'
ORDER BY p.year ASC;


-- --------------------------------------------------------------------
-- QUERY 3: Multi-Table JOIN (Paper + Authors + Venue)
-- Goal: Retrieve papers with aggregated author list and published venue.
-- --------------------------------------------------------------------
SELECT 
    p.paper_id,
    p.title,
    p.year,
    v.name AS venue_name,
    v.type AS venue_type,
    STRING_AGG(a.name, '; ' ORDER BY a.name) AS authors
FROM Paper p
LEFT JOIN Venue v ON p.venue_id = v.venue_id
LEFT JOIN Paper_Author pa ON p.paper_id = pa.paper_id
LEFT JOIN Author a ON pa.author_id = a.author_id
GROUP BY p.paper_id, p.title, p.year, v.name, v.type
ORDER BY p.year ASC, p.paper_id ASC;


-- --------------------------------------------------------------------
-- QUERY 4: Aggregation (Author Publication Counts & Keyword Popularity)
-- Goal: Aggregate productivity per author and keyword frequency.
-- --------------------------------------------------------------------
-- 4A: Top prolific authors in the repository
SELECT 
    a.name,
    a.affiliation,
    a.publication_count
FROM Author a
WHERE a.publication_count > 1
ORDER BY a.publication_count DESC, a.name ASC;

-- 4B: Most frequent research keywords across papers
SELECT 
    k.keyword_name,
    COUNT(pk.paper_id) AS paper_frequency
FROM Keyword k
JOIN Paper_Keyword pk ON k.keyword_id = pk.keyword_id
GROUP BY k.keyword_id, k.keyword_name
ORDER BY paper_frequency DESC, k.keyword_name ASC
LIMIT 10;


-- --------------------------------------------------------------------
-- QUERY 5: Top-N Most Frequently Used Benchmarks / Datasets
-- Goal: Find which evaluation datasets/benchmarks are adopted most often.
-- --------------------------------------------------------------------
SELECT 
    d.name AS dataset_name,
    d.domain,
    COUNT(pd.paper_id) AS usage_count
FROM Dataset d
JOIN Paper_Dataset pd ON d.dataset_id = pd.dataset_id
GROUP BY d.dataset_id, d.name, d.domain
ORDER BY usage_count DESC, d.name ASC
LIMIT 5;


-- --------------------------------------------------------------------
-- QUERY 6: Nested Subquery
-- Goal: Find authors whose publication count is strictly above the average.
-- --------------------------------------------------------------------
SELECT 
    a.name,
    a.affiliation,
    a.publication_count,
    ROUND((SELECT AVG(publication_count) FROM Author), 2) AS corpus_average
FROM Author a
WHERE a.publication_count > (
    SELECT AVG(publication_count) 
    FROM Author
)
ORDER BY a.publication_count DESC, a.name ASC;


-- --------------------------------------------------------------------
-- QUERY 7: RECURSIVE CTE — Downstream Citation-Influence Traversal
-- Goal: Trace all direct AND indirect downstream papers influenced by a paper.
-- Example: Full downstream reach of Google File System ('P010').
-- Cycle-safe implementation using an array of visited IDs.
-- --------------------------------------------------------------------
WITH RECURSIVE InfluenceChain AS (
    -- Anchor member: immediate papers that cite P010
    SELECT 
        c.citing_paper_id,
        c.cited_paper_id,
        1 AS citation_distance,
        ARRAY[c.cited_paper_id, c.citing_paper_id] AS path
    FROM Citation c
    WHERE c.cited_paper_id = 'P010'

    UNION ALL

    -- Recursive member: papers that cite the citing papers
    SELECT 
        c.citing_paper_id,
        c.cited_paper_id,
        ic.citation_distance + 1,
        ic.path || c.citing_paper_id
    FROM Citation c
    JOIN InfluenceChain ic ON c.cited_paper_id = ic.citing_paper_id
    WHERE NOT (c.citing_paper_id = ANY(ic.path)) -- Cycle guard
)
SELECT 
    ic.citation_distance,
    p_cited.title AS source_paper,
    p_citing.paper_id AS downstream_paper_id,
    p_citing.title AS downstream_title,
    p_citing.year AS downstream_year,
    ARRAY_TO_STRING(ic.path, ' -> ') AS citation_path
FROM InfluenceChain ic
JOIN Paper p_cited ON ic.cited_paper_id = p_cited.paper_id
JOIN Paper p_citing ON ic.citing_paper_id = p_citing.paper_id
ORDER BY ic.citation_distance ASC, p_citing.year ASC;


-- --------------------------------------------------------------------
-- QUERY 8: STANDALONE CYCLE DETECTION QUERY (Viva Highlight)
-- Goal: Detect circular citation dependencies (A -> B -> C -> A).
-- This identifies the deliberately planted cycle:
-- P004 (Volcano) -> P005 (Query Opt) -> P007 (Robust Query Opt) -> P004
-- --------------------------------------------------------------------
WITH RECURSIVE CitationPaths AS (
    -- Base step: all directed citation edges
    SELECT 
        c.citing_paper_id AS start_paper,
        c.cited_paper_id AS current_paper,
        1 AS cycle_depth,
        ARRAY[c.citing_paper_id, c.cited_paper_id] AS path,
        FALSE AS is_cycle
    FROM Citation c

    UNION ALL

    -- Recursive step: extend citation paths
    SELECT 
        cp.start_paper,
        c.cited_paper_id AS current_paper,
        cp.cycle_depth + 1,
        cp.path || c.cited_paper_id,
        (c.cited_paper_id = cp.start_paper) AS is_cycle
    FROM Citation c
    JOIN CitationPaths cp ON c.citing_paper_id = cp.current_paper
    WHERE NOT (c.cited_paper_id = ANY(cp.path)) OR (c.cited_paper_id = cp.start_paper)
      AND cp.is_cycle = FALSE
      AND cp.cycle_depth < 6 -- Safety depth limit
)
SELECT 
    start_paper,
    cycle_depth,
    ARRAY_TO_STRING(path, ' -> ') AS detected_circular_chain
FROM CitationPaths
WHERE is_cycle = TRUE
ORDER BY cycle_depth ASC, start_paper ASC;


-- --------------------------------------------------------------------
-- QUERY 9: LIVE TRIGGER DEMONSTRATION SCRIPT
-- Goal: Demonstrate dynamic maintenance of citation_count and publication_count.
-- (Run this block step by step during Viva)
-- --------------------------------------------------------------------

-- Step 9.1: Check current citation count for P001 (Codd 1970)
SELECT paper_id, title, citation_count 
FROM Paper 
WHERE paper_id = 'P001';

-- Step 9.2: Insert a new citation (e.g. P014 cites P001)
INSERT INTO Citation (citing_paper_id, cited_paper_id) 
VALUES ('P014', 'P001');

-- Step 9.3: Verify citation_count automatically incremented by 1
SELECT paper_id, title, citation_count 
FROM Paper 
WHERE paper_id = 'P001';

-- Step 9.4: Delete the citation
DELETE FROM Citation 
WHERE citing_paper_id = 'P014' AND cited_paper_id = 'P001';

-- Step 9.5: Verify citation_count automatically decremented back
SELECT paper_id, title, citation_count 
FROM Paper 
WHERE paper_id = 'P001';


-- --------------------------------------------------------------------
-- QUERY 10: COMBINABLE MULTI-FIELD SEARCH
-- Goal: Search across Title, Keywords, Authors, Year range, and Venue.
-- --------------------------------------------------------------------
SELECT DISTINCT
    p.paper_id,
    p.title,
    p.year,
    v.name AS venue,
    p.citation_count,
    p.local_path,
    p.scholar_url
FROM Paper p
LEFT JOIN Venue v ON p.venue_id = v.venue_id
LEFT JOIN Paper_Author pa ON p.paper_id = pa.paper_id
LEFT JOIN Author a ON pa.author_id = a.author_id
LEFT JOIN Paper_Keyword pk ON p.paper_id = pk.paper_id
LEFT JOIN Keyword k ON pk.keyword_id = k.keyword_id
WHERE 
    -- Flexible filter clauses (change or comment out as needed)
    (p.year BETWEEN 1990 AND 2015)
    AND (
        p.title ILIKE '%system%' 
        OR k.keyword_name ILIKE '%distributed%' 
        OR a.name ILIKE '%Ghemawat%'
    )
ORDER BY p.citation_count DESC, p.year DESC;


-- --------------------------------------------------------------------
-- QUERY 11: FULL-TEXT SEARCH OVER TITLE AND ABSTRACT (GIN tsvector)
-- Goal: Ranked search using PostgreSQL full-text search engine.
-- --------------------------------------------------------------------
SELECT 
    p.paper_id,
    p.title,
    p.year,
    ts_rank(to_tsvector('english', p.title || ' ' || p.abstract), to_tsquery('english', 'relational & storage')) AS search_rank,
    p.scholar_url
FROM Paper p
WHERE to_tsvector('english', p.title || ' ' || p.abstract) @@ to_tsquery('english', 'relational & storage')
ORDER BY search_rank DESC;


-- --------------------------------------------------------------------
-- QUERY 12: CLICKABLE OUTPUT LAYER / HTML EXPORT VIEW
-- Goal: Generates HTML anchors so query results rendered in SQLTools or 
-- exported to HTML provide direct clickable links to local PDFs and Scholar.
-- --------------------------------------------------------------------
SELECT 
    p.paper_id,
    p.title,
    p.year,
    p.citation_count,
    '<a href="file:///' || REPLACE(p.local_path, '\', '/') || '" target="_blank">📄 Open PDF</a>' AS local_pdf_link,
    '<a href="' || p.scholar_url || '" target="_blank">🎓 Google Scholar</a>' AS scholar_search_link
FROM Paper p
ORDER BY p.citation_count DESC;
