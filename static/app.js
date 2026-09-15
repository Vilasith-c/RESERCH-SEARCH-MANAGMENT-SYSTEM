// ==========================================================================
// Research Hub — Application Logic & Query Engine
// ==========================================================================

let allPapers = [];
let savedPaperIds = new Set(JSON.parse(localStorage.getItem("research_hub_saved") || "[]"));
let activeSqlString = "";
let currentSearchQuery = "";
let debounceTimer = null;
let currentAppMode = "home"; // "home" or "results"

document.addEventListener("DOMContentLoaded", () => {
    initResearchHub();
});

function initResearchHub() {
    updateSavedCountBadge();
    setupEventListeners();
    setAppMode("home");
}

function setAppMode(mode) {
    currentAppMode = mode;
    const wrapper = document.querySelector(".app-wrapper");
    const mainBody = document.getElementById("mainBodyContainer");

    if (mode === "home") {
        if (wrapper) {
            wrapper.classList.remove("mode-results");
            wrapper.classList.add("mode-home");
        }
        if (mainBody) mainBody.style.display = "none";
        document.getElementById("btnNavPapers")?.classList.add("active");
    } else {
        if (wrapper) {
            wrapper.classList.remove("mode-home");
            wrapper.classList.add("mode-results");
        }
        if (mainBody) mainBody.style.display = "block";
    }
}

function goToHomePage() {
    const input = document.getElementById("globalSearchInput");
    if (input) input.value = "";
    const btnClear = document.getElementById("btnClearInput");
    if (btnClear) btnClear.style.display = "none";
    setAppMode("home");
    window.scrollTo({ top: 0, behavior: "smooth" });
}

// --------------------------------------------------------------------------
// 1. DATA FETCHING & API INTERACTION
// --------------------------------------------------------------------------
async function fetchAndDisplayPapers(query) {
    currentSearchQuery = query;
    setAppMode("results");
    const skeleton = document.getElementById("loadingSkeleton");
    const container = document.getElementById("papersList");
    const emptyState = document.getElementById("emptyState");
    const countDisplay = document.getElementById("resultsCount");

    container.style.display = "none";
    emptyState.style.display = "none";
    skeleton.style.display = "flex";

    try {
        const url = `/api/search?q=${encodeURIComponent(query)}&filter_type=all`;
        const res = await fetch(url);
        const data = await res.json();

        allPapers = data.results || [];
        activeSqlString = data.sql_query || "-- No query generated";

        document.getElementById("sqlModalCodeBlock").innerText = activeSqlString;

        skeleton.style.display = "none";
        applySidebarFiltersAndRender();
    } catch (e) {
        console.error("Failed to fetch papers:", e);
        skeleton.style.display = "none";
        container.style.display = "block";
        container.innerHTML = `<div style="padding: 24px; color: #e11d48;">Error connecting to search service.</div>`;
    }
}

// --------------------------------------------------------------------------
// 2. CLIENT-SIDE FILTERING & SORTING
// --------------------------------------------------------------------------
function applySidebarFiltersAndRender() {
    let filtered = [...allPapers];

    // Year Filter
    const selectedYear = document.querySelector('input[name="yearFilter"]:checked')?.value || "all";
    if (selectedYear !== "all") {
        const minYear = parseInt(selectedYear, 10);
        filtered = filtered.filter(p => p.year >= minYear);
    }

    // Availability Filters
    const requireLocal = document.getElementById("chkLocalPdf")?.checked;
    if (requireLocal) {
        filtered = filtered.filter(p => p.pdf_url && p.pdf_url.trim().length > 0);
    }

    // Research Area Filters
    const activeAreas = Array.from(document.querySelectorAll('.area-filter:checked')).map(cb => cb.value);
    if (activeAreas.length > 0 && activeAreas.length < 4) {
        filtered = filtered.filter(p => {
            const kw = (p.keywords || "").toLowerCase();
            const title = (p.title || "").toLowerCase();
            const text = kw + " " + title;
            return activeAreas.some(area => {
                if (area === "database") return text.includes("database") || text.includes("dbms") || text.includes("relational");
                if (area === "distributed") return text.includes("distributed") || text.includes("cluster") || text.includes("google");
                if (area === "retrieval") return text.includes("retrieval") || text.includes("index") || text.includes("search");
                if (area === "graph") return text.includes("graph") || text.includes("semantic") || text.includes("network");
                return true;
            });
        });
    }

    // Sorting
    const sortVal = document.getElementById("sortSelector")?.value || "citations";
    if (sortVal === "citations") {
        filtered.sort((a, b) => b.citation_count - a.citation_count);
    } else if (sortVal === "year_desc") {
        filtered.sort((a, b) => b.year - a.year);
    } else if (sortVal === "year_asc") {
        filtered.sort((a, b) => a.year - b.year);
    }

    // Update count & render
    document.getElementById("resultsCount").innerText = filtered.length;
    renderPaperCards(filtered);
}

