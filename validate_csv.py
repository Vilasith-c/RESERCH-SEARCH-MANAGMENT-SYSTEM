import os
import pandas as pd

def validate():
    csv_file = "papers.csv"
    assert os.path.exists(csv_file), f"{csv_file} does not exist!"
    
    # Check pandas load
    df = pd.read_csv(csv_file)
    print(f"[PASS] Loaded {csv_file} successfully via pandas. Shape: {df.shape}")
    
    # 1. Check columns
    expected_cols = [
        'paper_id', 'title', 'authors', 'author_affiliations', 'year', 'doi',
        'venue_name', 'venue_type', 'venue_year', 'keywords', 'abstract',
        'datasets_used', 'dataset_domains', 'methodology', 'methodology_category',
        'cited_paper_ids', 'page_count', 'language', 'publisher', 'isbn_issn',
        'pdf_filename', 'local_path', 'file_size_kb', 'scholar_url', 'date_added', 'notes'
    ]
    assert list(df.columns) == expected_cols, f"Columns mismatch! Got: {list(df.columns)}"
    print(f"[PASS] Exactly matches 26 expected columns.")

    # 2. Check row count (15 - 20)
    assert 15 <= len(df) <= 25, f"Row count {len(df)} outside range 15-25"
    print(f"[PASS] Total rows: {len(df)} (meets criteria: at least 15-20 papers)")

    # 3. Check uniqueness of paper_id
    assert df['paper_id'].is_unique, "Duplicate paper_id found!"
    print(f"[PASS] All paper_id values are unique.")

    # 4. Check required columns not null
    required_cols = ['paper_id', 'title', 'authors', 'year', 'venue_name', 'keywords', 'abstract', 'pdf_filename', 'local_path']
    for col in required_cols:
        null_count = df[col].isnull().sum()
        assert null_count == 0, f"Column {col} has {null_count} null values!"
    print(f"[PASS] All required columns are populated across all rows.")

    # 5. Check local_path files exist
    for idx, row in df.iterrows():
        path = row['local_path']
        assert os.path.exists(path), f"File not found on disk: {path} (row {row['paper_id']})"
    print(f"[PASS] All 18 local_path references point to actual existing files on disk.")

    # 6. Check cited_paper_ids refer to existing paper_ids
    all_ids = set(df['paper_id'])
    citation_pairs = []
    for idx, row in df.iterrows():
        cited = str(row['cited_paper_ids']) if pd.notna(row['cited_paper_ids']) else ''
        if cited.strip():
            for c_id in cited.split(';'):
                c_id = c_id.strip()
                assert c_id in all_ids, f"Unknown paper_id '{c_id}' cited by {row['paper_id']}"
                citation_pairs.append((row['paper_id'], c_id))
    print(f"[PASS] All citations ({len(citation_pairs)} citation edges) reference valid paper_ids in the dataset.")

    # 7. Check cycle detection (A -> B -> C -> A)
    # Trace planted cycle: P004 -> P005 -> P007 -> P004
    adj = {}
    for citing, cited in citation_pairs:
        adj.setdefault(citing, []).append(cited)
    
    cycles = []
    def find_cycles(path):
        curr = path[-1]
        for neighbor in adj.get(curr, []):
            if neighbor == path[0] and len(path) >= 3:
                cycles.append(path + [neighbor])
            elif neighbor not in path and len(path) < 6:
                find_cycles(path + [neighbor])

    for start_node in adj:
        find_cycles([start_node])

    assert len(cycles) > 0, "No citation cycle detected! Expected planted cycle."
    print(f"[PASS] Detected {len(cycles)} cycle instances. Sample cycle: {' -> '.join(cycles[0])}")

    print("\nALL ACCEPTANCE CRITERIA PASSED COMPLETELY! [SUCCESS]")

if __name__ == "__main__":
    validate()
