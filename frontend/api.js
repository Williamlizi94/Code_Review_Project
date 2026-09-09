(function () {
  "use strict";

  const TOKEN_KEY = "codeguardian_access_token";
  const USER_KEY = "codeguardian_user";

  class ApiError extends Error {
    constructor(message, status, payload) {
      super(message);
      this.name = "ApiError";
      this.status = status;
      this.payload = payload;
    }
  }

  function token() {
    return localStorage.getItem(TOKEN_KEY) || "";
  }

  function setSession(accessToken, user) {
    localStorage.setItem(TOKEN_KEY, accessToken);
    if (user) localStorage.setItem(USER_KEY, JSON.stringify(user));
  }

  function clearSession() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }

  function cachedUser() {
    try {
      return JSON.parse(localStorage.getItem(USER_KEY) || "null");
    } catch (_) {
      return null;
    }
  }

  async function request(path, options) {
    const opts = options || {};
    const headers = new Headers(opts.headers || {});
    const accessToken = token();
    if (opts.auth !== false && accessToken) {
      headers.set("Authorization", "Bearer " + accessToken);
    }

    let body = opts.body;
    if (body != null && !(body instanceof FormData) && typeof body !== "string") {
      headers.set("Content-Type", "application/json");
      body = JSON.stringify(body);
    }

    const response = await fetch(path, {
      method: opts.method || "GET",
      headers: headers,
      body: body,
    });

    if (!response.ok) {
      let payload = null;
      try {
        payload = await response.json();
      } catch (_) {
        payload = await response.text();
      }
      const detail = payload && payload.detail;
      const message = Array.isArray(detail)
        ? detail.map(function (item) { return item.msg; }).join("; ")
        : detail || (typeof payload === "string" && payload) || response.statusText;
      if (response.status === 401 && opts.auth !== false) clearSession();
      throw new ApiError(message || "Request failed", response.status, payload);
    }

    if (opts.response === "response") return response;
    if (opts.response === "text") return response.text();
    if (opts.response === "blob") return response.blob();
    if (response.status === 204) return null;
    return response.json();
  }

  function query(path, params) {
    const url = new URL(path, window.location.origin);
    Object.keys(params || {}).forEach(function (key) {
      const value = params[key];
      if (value !== "" && value !== null && value !== undefined) {
        url.searchParams.set(key, value);
      }
    });
    return url.pathname + url.search;
  }

  function escapeHtml(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function formatDate(value) {
    if (!value) return "-";
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
  }

  function shortTarget(review) {
    if (review.target) return review.target.replace(/^https?:\/\//, "").replace(/\.git$/, "");
    return review.type === "SNIPPET" ? "Code snippet" : review.type;
  }

  function notice(message, type) {
    let element = document.getElementById("cgNotice");
    if (!element) {
      element = document.createElement("div");
      element.id = "cgNotice";
      element.style.cssText = "position:fixed;right:20px;bottom:20px;z-index:9999;max-width:420px;padding:12px 16px;border-radius:8px;font:13px/1.4 -apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;box-shadow:0 12px 30px rgba(0,0,0,.35);transition:opacity .2s";
      document.body.appendChild(element);
    }
    const failed = type === "error";
    element.style.background = failed ? "#7f1d1d" : "#064e3b";
    element.style.color = "#fff";
    element.textContent = message;
    element.style.opacity = "1";
    clearTimeout(element._timer);
    element._timer = setTimeout(function () { element.style.opacity = "0"; }, 3500);
  }

  const api = {
    ApiError: ApiError,
    token: token,
    cachedUser: cachedUser,
    setSession: setSession,
    clearSession: clearSession,
    request: request,
    query: query,
    escape: escapeHtml,
    formatDate: formatDate,
    shortTarget: shortTarget,
    notice: notice,
    login: function (email, password) {
      return request("/api/v1/auth/login", { method: "POST", body: { email: email, password: password }, auth: false });
    },
    register: function (email, password, fullName) {
      return request("/api/v1/auth/register", { method: "POST", body: { email: email, password: password, full_name: fullName }, auth: false });
    },
    me: function () { return request("/api/v1/auth/me"); },
    reviews: function (params) { return request(query("/api/v1/reviews", params)); },
    review: function (id) { return request("/api/v1/reviews/" + encodeURIComponent(id)); },
    submitReview: function (payload) { return request("/api/v1/reviews", { method: "POST", body: payload }); },
    report: function (id, format, responseType) {
      return request(query("/api/v1/reviews/" + encodeURIComponent(id) + "/report", { format: format }), { response: responseType || "text" });
    },
    documents: function (category) { return request(query("/api/v1/knowledge/documents", { category: category })); },
    uploadDocument: function (formData) { return request("/api/v1/knowledge/upload", { method: "POST", body: formData }); },
    deleteDocument: function (id) { return request("/api/v1/knowledge/documents/" + encodeURIComponent(id), { method: "DELETE" }); },
    searchKnowledge: function (params) { return request(query("/api/v1/knowledge/search", params)); },
    webhook: function (platform, payload, headers) {
      return request("/api/v1/webhook/" + platform, { method: "POST", body: payload, headers: headers, auth: false });
    },
  };

  window.CodeGuardian = api;
})();
