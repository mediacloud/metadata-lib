(function () {
  "use strict";

  // text_content is rendered via the precomputed diff instead.
  const SKIP_TABLE_KEYS = new Set(["text_content", "error"]);
  // fields that differ because of library/pipeline versioning, not extraction quality -
  // flagged as warnings (yellow) rather than diffs (red).
  const WARNING_KEYS = new Set(["parsed_date", "unique_url_hash", "version"]);

  let docs = [];
  let summary = null;
  let filteredDocs = [];
  let domainFilter = "";
  let langFilter = "";
  let fieldErrorFilter = "";
  let currentDocId = null;

  const el = (id) => document.getElementById(id);

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function formatValue(v) {
    if (v === undefined) return "—";
    if (v === null) return "null";
    if (typeof v === "object") return JSON.stringify(v);
    return String(v);
  }

  function similarityClass(similarity) {
    if (similarity === null || similarity === undefined) return "";
    if (similarity < 0.7) return "low";
    if (similarity > 0.95) return "high";
    return "mid";
  }

  function readStateFromUrl() {
    const params = new URLSearchParams(window.location.search);
    return {
      domain: params.get("domain") || "",
      lang: params.get("lang") || "",
      field: params.get("field") || "",
      doc: params.get("doc") || null,
    };
  }

  function syncUrl() {
    const url = new URL(window.location.href);
    const params = url.searchParams;
    domainFilter ? params.set("domain", domainFilter) : params.delete("domain");
    langFilter ? params.set("lang", langFilter) : params.delete("lang");
    fieldErrorFilter ? params.set("field", fieldErrorFilter) : params.delete("field");
    currentDocId ? params.set("doc", currentDocId) : params.delete("doc");
    history.replaceState(null, "", url.toString());
  }

  function showSummary({ updateHistory = true } = {}) {
    currentDocId = null;
    el("doc-view").style.display = "none";
    el("summary-view").style.display = "block";
    document.querySelectorAll("#doc-list li").forEach((li) => li.classList.remove("active"));
    if (updateHistory) syncUrl();
  }

  // When the new code failed to process this doc at all, there's nothing meaningful to compare
  // field-by-field - render plain empty boxes under "new" instead of flagging every row as a diff.
  function renderMetaTable(oldMeta, newMeta, newFailed) {
    const keys = new Set([...Object.keys(oldMeta || {}), ...Object.keys(newMeta || {})]);
    const tbody = el("meta-body");
    tbody.innerHTML = "";
    Array.from(keys)
      .filter((k) => !SKIP_TABLE_KEYS.has(k))
      .sort()
      .forEach((key) => {
        const oldVal = oldMeta ? oldMeta[key] : undefined;
        const oldStr = formatValue(oldVal);
        let newStr = "—";
        let oldClass = "";
        let newClass = "";
        if (newFailed) {
          newClass = "empty";
        } else {
          const newVal = newMeta ? newMeta[key] : undefined;
          newStr = formatValue(newVal);
          const differs = oldStr !== newStr;
          if (differs) oldClass = newClass = WARNING_KEYS.has(key) ? "warn" : "diff";
        }
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <th>${escapeHtml(key)}</th>
          <td class="value ${oldClass}">${escapeHtml(oldStr)}</td>
          <td class="value ${newClass}">${escapeHtml(newStr)}</td>
        `;
        tbody.appendChild(tr);
      });
  }

  // Renders a diff precomputed server-side by difflib (list of {type, text} ops).
  function renderTextDiff(textComparison, oldText, newText) {
    const badge = el("similarity-badge");
    const note = el("diff-note");
    note.style.display = "none";

    if (!textComparison) {
      badge.textContent = "";
      el("text-diff").innerHTML = "<em>(no comparison available)</em>";
      return;
    }

    const pct = Math.round((textComparison.similarity || 0) * 100);
    badge.textContent = `${pct}% similar`;
    badge.className = "similarity-badge " + similarityClass(textComparison.similarity);

    if (textComparison.truncated || !textComparison.diff) {
      note.style.display = "block";
      note.textContent =
        "Text is very long — showing full old/new text side-by-side instead of an inline diff " +
        "(similarity score is an approximation).";
      el("text-diff").innerHTML = `
        <div class="fallback-columns">
          <div><h4>Old</h4>${escapeHtml(oldText || "")}</div>
          <div><h4>New</h4>${escapeHtml(newText || "")}</div>
        </div>
      `;
      return;
    }

    let html = "";
    for (const op of textComparison.diff) {
      if (op.type === "equal") {
        html += escapeHtml(op.text);
      } else if (op.type === "delete") {
        html += `<span class="diff-del">${escapeHtml(op.text)}</span>`;
      } else if (op.type === "insert") {
        html += `<span class="diff-ins">${escapeHtml(op.text)}</span>`;
      }
    }
    el("text-diff").innerHTML = html || "<em>(empty)</em>";
  }

  async function loadDocById(id, { updateHistory = true } = {}) {
    const docSummary = docs.find((d) => d.id === id);
    if (!docSummary) return;
    currentDocId = id;

    document.querySelectorAll("#doc-list li").forEach((li) => {
      li.classList.toggle("active", li.dataset.id === id);
    });

    el("summary-view").style.display = "none";
    el("doc-view").style.display = "block";
    el("doc-title").textContent = docSummary.title || "(untitled)";
    el("doc-url").innerHTML = `<a href="${escapeHtml(docSummary.url)}" target="_blank" rel="noopener">${escapeHtml(docSummary.url)}</a>`;

    const doc = await fetch(`data/${id}.json`).then((r) => r.json());

    const newFailed = Boolean(doc.new && doc.new.error);
    const errorBanner = el("error-banner");
    if (newFailed) {
      errorBanner.style.display = "block";
      errorBanner.textContent = `Extraction failed on new code: ${doc.new.error}`;
      el("text-section").style.display = "none";
    } else {
      errorBanner.style.display = "none";
      el("text-section").style.display = "block";
    }

    renderMetaTable(doc.old, doc.new, newFailed);
    renderTextDiff(
      doc.text_comparison,
      doc.old ? doc.old.text_content : "",
      doc.new ? doc.new.text_content : ""
    );

    if (updateHistory) syncUrl();
  }

  function currentFilteredIndex() {
    return filteredDocs.findIndex((d) => d.id === currentDocId);
  }

  function renderList() {
    const list = el("doc-list");
    list.innerHTML = "";
    filteredDocs.forEach((doc) => {
      const li = document.createElement("li");
      li.dataset.id = doc.id;
      if (doc.id === currentDocId) li.classList.add("active");
      if (doc.error) li.classList.add("has-error");
      const dotClass = doc.error ? "" : similarityClass(doc.similarity);
      li.innerHTML = `
        <span class="sim-dot ${dotClass}"></span>
        <span class="doc-text">
          <span class="doc-title">${escapeHtml(doc.title || doc.id)}</span>
          <span class="doc-url">${escapeHtml(doc.url || "")}</span>
        </span>
      `;
      li.addEventListener("click", () => loadDocById(doc.id));
      list.appendChild(li);
    });
    el("doc-count").textContent = `${filteredDocs.length} of ${docs.length} stories`;
  }

  function populateFilterOptions() {
    const domains = Array.from(new Set(docs.map((d) => d.canonical_domain).filter(Boolean))).sort();
    const languages = Array.from(new Set(docs.map((d) => d.language).filter(Boolean))).sort();

    const domainSelect = el("filter-domain");
    domains.forEach((domain) => {
      const opt = document.createElement("option");
      opt.value = domain;
      opt.textContent = domain;
      domainSelect.appendChild(opt);
    });

    const langSelect = el("filter-language");
    languages.forEach((lang) => {
      const opt = document.createElement("option");
      opt.value = lang;
      opt.textContent = lang;
      langSelect.appendChild(opt);
    });

    const fields = summary && summary.field_stats ? Object.keys(summary.field_stats).sort() : [];
    const fieldSelect = el("filter-field-error");
    fields.forEach((field) => {
      const opt = document.createElement("option");
      opt.value = field;
      opt.textContent = field;
      fieldSelect.appendChild(opt);
    });
  }

  // A doc whose new extraction failed entirely trivially "has an error" for every field.
  function docHasFieldError(doc, field) {
    if (doc.error) return true;
    return Boolean(doc.field_errors && doc.field_errors.includes(field));
  }

  function applyFilters() {
    filteredDocs = docs.filter(
      (d) =>
        (!domainFilter || d.canonical_domain === domainFilter) &&
        (!langFilter || d.language === langFilter) &&
        (!fieldErrorFilter || docHasFieldError(d, fieldErrorFilter))
    );
    if (el("sort-order").value === "similarity") {
      filteredDocs.sort((a, b) => {
        const sa = a.error ? -1 : a.similarity ?? 1;
        const sb = b.error ? -1 : b.similarity ?? 1;
        return sa - sb;
      });
    }
    renderList();
  }

  function renderSummaryView() {
    if (!summary) return;

    const errorRate = summary.total_docs
      ? Math.round((summary.error_docs / summary.total_docs) * 100)
      : 0;
    el("summary-stats").innerHTML = `
      <div class="stat-tile">
        <div class="stat-value">${summary.total_docs}</div>
        <div class="stat-label">Total stories compared</div>
      </div>
      <div class="stat-tile${summary.error_docs ? " warn" : ""}">
        <div class="stat-value">${summary.error_docs} (${errorRate}%)</div>
        <div class="stat-label">New code failed to extract entirely</div>
      </div>
    `;

    const rows = Object.entries(summary.field_stats)
      .map(([field, stats]) => {
        const total = stats.success + stats.error;
        const rate = total ? stats.success / total : 1;
        return { field, ...stats, total, rate };
      })
      .sort((a, b) => b.error - a.error || a.field.localeCompare(b.field));

    el("field-stats-body").innerHTML = rows
      .map((r) => {
        const pct = Math.round(r.rate * 100);
        const rateClass = r.rate < 0.9 ? "match-rate-low" : r.rate === 1 ? "match-rate-high" : "";
        return `
          <tr>
            <th>${escapeHtml(r.field)}</th>
            <td class="value">${r.success}</td>
            <td class="value">${r.error}</td>
            <td class="value ${rateClass}">${pct}%</td>
          </tr>
        `;
      })
      .join("");

    const buckets = summary.similarity_histogram;
    const maxCount = Math.max(1, ...buckets.map((b) => b.count));
    el("similarity-histogram").innerHTML = buckets
      .map((b) => {
        const heightPx = b.count ? Math.max(3, Math.round((b.count / maxCount) * 130)) : 0;
        return `
          <div class="hist-col">
            <div class="hist-count">${b.count}</div>
            <div class="hist-bar" style="height:${heightPx}px"></div>
            <div class="hist-label">${b.bucket}</div>
          </div>
        `;
      })
      .join("");
  }

  el("filter-domain").addEventListener("change", (e) => {
    domainFilter = e.target.value;
    applyFilters();
    syncUrl();
  });
  el("filter-language").addEventListener("change", (e) => {
    langFilter = e.target.value;
    applyFilters();
    syncUrl();
  });
  el("filter-field-error").addEventListener("change", (e) => {
    fieldErrorFilter = e.target.value;
    applyFilters();
    syncUrl();
  });
  el("sort-order").addEventListener("change", applyFilters);
  el("prev-btn").addEventListener("click", () => {
    const idx = currentFilteredIndex();
    const newIdx = idx <= 0 ? 0 : idx - 1;
    if (filteredDocs[newIdx]) loadDocById(filteredDocs[newIdx].id);
  });
  el("next-btn").addEventListener("click", () => {
    const idx = currentFilteredIndex();
    const newIdx = idx < 0 ? 0 : idx + 1;
    if (filteredDocs[newIdx]) loadDocById(filteredDocs[newIdx].id);
  });
  el("summary-title").addEventListener("click", () => showSummary());

  fetch("data/meta.json")
    .then((r) => r.json())
    .then((meta) => {
      if (meta && meta.source_warc) {
        document.title = `Metadata extraction comparison — ${meta.source_warc}`;
        el("source-warc").textContent = meta.source_warc;
      }
    })
    .catch((err) => console.error(err));

  Promise.all([
    fetch("data/docs.json").then((r) => r.json()),
    fetch("data/summary.json").then((r) => r.json()),
  ])
    .then(([docsData, summaryData]) => {
      docs = docsData;
      summary = summaryData;

      const initial = readStateFromUrl();
      domainFilter = initial.domain;
      langFilter = initial.lang;
      fieldErrorFilter = initial.field;

      populateFilterOptions();
      el("filter-domain").value = domainFilter;
      el("filter-language").value = langFilter;
      el("filter-field-error").value = fieldErrorFilter;

      applyFilters();
      renderSummaryView();
      if (initial.doc) {
        loadDocById(initial.doc, { updateHistory: false });
      } else {
        showSummary({ updateHistory: false });
      }
    })
    .catch((err) => {
      el("doc-count").textContent = "Failed to load comparison data";
      console.error(err);
    });
})();