// --------------------------------------------------------------------------
// 3. PAPER CARD RENDERING
// --------------------------------------------------------------------------
function renderPaperCards(papers) {
    const container = document.getElementById("papersList");
    const emptyState = document.getElementById("emptyState");

    if (papers.length === 0) {
        container.style.display = "none";
        emptyState.style.display = "block";
        return;
    }

    emptyState.style.display = "none";
    container.style.display = "flex";
    container.innerHTML = "";

    papers.forEach(p => {
        const isSaved = savedPaperIds.has(p.paper_id);
        const card = document.createElement("article");
        card.className = "paper-card";

        // Abstract snippet
        const fullAbs = p.abstract || "No abstract available.";
        const shortAbs = fullAbs.length > 210 ? fullAbs.substring(0, 210) + "..." : fullAbs;
        const needsMore = fullAbs.length > 210;

        card.innerHTML = `
            <div class="card-badges-row">
                <span class="badge-pill badge-pdf-available">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
                    PDF Available
                </span>
                <span class="badge-pill badge-local-disk">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="9" y1="3" x2="9" y2="21"></line></svg>
                    Local File
                </span>
                <span class="badge-pill badge-year-tag">${p.year}</span>
                <span class="badge-pill badge-citations-count">★ ${p.citation_count} citations</span>
            </div>

            <h3 class="card-paper-title">
                <a href="${p.pdf_url}" target="_blank">${p.title}</a>
            </h3>

            <div class="card-metadata-line">
                <strong>${p.authors}</strong> · <span class="venue-text">${p.venue}</span> · <span>${p.year}</span>
            </div>

            <div class="card-abstract-snippet" id="abs_${p.paper_id}">
                <span class="abs-text">${shortAbs}</span>
                ${needsMore ? `<button class="btn-read-more" onclick="toggleReadMore('${p.paper_id}', this)">Read more</button>` : ''}
            </div>

            <div class="card-actions-bar">
                <a href="${p.pdf_url}" target="_blank" class="card-btn card-btn-primary" title="Open paper in browser PDF viewer">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
                    Open PDF
                </a>
                <a href="javascript:void(0)" onclick="alert('Local file path:\\n${p.pdf_url.substring(1)}')" class="card-btn card-btn-emerald" title="View local file location">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>
                    Local File
                </a>
                <a href="${p.scholar_url}" target="_blank" class="card-btn card-btn-secondary" title="View on Google Scholar">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>
                    Scholar
                </a>
                <button class="card-btn-save ${isSaved ? 'saved' : ''}" onclick="toggleSavePaper('${p.paper_id}', this)" title="Save to collection">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="${isSaved ? 'currentColor' : 'none'}" stroke="currentColor" stroke-width="2"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path></svg>
                    <span>${isSaved ? 'Saved' : 'Save'}</span>
                </button>
                <button class="card-btn card-btn-secondary" onclick="openInfluenceModal('${p.paper_id}', '${escapeQuotes(p.title)}')" title="Trace downstream influence via recursive CTE">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="18" cy="5" r="3"></circle><circle cx="6" cy="12" r="3"></circle><circle cx="18" cy="19" r="3"></circle><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line></svg>
                    Influence Chain
                </button>
                <span class="card-extra-meta">${p.citation_count} citations · 12 related</span>
            </div>
        `;

        // Store full abstract on element for expand/collapse
        card.querySelector(`#abs_${p.paper_id}`).dataset.full = fullAbs;
        card.querySelector(`#abs_${p.paper_id}`).dataset.short = shortAbs;

        container.appendChild(card);
    });
}

