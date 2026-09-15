import os
import pandas as pd

def generate_demo_html(csv_file="papers.csv", output_html="search_results.html"):
    df = pd.read_csv(csv_file)
    
    rows_html = ""
    for _, row in df.iterrows():
        abs_path = os.path.abspath(row['local_path']).replace('\\', '/')
        file_url = f"file:///{abs_path}"
        scholar_url = row['scholar_url'] if pd.notna(row['scholar_url']) else f"https://scholar.google.com/scholar?q={row['title'].replace(' ', '+')}"
        
        rows_html += f"""
        <tr>
            <td><span class="badge-id">{row['paper_id']}</span></td>
            <td class="title-cell">
                <div class="title-text">{row['title']}</div>
                <div class="meta-sub">{row['authors']} &bull; <em>{row['venue_name']}</em> ({row['year']})</div>
            </td>
            <td><span class="badge-year">{row['year']}</span></td>
            <td><span class="badge-cite">{row['notes'] if 'planted' in str(row['notes']).lower() else 'Normal'}</span></td>
            <td class="action-cell">
                <a href="{file_url}" target="_blank" class="btn btn-pdf">📄 Open PDF</a>
                <a href="{scholar_url}" target="_blank" class="btn btn-scholar">🎓 Scholar</a>
            </td>
        </tr>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Recursive Influence Tracker — Research Papers Demo</title>
    <style>
        :root {{
            --bg: #0d1117;
            --surface: #161b22;
            --border: #30363d;
            --accent: #58a6ff;
            --accent-green: #238636;
            --accent-purple: #8957e5;
            --text: #c9d1d9;
            --text-heading: #f0f6fc;
            --muted: #8b949e;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; }}
        body {{ background: var(--bg); color: var(--text); padding: 30px 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        header {{ margin-bottom: 24px; padding-bottom: 16px; border-bottom: 1px solid var(--border); }}
        h1 {{ color: var(--text-heading); font-size: 26px; margin-bottom: 8px; }}
        p.subtitle {{ color: var(--muted); font-size: 14px; }}
        .search-box {{ margin: 20px 0; display: flex; gap: 12px; }}
        input#search {{
            flex: 1;
            padding: 12px 16px;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 6px;
            color: var(--text-heading);
            font-size: 15px;
            outline: none;
        }}
        input#search:focus {{ border-color: var(--accent); }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: var(--surface);
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid var(--border);
        }}
        th {{ background: #21262d; color: var(--text-heading); text-align: left; padding: 12px 16px; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid var(--border); }}
        td {{ padding: 14px 16px; border-bottom: 1px solid var(--border); font-size: 14px; vertical-align: middle; }}
        tr:hover td {{ background: rgba(88, 166, 255, 0.04); }}
        .title-text {{ font-weight: 600; color: var(--text-heading); margin-bottom: 4px; font-size: 15px; }}
        .meta-sub {{ color: var(--muted); font-size: 12.5px; }}
        .badge-id {{ background: #21262d; color: var(--accent); font-weight: bold; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-family: monospace; border: 1px solid var(--border); }}
        .badge-year {{ background: #1f242c; color: var(--text); padding: 3px 8px; border-radius: 4px; font-size: 12px; font-family: monospace; }}
        .badge-cite {{ font-size: 11px; padding: 3px 8px; border-radius: 12px; background: rgba(137, 87, 229, 0.15); color: #d2a8ff; border: 1px solid rgba(137, 87, 229, 0.4); }}
        .action-cell {{ display: flex; gap: 8px; }}
        .btn {{
            text-decoration: none;
            padding: 6px 12px;
            border-radius: 5px;
            font-size: 12px;
            font-weight: 500;
            display: inline-flex;
            align-items: center;
            transition: 0.2s;
        }}
        .btn-pdf {{ background: var(--surface); border: 1px solid var(--border); color: var(--accent); }}
        .btn-pdf:hover {{ background: rgba(88, 166, 255, 0.15); border-color: var(--accent); }}
        .btn-scholar {{ background: var(--accent-green); color: #fff; border: 1px solid transparent; }}
        .btn-scholar:hover {{ background: #2ea043; }}
        .stats {{ display: flex; gap: 20px; margin-bottom: 16px; font-size: 13px; color: var(--muted); }}
        .stat-item {{ background: var(--surface); padding: 8px 14px; border-radius: 6px; border: 1px solid var(--border); }}
        .stat-val {{ color: var(--accent); font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Recursive Influence Tracker</h1>
            <p class="subtitle">Database Management Systems (22AIE303) &bull; Team 6 &bull; Search & Output Layer</p>
        </header>

        <div class="stats">
            <div class="stat-item">Total Papers: <span class="stat-val">{len(df)}</span></div>
            <div class="stat-item">Local Storage: <span class="stat-val">data/</span></div>
            <div class="stat-item">Cycle Detection Demo: <span class="stat-val">P004 &harr; P005 &harr; P007</span></div>
        </div>

        <div class="search-box">
            <input type="text" id="search" placeholder="Quick filter by title, author, keyword, or year..." onkeyup="filterTable()">
        </div>

        <table id="papersTable">
            <thead>
                <tr>
                    <th style="width: 80px;">ID</th>
                    <th>Title & Citation Metadata</th>
                    <th style="width: 80px;">Year</th>
                    <th style="width: 110px;">Graph Role</th>
                    <th style="width: 220px;">Actions</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </div>

    <script>
        function filterTable() {{
            const input = document.getElementById("search").value.toLowerCase();
            const rows = document.querySelectorAll("#papersTable tbody tr");
            rows.forEach(row => {{
                const text = row.innerText.toLowerCase();
                row.style.display = text.includes(input) ? "" : "none";
            }});
        }}
    </script>
</body>
</html>
"""
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"[+] Successfully generated {output_html} with interactive search and clickable links!")

if __name__ == "__main__":
    generate_demo_html()
