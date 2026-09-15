import re
import pandas as pd

df = pd.read_csv('papers.csv')

def parse_search_query(q):
    """
    Parses complex queries:
    - Boolean OR: 'DBMS or database', 'MapReduce | Bigtable'
    - Year constraints: 'after 2000', 'since 2005', 'year 1990'
    - Multi-keyword: 'query optimization', 'google file system'
    """
    q_clean = q.strip()
    year_filter = None
    
    # Check for year patterns
    year_match = re.search(r'(?:after|since|>)\s*(\d{4})', q_clean, re.I)
    if year_match:
        year_filter = ('>=', int(year_match.group(1)))
        q_clean = re.sub(r'(?:after|since|>)\s*\d{4}', '', q_clean, flags=re.I).strip()
    else:
        year_match_before = re.search(r'(?:before|<)\s*(\d{4})', q_clean, re.I)
        if year_match_before:
            year_filter = ('<=', int(year_match_before.group(1)))
            q_clean = re.sub(r'(?:before|<)\s*\d{4}', '', q_clean, flags=re.I).strip()
        else:
            exact_year = re.search(r'\b(19\d{2}|20\d{2})\b', q_clean)
            if exact_year and len(q_clean.split()) > 1:
                # User typed something like 'query 1996'
                year_filter = ('==', int(exact_year.group(1)))
                q_clean = re.sub(r'\b(19\d{2}|20\d{2})\b', '', q_clean).strip()

    # Check for boolean OR
    if re.search(r'\bOR\b|\|', q_clean, re.I):
        clauses = [c.strip() for c in re.split(r'\bOR\b|\|', q_clean, flags=re.I) if c.strip()]
        is_or = True
    else:
        # Default terms
        raw_terms = q_clean.split()
        stop_words = {'and', 'the', 'a', 'an', 'in', 'of', 'for', 'about', 'paper', 'papers', 'by', 'with'}
        clauses = [w for w in raw_terms if w.lower() not in stop_words]
        is_or = False
        
    return {
        "raw": q,
        "clauses": clauses,
        "is_or": is_or,
        "year_filter": year_filter
    }

def smart_search_papers(query_str, df_papers):
    parsed = parse_search_query(query_str)
    clauses = [c.lower() for c in parsed['clauses']]
    is_or = parsed['is_or']
    y_filter = parsed['year_filter']
    
    scored_results = []
    for _, row in df_papers.iterrows():
        p_year = int(row['year'])
        if y_filter:
            op, target_y = y_filter
            if op == '>=' and not (p_year >= target_y):
                continue
            elif op == '<=' and not (p_year <= target_y):
                continue
            elif op == '==' and not (p_year == target_y):
                continue
                
        t_title = str(row['title']).lower()
        t_kw = str(row['keywords']).lower()
        t_auth = str(row['authors']).lower()
        t_venue = str(row['venue_name']).lower()
        t_abs = str(row['abstract']).lower()
        
        matches = 0
        relevance_score = 0
        
        for clause in clauses:
            matched_clause = False
            if clause in t_title:
                relevance_score += 60
                matched_clause = True
            if clause in t_kw:
                relevance_score += 50
                matched_clause = True
            if clause in t_auth:
                relevance_score += 40
                matched_clause = True
            if clause in t_venue:
                relevance_score += 30
                matched_clause = True
            if clause in t_abs:
                relevance_score += 15
                matched_clause = True
                
            if matched_clause:
                matches += 1
                
        # Matching logic
        should_include = False
        if not clauses:
            should_include = True
        elif is_or and matches > 0:
            should_include = True
        elif not is_or and matches == len(clauses):
            should_include = True
        elif not is_or and len(clauses) > 1 and matches >= 1:
            should_include = True
            
        if should_include:
            # Score bonus for citations
            cite_count = 0
            if pd.notna(row['cited_paper_ids']) and str(row['cited_paper_ids']).strip():
                cite_count = len(str(row['cited_paper_ids']).split(';'))
            total_score = relevance_score + (cite_count * 5)
            scored_results.append((total_score, row))
            
    scored_results.sort(key=lambda x: x[0], reverse=True)
    return [r for _, r in scored_results], parsed

if __name__ == '__main__':
    for test_q in ['DBMS or database', 'query optimization', 'google file system after 2000', 'Ghemawat']:
        res, p = smart_search_papers(test_q, df)
        print(f"=== Query: '{test_q}' -> {len(res)} results ===")
        for r in res[:3]:
            print(f"  [{r['paper_id']}] {r['title']} ({r['year']})")