// --------------------------------------------------------------------------
// 4. EVENT LISTENERS & SEARCH HANDLERS
// --------------------------------------------------------------------------
function setupEventListeners() {
    const input = document.getElementById("globalSearchInput");
    const btnClear = document.getElementById("btnClearInput");

    // Debounced live search only when already in results mode
    input.addEventListener("input", (e) => {
        const val = e.target.value.trim();
        btnClear.style.display = val.length > 0 ? "block" : "none";
        
        if (currentAppMode === "results") {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                if (val.length === 0) {
                    goToHomePage();
                } else {
                    fetchAndDisplayPapers(val);
                }
            }, 300);
        }
    });

    btnClear.addEventListener("click", () => {
        goToHomePage();
        input.focus();
    });

    // Brand link and nav papers return to clean home page
    document.getElementById("brandLink")?.addEventListener("click", (e) => {
        e.preventDefault();
        goToHomePage();
    });
    document.getElementById("btnNavPapers")?.addEventListener("click", (e) => {
        e.preventDefault();
        goToHomePage();
    });

    // Top buttons
    document.getElementById("btnOpenSqlModal")?.addEventListener("click", () => openModal("sqlModal"));
    document.getElementById("btnOpenCycleModal")?.addEventListener("click", () => openCycleDetectionModal());
    document.getElementById("btnNavCollections")?.addEventListener("click", () => openCollectionsModal());
    document.getElementById("btnNavAnalytics")?.addEventListener("click", () => openAnalyticsModal());
}

function handleSearchSubmit(e) {
    if (e) e.preventDefault();
    const query = document.getElementById("globalSearchInput").value.trim();
    fetchAndDisplayPapers(query);
}

function applyTagSearch(tag) {
    const input = document.getElementById("globalSearchInput");
    input.value = tag;
    document.getElementById("btnClearInput").style.display = "block";
    fetchAndDisplayPapers(tag);
}

function resetSearch() {
    goToHomePage();
}

function handleFilterChange() {
    applySidebarFiltersAndRender();
}

function handleSortChange() {
    applySidebarFiltersAndRender();
}

function resetAllFilters() {
    // Reset Year
    const defaultYear = document.querySelector('input[name="yearFilter"][value="all"]');
    if (defaultYear) defaultYear.checked = true;

    // Reset Checkboxes
    document.querySelectorAll('.filters-card input[type="checkbox"]').forEach(cb => cb.checked = true);

    applySidebarFiltersAndRender();
}

// Read more / less toggle
function toggleReadMore(paperId, btn) {
    const box = document.getElementById(`abs_${paperId}`);
    const textSpan = box.querySelector(".abs-text");
    if (btn.innerText === "Read more") {
        textSpan.innerText = box.dataset.full;
        btn.innerText = "Read less";
    } else {
        textSpan.innerText = box.dataset.short;
        btn.innerText = "Read more";
    }
}

// --------------------------------------------------------------------------
// 5. BOOKMARK / COLLECTIONS MANAGEMENT
// --------------------------------------------------------------------------
function toggleSavePaper(paperId, btn) {
    const isCurrentlySaved = savedPaperIds.has(paperId);
    if (isCurrentlySaved) {
        savedPaperIds.delete(paperId);
        btn.classList.remove("saved");
        btn.querySelector("span").innerText = "Save";
        btn.querySelector("svg").setAttribute("fill", "none");
    } else {
        savedPaperIds.add(paperId);
        btn.classList.add("saved");
        btn.querySelector("span").innerText = "Saved";
        btn.querySelector("svg").setAttribute("fill", "currentColor");
    }
    localStorage.setItem("research_hub_saved", JSON.stringify(Array.from(savedPaperIds)));
    updateSavedCountBadge();
}

function updateSavedCountBadge() {
    const badge = document.getElementById("collectionsCount");
    if (badge) badge.innerText = savedPaperIds.size;
}

// --------------------------------------------------------------------------
// 6. MODAL CONTROLLERS (SQL, Cycle, Influence, Analytics, Collections)
// --------------------------------------------------------------------------
function openModal(id) {
    const m = document.getElementById(id);
    if (m) m.style.display = "flex";
}

function closeModal(id) {
    const m = document.getElementById(id);
    if (m) m.style.display = "none";
}

