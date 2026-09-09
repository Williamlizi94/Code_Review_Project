(function () {
  "use strict";

  const CG = window.CodeGuardian;
  const page = window.location.pathname.split("/").pop() || "index.html";
  const protectedPages = new Set([
    "02-dashboard.html",
    "03-submit-review.html",
    "04-review-list.html",
    "05-review-detail.html",
    "06-issue-viewer.html",
    "07-report-viewer.html",
    "08-knowledge-base.html",
    "09-webhook-setup.html",
    "10-quality-gate.html",
  ]);

  const one = function (selector, root) { return (root || document).querySelector(selector); };
  const all = function (selector, root) { return Array.from((root || document).querySelectorAll(selector)); };
  const esc = CG.escape;

  function errorMessage(error) {
    return error && error.message ? error.message : "Unable to reach the API";
  }

  function statusClass(status) {
    return "b-" + String(status || "pending").toLowerCase();
  }

  function gateMarkup(status) {
    const gate = status || "SKIPPED";
    const cls = gate === "PASS" ? "gate-pass" : gate === "FAIL" ? "gate-fail" : "gate-skip";
    return '<span class="' + cls + '">' + esc(gate) + "</span>";
  }

  function language(review) {
    return Array.isArray(review.languages) && review.languages.length ? review.languages.join(", ") : "Auto";
  }

  function detailHref(reviewId, issueId) {
    let href = "05-review-detail.html?id=" + encodeURIComponent(reviewId);
    if (issueId) href = "06-issue-viewer.html?id=" + encodeURIComponent(reviewId) + "&issue=" + encodeURIComponent(issueId);
    return href;
  }

  function updateUser(user) {
    if (!user) return;
    all(".sb-uname").forEach(function (element) { element.textContent = user.full_name || user.email; });
    all(".sb-uemail").forEach(function (element) { element.textContent = user.email; });
    all(".sb-avatar").forEach(function (element) {
      element.textContent = (user.full_name || user.email || "U").charAt(0).toUpperCase();
    });
    const footer = one(".sb-footer");
    if (footer && !one("#cgLogout")) {
      const logout = document.createElement("button");
      logout.id = "cgLogout";
      logout.className = "sb-item";
      logout.type = "button";
      logout.style.cssText = "width:100%;border:0;background:transparent;cursor:pointer;text-align:left";
      logout.textContent = "Log out";
      logout.addEventListener("click", function () {
        CG.clearSession();
        window.location.href = "01-login.html";
      });
      footer.appendChild(logout);
    }
  }

  async function loadCurrentUser() {
    const cached = CG.cachedUser();
    if (cached) updateUser(cached);
    try {
      const user = await CG.me();
      CG.setSession(CG.token(), user);
      updateUser(user);
      return user;
    } catch (error) {
      if (error.status === 401) window.location.replace("01-login.html");
      throw error;
    }
  }

  async function latestReview() {
    const result = await CG.reviews({ page: 0, size: 1 });
    return result.items[0] || null;
  }

  async function selectedReview() {
    const id = new URLSearchParams(window.location.search).get("id");
    if (id) return CG.review(id);
    const latest = await latestReview();
    if (!latest) throw new Error("No reviews yet. Submit a review first.");
    return CG.review(latest.id);
  }

  function reviewRow(review, includeDate) {
    const submitted = includeDate ? "<td><span class=\"mono\">" + esc(CG.formatDate(review.created_at)) + "</span></td>" : "";
    return '<tr data-status="' + esc(review.status) + '" data-lang="' + esc(language(review).toLowerCase()) + '" data-gate="' + esc(review.quality_gate_status) + '">' +
      '<td><span class="mono">' + esc(CG.shortTarget(review)) + "</span></td>" +
      '<td><span class="type-tag">' + esc(review.type) + "</span></td>" +
      "<td>" + esc(language(review)) + "</td>" +
      "<td>" + esc(review.issues_count) + "</td>" +
      '<td><span class="sev ' + (review.critical_count ? "sev-critical" : "sev-0") + '">' + esc(review.critical_count) + "</span></td>" +
      "<td>" + gateMarkup(review.quality_gate_status) + "</td>" +
      '<td><span class="badge ' + statusClass(review.status) + '">' + esc(review.status) + "</span></td>" +
      submitted +
      '<td><a href="' + detailHref(review.id) + '" class="link row-link">Detail</a></td></tr>';
  }

  function initLogin() {
    window.doLogin = async function () {
      const email = one("#lEmail").value.trim();
      const password = one("#lPass").value;
      const button = one("#paneLogin .btn-primary");
      if (!email || !password) return window.alert_("alertLogin", "error", "Please enter email and password");
      button.disabled = true;
      button.textContent = "Logging in...";
      try {
        const auth = await CG.login(email, password);
        CG.setSession(auth.access_token);
        const user = await CG.me();
        CG.setSession(auth.access_token, user);
        one("#loginBody").textContent = JSON.stringify(auth, null, 2);
        one("#loginUser").innerHTML = '<div class="user-row"><span class="uk">User ID</span><span>' + esc(user.id) + '</span></div><div class="user-row"><span class="uk">Email</span><span>' + esc(user.email) + '</span></div><div class="user-row"><span class="uk">Status</span><span class="badge">Active</span></div>';
        one("#respLogin").classList.add("show");
        window.alert_("alertLogin", "success", "Login successful");
        setTimeout(function () { window.location.href = "02-dashboard.html"; }, 450);
      } catch (error) {
        window.alert_("alertLogin", "error", errorMessage(error));
      } finally {
        button.disabled = false;
        button.textContent = "Login";
      }
    };

    window.doRegister = async function () {
      const name = one("#rName").value.trim();
      const email = one("#rEmail").value.trim();
      const password = one("#rPass").value;
      const button = one("#paneRegister .btn-primary");
      if (!name || !email || !password) return window.alert_("alertReg", "error", "Please fill in all fields");
      button.disabled = true;
      button.textContent = "Creating...";
      try {
        const user = await CG.register(email, password, name);
        one("#regBody").textContent = JSON.stringify(user, null, 2);
        one("#respReg").classList.add("show");
        one("#lEmail").value = email;
        one("#lPass").value = password;
        window.alert_("alertReg", "success", "Account created. You can log in now.");
      } catch (error) {
        window.alert_("alertReg", "error", errorMessage(error));
      } finally {
        button.disabled = false;
        button.textContent = "Create Account";
      }
    };
  }

  async function initDashboard() {
    const results = await Promise.all([CG.reviews({ page: 0, size: 100 }), CG.documents()]);
    const reviews = results[0].items;
    const docs = results[1];
    const values = all(".stat-val");
    const critical = reviews.reduce(function (sum, item) { return sum + item.critical_count; }, 0);
    const completed = reviews.filter(function (item) { return item.status === "COMPLETED"; });
    const passed = completed.filter(function (item) { return item.quality_gate_status === "PASS"; }).length;
    const passRate = completed.length ? Math.round((passed / completed.length) * 100) : 0;
    if (values[0]) values[0].textContent = results[0].total;
    if (values[1]) values[1].textContent = critical;
    if (values[2]) values[2].textContent = passRate + "%";
    if (values[3]) values[3].textContent = docs.length;
    const deltas = all(".stat-delta");
    const deltaText = ["Stored reviews", "Across current reviews", completed.length + " completed", docs.filter(function (doc) { return doc.status === "READY"; }).length + " ready"];
    deltas.forEach(function (element, index) { element.textContent = deltaText[index] || "Live data"; });

    const dayCounts = Array.from({ length: 7 }, function (_, index) {
      const date = new Date();
      date.setHours(0, 0, 0, 0);
      date.setDate(date.getDate() - (6 - index));
      return { date: date, count: 0 };
    });
    reviews.forEach(function (review) {
      const created = new Date(review.created_at);
      created.setHours(0, 0, 0, 0);
      const day = dayCounts.find(function (item) { return item.date.getTime() === created.getTime(); });
      if (day) day.count += 1;
    });
    const maxDay = Math.max.apply(null, dayCounts.map(function (item) { return item.count; }).concat([1]));
    all(".act-row").forEach(function (row, index) {
      const data = dayCounts[index];
      if (!data) return;
      one(".act-day", row).textContent = data.date.toLocaleDateString(undefined, { weekday: "short" });
      one(".act-bar", row).style.width = Math.round(data.count * 100 / maxDay) + "%";
      one(".act-num", row).textContent = data.count;
    });

    const issueTotal = reviews.reduce(function (sum, item) { return sum + item.issues_count; }, 0);
    const high = reviews.reduce(function (sum, item) { return sum + item.high_count; }, 0);
    const counts = [critical, high, Math.max(0, issueTotal - critical - high), 0, 0];
    const donut = one(".donut-num");
    if (donut) donut.textContent = issueTotal;
    all(".leg-cnt").forEach(function (element, index) { element.textContent = counts[index] || 0; });

    const tbody = one(".table-wrap tbody");
    if (tbody) tbody.innerHTML = reviews.length ? reviews.slice(0, 5).map(function (review) { return reviewRow(review, false); }).join("") : '<tr><td colspan="8" class="empty-note">No reviews yet</td></tr>';
    const updated = one(".page-sub");
    if (updated) updated.textContent = "Live data from /api/v1/reviews - " + new Date().toLocaleTimeString();
  }

  function initSubmit() {
    let selectedType = "GIT_REPO";
    window.selectType = function (type, element) {
      selectedType = type;
      all(".type-btn").forEach(function (button) { button.classList.remove("active"); });
      element.classList.add("active");
      one("#targetGit").style.display = type === "GIT_REPO" ? "block" : "none";
      one("#targetSnippet").style.display = type === "SNIPPET" ? "block" : "none";
      one("#targetPath").style.display = type === "DIRECTORY" || type === "FILE" ? "block" : "none";
    };
    window.doSubmit = async function () {
      const button = one(".page .btn-primary") || one(".main-wrap .btn-primary");
      const mode = (one(".mode-opt.active") && one(".mode-opt.active").textContent.toUpperCase().includes("INCREMENTAL")) ? "INCREMENTAL" : "FULL";
      const activeLanguages = all("#langChips .chip.on").map(function (chip) { return chip.textContent.trim().toLowerCase().replace("c/c++", "cpp"); });
      const payload = { type: selectedType, mode: mode, languages: activeLanguages.length ? activeLanguages : null };
      if (payload.type === "GIT_REPO") {
        payload.target = one("#repoUrl").value.trim();
        payload.branch = one("#targetGit input:not(#repoUrl)").value.trim() || null;
      } else if (payload.type === "SNIPPET") {
        payload.snippet_language = one("#snippetLang").value;
        payload.snippet_content = one("#targetSnippet textarea").value;
      } else {
        payload.target = one("#targetPath input").value.trim();
      }
      const notify = one('input[placeholder^="https://ci"]');
      if (notify && notify.value.trim()) payload.notify_webhook = notify.value.trim();
      if ((payload.type !== "SNIPPET" && !payload.target) || (payload.type === "SNIPPET" && !payload.snippet_content)) {
        return CG.notice("Please provide the review target or snippet", "error");
      }
      button.disabled = true;
      button.textContent = "Submitting...";
      try {
        const review = await CG.submitReview(payload);
        one("#submitBody").textContent = JSON.stringify(review, null, 2);
        one("#submitResp").classList.add("show");
        const tracking = one("#submitResp a");
        if (tracking) tracking.href = detailHref(review.id);
        CG.notice("Review accepted and queued");
      } catch (error) {
        CG.notice(errorMessage(error), "error");
      } finally {
        button.disabled = false;
        button.textContent = "Submit Review";
      }
    };
  }

  let reviewListItems = [];
  async function loadReviewList() {
    const keyword = one("#searchInput").value.trim();
    const status = one("#filterStatus").value;
    const result = await CG.reviews({ page: 0, size: 100, keyword: keyword, status: status });
    reviewListItems = result.items;
    renderReviewList();
  }

  function renderReviewList() {
    const lang = one("#filterLang").value.toLowerCase();
    const gate = one("#filterGate").value;
    const items = reviewListItems.filter(function (review) {
      return (!lang || language(review).toLowerCase().includes(lang)) && (!gate || review.quality_gate_status === gate);
    });
    one("#reviewTable").innerHTML = items.length ? items.map(function (review) { return reviewRow(review, true); }).join("") : '<tr><td colspan="9" class="empty-note">No matching reviews</td></tr>';
    one("#resultCount").innerHTML = "<strong>" + items.length + "</strong> reviews";
  }

  function initReviewList() {
    let timer;
    window.filterTable = function () {
      clearTimeout(timer);
      timer = setTimeout(function () {
        loadReviewList().catch(function (error) { CG.notice(errorMessage(error), "error"); });
      }, 180);
    };
    return loadReviewList();
  }

  function severityClass(severity) {
    return "sev-" + String(severity || "info").toLowerCase();
  }

  function issueMarkup(issue, reviewId) {
    return '<a href="' + detailHref(reviewId, issue.id) + '" style="text-decoration:none"><div class="issue-item" data-severity="' + esc(issue.severity) + '"><div class="ii-top"><span class="sev-badge ' + severityClass(issue.severity) + '">' + esc(issue.severity) + '</span><span class="src-tag">' + esc(issue.source) + '</span><span class="src-tag">' + esc(issue.rule_id || "-") + '</span><span class="cat-tag">' + esc(issue.category || "general") + '</span></div><div class="ii-msg">' + esc(issue.message) + '</div><div class="ii-loc">' + esc(issue.file_path || "Unknown file") + " : Line " + esc(issue.line_start || "-") + '</div><div class="ii-sug">' + esc(issue.suggestion || "No suggestion available") + "</div></div></a>";
  }

  async function initReviewDetail() {
    const review = await selectedReview();
    const breadcrumb = one(".breadcrumb span");
    if (breadcrumb) breadcrumb.textContent = review.id;
    one(".rh-title").textContent = review.target || (review.type + " review");
    one(".rh-meta").innerHTML = "<span>" + esc(review.type + " - " + review.mode + " mode") + "</span><span>branch: " + esc(review.branch || "-") + '</span><span class="mono">' + esc(review.id) + "</span><span>" + esc(CG.formatDate(review.created_at)) + "</span>";
    const status = one(".rh-top > .badge");
    status.className = "badge " + statusClass(review.status);
    status.textContent = review.status;
    all(".stage-icon").forEach(function (icon) {
      icon.className = "stage-icon " + (review.status === "COMPLETED" ? "stage-done" : review.status === "FAILED" ? "stage-error" : "stage-wait");
      icon.textContent = review.status === "COMPLETED" ? "OK" : review.status === "FAILED" ? "!" : "...";
    });
    const stats = all(".ms-val");
    const mediumLow = Math.max(0, review.issues_count - review.critical_count - review.high_count);
    [review.issues_count, review.critical_count, review.high_count, mediumLow, review.quality_gate_status].forEach(function (value, index) {
      if (stats[index]) stats[index].textContent = value;
    });
    const filters = one(".filter-chips");
    const counts = review.issues.reduce(function (acc, issue) { acc[issue.severity] = (acc[issue.severity] || 0) + 1; return acc; }, {});
    filters.innerHTML = ["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"].map(function (severity, index) {
      const count = severity === "ALL" ? review.issues.length : (counts[severity] || 0);
      return '<span class="fchip' + (index === 0 ? " on" : "") + '" onclick="filterSev(\'' + severity + '\',this)">' + severity + " (" + count + ")</span>";
    }).join("");
    const issuesPane = one("#tab-issues");
    all(".issue-item", issuesPane).forEach(function (item) { const link = item.closest("a"); (link || item).remove(); });
    all("#tab-issues > div:not(.filter-chips)").forEach(function (item) { item.remove(); });
    issuesPane.insertAdjacentHTML("beforeend", review.issues.length ? review.issues.map(function (issue) { return issueMarkup(issue, review.id); }).join("") : '<div class="empty-note">No issues available while the review is processing.</div>');
    one("#tab-raw pre").textContent = JSON.stringify(review, null, 2);
    all(".report-btn").forEach(function (link, index) { link.href = "07-report-viewer.html?id=" + encodeURIComponent(review.id) + "&format=" + ["html", "markdown", "pdf"][index]; });
    const issueButton = all(".tab-btn")[0];
    if (issueButton) issueButton.textContent = "Issues (" + review.issues.length + ")";
    window.filterSev = function (severity, element) {
      all(".fchip").forEach(function (chip) { chip.classList.remove("on"); });
      element.classList.add("on");
      all(".issue-item").forEach(function (item) { item.closest("a").style.display = severity === "ALL" || item.dataset.severity === severity ? "" : "none"; });
    };
  }

  async function initIssueViewer() {
    const review = await selectedReview();
    const issueId = new URLSearchParams(window.location.search).get("issue");
    const issue = review.issues.find(function (item) { return item.id === issueId; }) || review.issues[0];
    if (!issue) throw new Error("This review has no issues yet.");
    const crumbs = all(".breadcrumb a");
    if (crumbs[1]) { crumbs[1].textContent = review.id; crumbs[1].href = detailHref(review.id); }
    const crumbIssue = one(".breadcrumb span");
    if (crumbIssue) crumbIssue.textContent = issue.id;
    const sev = one(".sev-block");
    sev.className = "sev-block " + severityClass(issue.severity);
    sev.textContent = issue.severity;
    one(".ih-title").textContent = issue.message;
    one(".ih-meta").innerHTML = '<span class="tag tag-source">Source: ' + esc(issue.source) + '</span><span class="tag tag-source">Rule: ' + esc(issue.rule_id || "-") + '</span><span class="tag tag-cat">Category: ' + esc(issue.category || "general") + "</span>";
    one(".loc-path").textContent = issue.file_path || "Unknown file";
    one(".loc-lines").textContent = "Line " + (issue.line_start || "-") + (issue.line_end ? "-" + issue.line_end : "");
    const codeHeader = one(".code-header span");
    if (codeHeader) codeHeader.textContent = issue.file_path || "Source unavailable";
    const codeBody = one(".code-body");
    if (codeBody) codeBody.innerHTML = '<div class="code-line line-hl"><span class="line-num">' + esc(issue.line_start || "-") + '</span><span class="line-content">' + esc(issue.message) + "</span></div>";
    const suggestion = one(".suggest-text");
    if (suggestion) suggestion.textContent = issue.suggestion || "No automated fix suggestion was generated.";
    const fixCode = one(".fix-code");
    if (fixCode) fixCode.textContent = issue.suggestion || "No patch available.";
    try {
      const related = await CG.searchKnowledge({ q: issue.message, top_k: 3, use_rerank: true });
      const container = one(".section-title", all(".card").find(function (card) { return one(".rag-item", card); }));
      const card = container && container.closest(".card");
      if (card) {
        all(".rag-item", card).forEach(function (item) { item.remove(); });
        card.insertAdjacentHTML("beforeend", related.results.length ? related.results.map(function (item) {
          return '<div class="rag-item"><div class="rag-score">' + Math.round((item.score || 0) * 100) + '%</div><div class="rag-content"><div class="rag-title">Knowledge match</div><div class="rag-excerpt">' + esc(item.content) + '</div><span class="rag-cat">' + esc((item.metadata && item.metadata.category) || "knowledge") + "</span></div></div>";
        }).join("") : '<div class="empty-note">No related knowledge found.</div>');
      }
    } catch (error) {
      CG.notice("Issue loaded; related knowledge is unavailable: " + errorMessage(error), "error");
    }
  }

  async function initReportViewer() {
    const review = await selectedReview();
    one(".page-sub").textContent = "Review " + review.id;
    async function loadFormat(format) {
      try {
        if (format === "html") one("#fmt-html .html-report").innerHTML = await CG.report(review.id, "html", "text");
        if (format === "md" || format === "markdown") one("#fmt-md .md-report").textContent = await CG.report(review.id, "markdown", "text");
      } catch (error) {
        const pane = one(format === "html" ? "#fmt-html .html-report" : "#fmt-md .md-report");
        if (pane) pane.textContent = errorMessage(error);
      }
    }
    window.showFmt = function (format, element) {
      all(".report-pane").forEach(function (pane) { pane.classList.remove("active"); });
      all(".fmt-btn").forEach(function (button) { button.classList.remove("active"); });
      one("#fmt-" + format).classList.add("active");
      element.classList.add("active");
      if (format !== "pdf") loadFormat(format);
    };
    async function download(format) {
      try {
        const blob = await CG.report(review.id, format, "blob");
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = "review-" + review.id + "." + (format === "markdown" ? "md" : format);
        link.click();
        URL.revokeObjectURL(url);
      } catch (error) { CG.notice(errorMessage(error), "error"); }
    }
    const downloadButton = one(".dl-btn");
    if (downloadButton) downloadButton.onclick = function () {
      const active = one(".fmt-btn.active");
      const index = all(".fmt-btn").indexOf(active);
      download(["html", "markdown", "pdf"][index] || "html");
    };
    const pdfButton = one(".btn-pdf");
    if (pdfButton) pdfButton.onclick = function () { download("pdf"); };
    await loadFormat("html");
    const requested = new URLSearchParams(window.location.search).get("format");
    if (requested) {
      const normalized = requested === "markdown" ? "md" : requested;
      const index = ["html", "md", "pdf"].indexOf(normalized);
      if (index >= 0) window.showFmt(normalized, all(".fmt-btn")[index]);
    }
  }

  async function loadDocuments() {
    const documents = await CG.documents();
    const list = one("#docList");
    list.innerHTML = documents.length ? documents.map(function (doc) {
      return '<div class="doc-item"><div class="doc-icon">DOC</div><div class="doc-info"><div class="doc-title">' + esc(doc.title) + '</div><div class="doc-meta">' + esc(doc.category) + " - v" + esc(doc.version) + " - " + esc(doc.chunk_count) + ' chunks</div></div><span class="doc-status ' + (doc.status === "READY" ? "ds-ready" : "ds-proc") + '">' + esc(doc.status) + '</span><button class="del-btn" data-id="' + esc(doc.id) + '" onclick="deleteDoc(this)" title="Delete document">Delete</button></div>';
    }).join("") : '<div class="empty-note">No documents uploaded</div>';
  }

  function initKnowledge() {
    window.doUpload = async function () {
      const file = one("#fileIn").files[0];
      const title = one("#docTitle").value.trim();
      if (!file || !title) return CG.notice("Choose a file and enter a title", "error");
      const form = new FormData();
      form.append("title", title);
      form.append("category", one("#docCat").value);
      form.append("version", one("#docVer").value || "1.0");
      form.append("file", file);
      const progress = one("#uploadProgress");
      progress.classList.add("show");
      one("#progFile").textContent = file.name;
      one("#progPct").textContent = "Uploading...";
      one("#progFill").style.width = "35%";
      try {
        await CG.uploadDocument(form);
        one("#progPct").textContent = "Queued";
        one("#progFill").style.width = "100%";
        await loadDocuments();
        CG.notice("Document uploaded and queued for indexing");
      } catch (error) {
        one("#progPct").textContent = "Failed";
        CG.notice(errorMessage(error), "error");
      }
    };
    window.deleteDoc = async function (button) {
      const id = button.dataset.id;
      if (!id || !window.confirm("Delete this document and its chunks?")) return;
      try { await CG.deleteDocument(id); await loadDocuments(); CG.notice("Document deleted"); }
      catch (error) { CG.notice(errorMessage(error), "error"); }
    };
    window.doSearch = async function () {
      const q = one("#searchQ").value.trim();
      if (!q) return;
      const results = one("#searchResults");
      results.innerHTML = '<div class="results-label">Searching...</div>';
      try {
        const data = await CG.searchKnowledge({ q: q, category: one("#searchCat").value, top_k: 5, use_rerank: one("#rerank").checked });
        results.innerHTML = '<div class="results-label"><span>Found ' + data.total + ' results</span><span class="rag-badge">Live API</span></div>' + data.results.map(function (item) {
          const score = Math.round((item.score || 0) * 100);
          return '<div class="result-item"><div class="ri-top"><div class="score-bar-wrap"><div class="score-bar" style="width:' + score + '%"></div></div><span class="score-txt">' + score + '</span></div><div class="ri-title">Knowledge result</div><div class="ri-excerpt">' + esc(item.content) + '</div><span class="cat-tag">' + esc((item.metadata && item.metadata.category) || "knowledge") + "</span></div>";
        }).join("");
      } catch (error) { results.innerHTML = '<div class="empty-note">' + esc(errorMessage(error)) + "</div>"; }
    };
    return loadDocuments();
  }

  function activeWebhookPlatform() {
    const pane = one(".pane.active");
    return pane ? pane.id.replace("pane-", "") : "github";
  }

  function initWebhook() {
    one("#ghUrl").textContent = window.location.origin + "/api/v1/webhook/github";
    one("#glUrl").textContent = window.location.origin + "/api/v1/webhook/gitlab";
    one("#bbUrl").textContent = window.location.origin + "/api/v1/webhook/bitbucket";
    window.testWebhook = async function () {
      const platform = activeWebhookPlatform();
      const headers = {};
      let payload = {};
      if (platform === "github") headers["X-GitHub-Event"] = "ping";
      if (platform === "gitlab") payload = { object_kind: "tag_push" };
      if (platform === "bitbucket") headers["X-Event-Key"] = "diagnostics:ping";
      try {
        const response = await CG.webhook(platform, payload, headers);
        const log = one("#eventLog");
        const item = document.createElement("div");
        item.className = "log-item";
        item.innerHTML = '<div class="log-status log-ok"></div><div class="log-meta"><div class="log-event">' + esc(platform) + ' test <span class="log-code code-200">200</span></div><div class="log-detail">' + esc(JSON.stringify(response)) + '</div></div><div class="log-time">' + new Date().toLocaleTimeString() + "</div>";
        log.insertBefore(item, log.firstChild);
      } catch (error) { CG.notice(errorMessage(error), "error"); }
    };
  }

  async function initQualityGate() {
    const result = await CG.reviews({ page: 0, size: 100 });
    const reviews = result.items;
    const completed = reviews.filter(function (item) { return item.status === "COMPLETED"; });
    const passed = completed.filter(function (item) { return item.quality_gate_status === "PASS"; });
    const failed = completed.filter(function (item) { return item.quality_gate_status === "FAIL"; });
    const statValues = all(".stat-v");
    if (statValues[0]) statValues[0].textContent = (completed.length ? Math.round(passed.length * 100 / completed.length) : 0) + "%";
    if (statValues[1]) statValues[1].textContent = failed.length;
    if (statValues[2]) statValues[2].textContent = reviews.length;
    if (statValues[3]) statValues[3].textContent = "Live";
    const latest = reviews[0];
    if (latest) {
      const title = all(".card-title").find(function (element) { return element.textContent.includes("Latest Review"); });
      if (title) title.textContent = "Latest Review - " + CG.shortTarget(latest);
      one(".gate-icon").textContent = latest.quality_gate_status === "PASS" ? "PASS" : latest.quality_gate_status === "FAIL" ? "FAIL" : "WAIT";
      const gateStatus = one(".gate-status");
      gateStatus.textContent = latest.quality_gate_status;
      gateStatus.className = "gate-status " + (latest.quality_gate_status === "PASS" ? "gate-pass" : "gate-fail");
      one(".gate-rate").textContent = latest.status + " - " + latest.issues_count + " issues";
    }
    const gateDays = Array.from({ length: 7 }, function (_, index) {
      const date = new Date();
      date.setHours(0, 0, 0, 0);
      date.setDate(date.getDate() - (6 - index));
      return { date: date, pass: 0, fail: 0 };
    });
    completed.forEach(function (review) {
      const created = new Date(review.created_at);
      created.setHours(0, 0, 0, 0);
      const day = gateDays.find(function (item) { return item.date.getTime() === created.getTime(); });
      if (day && review.quality_gate_status === "PASS") day.pass += 1;
      if (day && review.quality_gate_status === "FAIL") day.fail += 1;
    });
    const maxGate = Math.max.apply(null, gateDays.map(function (item) { return item.pass + item.fail; }).concat([1]));
    all(".trend-col").forEach(function (column, index) {
      const data = gateDays[index];
      if (!data) return;
      const bars = all(".trend-bar", column);
      if (bars[0]) bars[0].style.height = Math.round(data.pass * 80 / maxGate) + "px";
      if (bars[1]) bars[1].style.height = Math.round(data.fail * 80 / maxGate) + "px";
      const label = one(".trend-lbl", column);
      if (label) label.textContent = data.date.toLocaleDateString(undefined, { weekday: "short" });
    });
    const table = all("table tbody").pop();
    if (table) table.innerHTML = reviews.length ? reviews.map(function (review) {
      return "<tr><td><span class=\"mono\">" + esc(CG.shortTarget(review)) + "</span></td><td>" + esc(language(review)) + '</td><td><span class="sev-c">' + esc(review.critical_count) + '</span></td><td><span class="sev-h">' + esc(review.high_count) + '</span></td><td><span class="badge">' + esc(review.quality_gate_status) + '</span></td><td><a href="' + detailHref(review.id) + '" class="link">Detail</a></td></tr>';
    }).join("") : '<tr><td colspan="6" class="empty-note">No reviews yet</td></tr>';
    const save = all("button").find(function (button) { return button.textContent.includes("Save Config"); });
    if (save) save.onclick = function () {
      localStorage.setItem("codeguardian_quality_thresholds", JSON.stringify(all(".thresh-input").map(function (input) { return Number(input.value); })));
      CG.notice("Threshold draft saved in this browser. Server thresholds are configured through environment variables.");
    };
    const saved = JSON.parse(localStorage.getItem("codeguardian_quality_thresholds") || "null");
    if (saved) all(".thresh-input").forEach(function (input, index) { if (saved[index] != null) input.value = saved[index]; });
  }

  async function init() {
    if (page === "01-login.html") {
      initLogin();
      if (CG.token()) window.location.replace("02-dashboard.html");
      return;
    }
    if (protectedPages.has(page)) {
      if (!CG.token()) {
        window.location.replace("01-login.html");
        return;
      }
      await loadCurrentUser();
    }
    if (page === "02-dashboard.html") await initDashboard();
    if (page === "03-submit-review.html") initSubmit();
    if (page === "04-review-list.html") await initReviewList();
    if (page === "05-review-detail.html") await initReviewDetail();
    if (page === "06-issue-viewer.html") await initIssueViewer();
    if (page === "07-report-viewer.html") await initReportViewer();
    if (page === "08-knowledge-base.html") await initKnowledge();
    if (page === "09-webhook-setup.html") initWebhook();
    if (page === "10-quality-gate.html") await initQualityGate();
  }

  init().catch(function (error) {
    CG.notice(errorMessage(error), "error");
    const main = one(".main-wrap .page") || one(".main-wrap .content");
    if (main && !one(".cg-load-error", main)) {
      const message = document.createElement("div");
      message.className = "cg-load-error";
      message.style.cssText = "margin:16px;padding:14px;border:1px solid #ef4444;border-radius:8px;color:#fecaca;background:rgba(127,29,29,.35)";
      message.textContent = errorMessage(error);
      main.prepend(message);
    }
  });
})();
