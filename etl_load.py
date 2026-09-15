import os
import sys
import getpass
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

def get_db_connection():
    host = os.environ.get("PGHOST", "localhost")
    port = os.environ.get("PGPORT", "5432")
    dbname = os.environ.get("PGDATABASE", "research_db")
    user = os.environ.get("PGUSER", "postgres")
    password = os.environ.get("PGPASSWORD")
    
    if not password:
        # Prompt for password if not set in environment
        password = getpass.getpass(f"Enter password for PostgreSQL user '{user}' (database: {dbname}): ")

    conn = psycopg2.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password
    )
    return conn

def run_etl(csv_path="papers.csv", schema_path="schema.sql"):
    print(f"[*] Starting ETL pipeline...")
    assert os.path.exists(csv_path), f"CSV file {csv_path} not found!"
    assert os.path.exists(schema_path), f"Schema file {schema_path} not found!"

    df = pd.read_csv(csv_path)
    print(f"[*] Loaded {len(df)} records from {csv_path}")

    conn = get_db_connection()
    conn.autocommit = False
    cursor = conn.cursor()

    try:
        # Step 1: Execute Schema DDL
        print(f"[*] Applying schema from {schema_path}...")
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()
        cursor.execute(schema_sql)
        print("[+] Schema and triggers created successfully.")

        # Step 2: Ingest Venues
        print("[*] Processing Venues...")
        venue_cache = {}
        for _, row in df.iterrows():
            v_name = str(row['venue_name']).strip()
            v_type = str(row['venue_type']).strip() if pd.notna(row['venue_type']) else None
            v_year = int(row['venue_year']) if pd.notna(row['venue_year']) else int(row['year'])
            key = (v_name, v_year)
            if key not in venue_cache:
                cursor.execute(
                    "INSERT INTO Venue (name, type, year) VALUES (%s, %s, %s) "
                    "ON CONFLICT (name, year) DO UPDATE SET type = EXCLUDED.type RETURNING venue_id;",
                    (v_name, v_type, v_year)
                )
                venue_id = cursor.fetchone()[0]
                venue_cache[key] = venue_id

        # Step 3: Ingest Authors
        print("[*] Processing Authors...")
        author_cache = {}
        for _, row in df.iterrows():
            authors = [a.strip() for a in str(row['authors']).split(';') if a.strip()]
            affils = [af.strip() for af in str(row['author_affiliations']).split(';')] if pd.notna(row['author_affiliations']) else []
            for idx, a_name in enumerate(authors):
                a_affil = affils[idx] if idx < len(affils) and affils[idx] else None
                key = (a_name, a_affil)
                if key not in author_cache:
                    cursor.execute(
                        "INSERT INTO Author (name, affiliation) VALUES (%s, %s) "
                        "ON CONFLICT (name, affiliation) DO NOTHING RETURNING author_id;",
                        (a_name, a_affil)
                    )
                    res = cursor.fetchone()
                    if res:
                        author_cache[key] = res[0]
                    else:
                        cursor.execute("SELECT author_id FROM Author WHERE name = %s AND (affiliation = %s OR (affiliation IS NULL AND %s IS NULL));", (a_name, a_affil, a_affil))
                        author_cache[key] = cursor.fetchone()[0]

        # Step 4: Ingest Keywords
        print("[*] Processing Keywords...")
        keyword_cache = {}
        for _, row in df.iterrows():
            kw_list = [k.strip() for k in str(row['keywords']).split(';') if k.strip()]
            for kw in kw_list:
                if kw not in keyword_cache:
                    cursor.execute(
                        "INSERT INTO Keyword (keyword_name) VALUES (%s) "
                        "ON CONFLICT (keyword_name) DO NOTHING RETURNING keyword_id;",
                        (kw,)
                    )
                    res = cursor.fetchone()
                    if res:
                        keyword_cache[kw] = res[0]
                    else:
                        cursor.execute("SELECT keyword_id FROM Keyword WHERE keyword_name = %s;", (kw,))
                        keyword_cache[kw] = cursor.fetchone()[0]

        # Step 5: Ingest Datasets
        print("[*] Processing Datasets...")
        dataset_cache = {}
        for _, row in df.iterrows():
            if pd.notna(row['datasets_used']) and str(row['datasets_used']).strip():
                d_names = [d.strip() for d in str(row['datasets_used']).split(';') if d.strip()]
                d_domains = [dm.strip() for dm in str(row['dataset_domains']).split(';')] if pd.notna(row['dataset_domains']) else []
                for idx, d_name in enumerate(d_names):
                    d_dom = d_domains[idx] if idx < len(d_domains) and d_domains[idx] else None
                    if d_name not in dataset_cache:
                        cursor.execute(
                            "INSERT INTO Dataset (name, domain) VALUES (%s, %s) "
                            "ON CONFLICT (name) DO UPDATE SET domain = EXCLUDED.domain RETURNING dataset_id;",
                            (d_name, d_dom)
                        )
                        dataset_cache[d_name] = cursor.fetchone()[0]

        # Step 6: Ingest Methodologies
        print("[*] Processing Methodologies...")
        method_cache = {}
        for _, row in df.iterrows():
            if pd.notna(row['methodology']) and str(row['methodology']).strip():
                m_names = [m.strip() for m in str(row['methodology']).split(';') if m.strip()]
                m_cats = [mc.strip() for mc in str(row['methodology_category']).split(';')] if pd.notna(row['methodology_category']) else []
                for idx, m_name in enumerate(m_names):
                    m_cat = m_cats[idx] if idx < len(m_cats) and m_cats[idx] else None
                    if m_name not in method_cache:
                        cursor.execute(
                            "INSERT INTO Methodology (method_name, category) VALUES (%s, %s) "
                            "ON CONFLICT (method_name) DO UPDATE SET category = EXCLUDED.category RETURNING method_id;",
                            (m_name, m_cat)
                        )
                        method_cache[m_name] = cursor.fetchone()[0]

        # Step 7: Ingest Papers
        print("[*] Processing Papers...")
        for _, row in df.iterrows():
            v_name = str(row['venue_name']).strip()
            v_year = int(row['venue_year']) if pd.notna(row['venue_year']) else int(row['year'])
            venue_id = venue_cache.get((v_name, v_year))

            cursor.execute("""
                INSERT INTO Paper (
                    paper_id, title, year, doi, venue_id, abstract, page_count,
                    language, publisher, isbn_issn, pdf_filename, local_path,
                    file_size_kb, scholar_url, date_added, notes
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s
                );
            """, (
                row['paper_id'],
                row['title'],
                int(row['year']),
                row['doi'] if pd.notna(row['doi']) else None,
                venue_id,
                row['abstract'],
                int(row['page_count']) if pd.notna(row['page_count']) else None,
                row['language'] if pd.notna(row['language']) else 'English',
                row['publisher'] if pd.notna(row['publisher']) else None,
                row['isbn_issn'] if pd.notna(row['isbn_issn']) else None,
                row['pdf_filename'],
                row['local_path'],
                int(row['file_size_kb']) if pd.notna(row['file_size_kb']) else None,
                row['scholar_url'] if pd.notna(row['scholar_url']) else None,
                row['date_added'] if pd.notna(row['date_added']) else None,
                row['notes'] if pd.notna(row['notes']) else None
            ))

        # Step 8: Ingest Junction Tables
        print("[*] Processing Junction Tables...")
        for _, row in df.iterrows():
            p_id = row['paper_id']

            # Paper_Author (Auto-increments publication_count via Trigger!)
            authors = [a.strip() for a in str(row['authors']).split(';') if a.strip()]
            affils = [af.strip() for af in str(row['author_affiliations']).split(';')] if pd.notna(row['author_affiliations']) else []
            for idx, a_name in enumerate(authors):
                a_affil = affils[idx] if idx < len(affils) and affils[idx] else None
                a_id = author_cache.get((a_name, a_affil))
                cursor.execute(
                    "INSERT INTO Paper_Author (paper_id, author_id) VALUES (%s, %s) ON CONFLICT DO NOTHING;",
                    (p_id, a_id)
                )

            # Paper_Keyword
            kw_list = [k.strip() for k in str(row['keywords']).split(';') if k.strip()]
            for kw in kw_list:
                k_id = keyword_cache.get(kw)
                cursor.execute(
                    "INSERT INTO Paper_Keyword (paper_id, keyword_id) VALUES (%s, %s) ON CONFLICT DO NOTHING;",
                    (p_id, k_id)
                )

            # Paper_Dataset
            if pd.notna(row['datasets_used']) and str(row['datasets_used']).strip():
                d_names = [d.strip() for d in str(row['datasets_used']).split(';') if d.strip()]
                for d_name in d_names:
                    d_id = dataset_cache.get(d_name)
                    cursor.execute(
                        "INSERT INTO Paper_Dataset (paper_id, dataset_id) VALUES (%s, %s) ON CONFLICT DO NOTHING;",
                        (p_id, d_id)
                    )

            # Paper_Method
            if pd.notna(row['methodology']) and str(row['methodology']).strip():
                m_names = [m.strip() for m in str(row['methodology']).split(';') if m.strip()]
                for m_name in m_names:
                    m_id = method_cache.get(m_name)
                    cursor.execute(
                        "INSERT INTO Paper_Method (paper_id, method_id) VALUES (%s, %s) ON CONFLICT DO NOTHING;",
                        (p_id, m_id)
                    )

        # Step 9: Ingest Citations (Auto-increments citation_count via Trigger!)
        print("[*] Processing Citations...")
        for _, row in df.iterrows():
            citing_id = row['paper_id']
            if pd.notna(row['cited_paper_ids']) and str(row['cited_paper_ids']).strip():
                cited_ids = [c.strip() for c in str(row['cited_paper_ids']).split(';') if c.strip()]
                for cited_id in cited_ids:
                    cursor.execute(
                        "INSERT INTO Citation (citing_paper_id, cited_paper_id) VALUES (%s, %s) ON CONFLICT DO NOTHING;",
                        (citing_id, cited_id)
                    )

        # Commit entire atomic transaction
        conn.commit()
        print("\n[SUCCESS] Transaction committed successfully!")

        # Step 10: Verification queries
        print("\n--- DATABASE VERIFICATION SUMMARY ---")
        tables = [
            'Paper', 'Author', 'Venue', 'Keyword', 'Dataset', 'Methodology',
            'Paper_Author', 'Paper_Keyword', 'Paper_Dataset', 'Paper_Method', 'Citation'
        ]
        for tbl in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {tbl};")
            count = cursor.fetchone()[0]
            print(f"  • {tbl.ljust(16)}: {count} records")

        print("\n--- TRIGGER CHECK: TOP CITED PAPERS ---")
        cursor.execute("SELECT paper_id, title, citation_count FROM Paper WHERE citation_count > 0 ORDER BY citation_count DESC LIMIT 5;")
        for r in cursor.fetchall():
            print(f"  [{r[0]}] {r[1][:50]}... -> {r[2]} citations")

        print("\n--- TRIGGER CHECK: TOP AUTHORS (BY PUBLICATION COUNT) ---")
        cursor.execute("SELECT name, affiliation, publication_count FROM Author WHERE publication_count > 1 ORDER BY publication_count DESC LIMIT 5;")
        for r in cursor.fetchall():
            print(f"  • {r[0]} ({r[1]}): {r[2]} papers")

    except Exception as e:
        conn.rollback()
        print(f"\n[!] ETL FAILED with error: {e}")
        print("[!] Transaction rolled back. No corrupt data was committed.")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    run_etl()