// Cycle Detection Modal
async function openCycleDetectionModal() {
    openModal("cycleModal");
    const list = document.getElementById("cycleResultsList");
    const sqlBlock = document.getElementById("cycleSqlCode");

    list.innerHTML = `<div style="padding: 12px; color: #64748b;">Executing cycle detection query against PostgreSQL...</div>`;

    try {
        const res = await fetch("/api/cycle-detection");
        const data = await res.json();
        sqlBlock.innerText = data.sql_query;

        list.innerHTML = "";
        if (data.cycles && data.cycles.length > 0) {
            data.cycles.forEach(c => {
                const item = document.createElement("div");
                item.className = "cycle-item-row";
                item.innerHTML = `
                    <div style="font-family: var(--font-mono); font-weight: 700; color: #e11d48; margin-bottom: 4px;">
                        🔁 Loop: ${c.circular_chain}
                    </div>
                    <div style="font-size: 12px; color: #64748b;">
                        Cycle Depth: ${c.depth} citation hops &bull; Origin: ${c.start_paper}
                    </div>
                `;
                list.appendChild(item);
            });
        } else {
            list.innerHTML = `<div style="color: #059669; padding: 12px;">No circular cycles detected.</div>`;
        }
    } catch (e) {
        list.innerHTML = `<div style="color: #e11d48; padding: 12px;">Error executing cycle query.</div>`;
    }
}

// Recursive Influence Modal
async function openInfluenceModal(paperId, title) {
    openModal("influenceModal");
    document.getElementById("influenceModalHeading").innerText = `Influence: ${paperId} — ${title}`;
    const list = document.getElementById("influenceChainNodes");
    const sqlBlock = document.getElementById("influenceSqlCode");

    list.innerHTML = `<div style="padding: 12px; color: #64748b;">Traversing citation graph using recursive CTE...</div>`;

    try {
        const res = await fetch(`/api/citation-chain/${paperId}`);
        const data = await res.json();
        sqlBlock.innerText = data.sql_query;

        list.innerHTML = "";
        if (data.chain && data.chain.length > 0) {
            data.chain.forEach(c => {
                const node = document.createElement("div");
                node.className = "timeline-node-row";
                node.innerHTML = `
                    <div style="margin-bottom: 2px;">
                        <span class="badge-pill badge-pdf-available" style="font-size: 11px;">Hop ${c.citation_distance}</span>
                        <strong>[${c.downstream_paper_id}]</strong> ${c.downstream_title} (${c.downstream_year})
                    </div>
                    <div style="font-family: var(--font-mono); font-size: 11.5px; color: #2563eb; margin-top: 4px;">
                        Chain: ${c.citation_path}
                    </div>
                `;
                list.appendChild(node);
            });
        } else {
            list.innerHTML = `<div style="padding: 14px; color: #64748b; background: #f8fafc; border-radius: 6px;">This work has not yet been cited by other papers in the local database.</div>`;
        }
    } catch (e) {
        list.innerHTML = `<div style="color: #e11d48; padding: 12px;">Error traversing influence chain.</div>`;
    }
}

// Collections Modal
function openCollectionsModal() {
    openModal("collectionsModal");
    const container = document.getElementById("savedPapersList");
    container.innerHTML = "";

    const saved = allPapers.filter(p => savedPaperIds.has(p.paper_id));
    if (saved.length === 0) {
        container.innerHTML = `<div style="padding: 24px; text-align: center; color: #64748b;">No saved papers yet. Click "Save" on any paper card to bookmark it.</div>`;
        return;
    }

    saved.forEach(p => {
        const row = document.createElement("div");
        row.className = "saved-item-row";
        row.innerHTML = `
            <div>
                <strong>${p.title}</strong>
                <div style="font-size: 12px; color: #64748b;">${p.authors} (${p.year})</div>
            </div>
            <a href="${p.pdf_url}" target="_blank" class="card-btn card-btn-primary" style="padding: 4px 10px; font-size: 12px;">Open PDF</a>
        `;
        container.appendChild(row);
    });
}

// Analytics Modal
async function openAnalyticsModal() {
    openModal("analyticsModal");
    try {
        const res = await fetch("/api/stats");
        const data = await res.json();
        document.getElementById("analyticsPapers").innerText = data.papers || 18;
        document.getElementById("analyticsAuthors").innerText = data.authors || 68;
        document.getElementById("analyticsCitations").innerText = data.citations || 30;
        document.getElementById("analyticsBenchmarks").innerText = data.datasets || 34;
    } catch (e) {
        console.warn(e);
    }
}

function copySqlCode() {
    const code = document.getElementById("sqlModalCodeBlock").innerText;
    navigator.clipboard.writeText(code).then(() => {
        const btn = document.getElementById("btnCopySqlModal");
        btn.innerText = "✓ Copied!";
        setTimeout(() => btn.innerText = "Copy Query", 1600);
    });
}

function escapeQuotes(str) {
    if (!str) return "";
    return str.replace(/'/g, "\\'").replace(/"/g, "&quot;");
}
