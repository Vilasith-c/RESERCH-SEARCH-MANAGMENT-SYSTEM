SELECT p.paper_id,
    p.title,
    p.year,
    v.name AS venue,
    STRING_AGG(DISTINCT k.keyword_name, '; ') AS matched_keywords,
    p.citation_count,
    STRING_AGG(DISTINCT a.name, ', ') AS authors,
    p.local_path,
    p.scholar_url
FROM Paper p
    JOIN Paper_Keyword pk ON p.paper_id = pk.paper_id
    JOIN Keyword k ON pk.keyword_id = k.keyword_id
    LEFT JOIN Venue v ON p.venue_id = v.venue_id
    LEFT JOIN Paper_Author pa ON p.paper_id = pa.paper_id
    LEFT JOIN Author a ON pa.author_id = a.author_id
WHERE k.keyword_name ILIKE '%DBMS%'
    OR k.keyword_name ILIKE '%database%'
GROUP BY p.paper_id,
    p.title,
    p.year,
    v.name,
    p.citation_count,
    p.local_path,
    p.scholar_url
ORDER BY p.citation_count DESC;