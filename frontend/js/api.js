const SS = {
  apiBase: `${location.origin}/api/v1`,

  token() {
    return localStorage.getItem("ss_token");
  },
  user() {
    return JSON.parse(localStorage.getItem("ss_user") || "null");
  },
  isAuthed() {
    return !!SS.token();
  },

  setSession(token, user) {
    localStorage.setItem("ss_token", token);
    if (user) localStorage.setItem("ss_user", JSON.stringify(user));
  },
  clearSession() {
    localStorage.removeItem("ss_token");
    localStorage.removeItem("ss_user");
  },
  logout() {
    SS.clearSession();
    location.href = "/login.html";
  },

  async api(path, opts = {}) {
    const headers = new Headers(opts.headers || {});
    const token = SS.token();
    if (token) headers.set("Authorization", `Bearer ${token}`);
    if (opts.body && !headers.has("Content-Type") && !(opts.body instanceof FormData)) {
      headers.set("Content-Type", "application/json");
    }
    const res = await fetch(`${SS.apiBase}${path}`, { ...opts, headers });
    if (res.status === 401) {
      SS.clearSession();
      const here = location.pathname.split("/").pop();
      if (here !== "login.html" && here !== "register.html" && here !== "index.html" && here !== "") {
        location.href = "/login.html";
      }
      throw new Error("Unauthorized");
    }
    return res;
  },

  async login(email, password) {
    const res = await SS.api("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
    if (!res.ok) throw new Error((await res.json()).detail || "Invalid credentials");
    const data = await res.json();
    SS.setSession(data.access_token, null);
    return data;
  },

  async register(username, email, password) {
    const res = await SS.api("/auth/register", {
      method: "POST",
      body: JSON.stringify({ username, email, password }),
    });
    if (!res.ok) throw new Error((await res.json()).detail || "Registration failed");
    const data = await res.json();
    SS.setSession(data.access_token, null);
    return data;
  },

  async me() {
    const res = await SS.api("/auth/me");
    if (!res.ok) throw new Error("Failed to load profile");
    const user = await res.json();
    localStorage.setItem("ss_user", JSON.stringify(user));
    return user;
  },

  async listReceipts(params = {}) {
    const qs = new URLSearchParams();
    if (params.start_date) qs.set("start_date", params.start_date);
    if (params.end_date) qs.set("end_date", params.end_date);
    const suffix = qs.toString() ? `?${qs}` : "";
    const res = await SS.api(`/receipts${suffix}`);
    if (!res.ok) throw new Error("Failed to load receipts");
    return res.json();
  },

  async getDashboard(period_type = "monthly") {
    const res = await SS.api(`/analytics/dashboard?period_type=${period_type}`);
    if (!res.ok) throw new Error("Failed to load dashboard");
    return res.json();
  },

  async uploadReceipt(files) {
    const form = new FormData();
    for (const f of files) form.append("files", f, f.name);
    const res = await SS.api("/receipts", { method: "POST", body: form });
    if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || "Upload failed");
    return res.json();
  },

  async getReceipt(id) {
    const res = await SS.api(`/receipts/${id}`);
    if (!res.ok) throw new Error("Failed to load receipt");
    return res.json();
  },

  async updateReceipt(id, payload) {
    const res = await SS.api(`/receipts/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || "Save failed");
    return res.json();
  },

  async deleteReceipt(id) {
    const res = await SS.api(`/receipts/${id}`, { method: "DELETE" });
    if (!res.ok && res.status !== 204) throw new Error("Delete failed");
  },

  guard() {
    if (!SS.isAuthed()) location.href = "/login.html";
  },

  guestOnly() {
    if (SS.isAuthed()) location.href = "/";
  },

  async paintNav(active) {
    const root = document.getElementById("topnav");
    if (!root) return;
    const isAuthed = SS.isAuthed();
    let user = SS.user();
    if (isAuthed && !user) {
      try {
        user = await SS.me();
      } catch {
        user = null;
      }
    }
    const link = (key, href, icon, label) => `
      <a href="${href}" class="topnav__link${active === key ? " is-active" : ""}">
        <i data-lucide="${icon}"></i><span>${label}</span>
      </a>`;
    const coinsHtml =
      isAuthed && user
        ? `
      <div class="topnav__user">
        <span class="topnav__username">${user.username || ""}</span>
        <button type="button" class="btn btn--ghost btn--sm" id="ss-logout">
          <i data-lucide="log-out"></i><span>Sign out</span>
        </button>
      </div>`
        : `
      <div class="topnav__user">
        <a href="/login.html" class="topnav__link"><i data-lucide="log-in"></i><span>Sign in</span></a>
        <a href="/register.html" class="topnav__cta"><i data-lucide="user-plus"></i><span>Sign up</span></a>
      </div>`;
    root.innerHTML = `
      <div class="topnav__inner">
        <a href="/" class="topnav__brand">
          <img class="icon" src="/assets/icon.png" alt="">
          <img class="wordmark" src="/assets/logo.png" alt="SpendScan">
        </a>
        <div class="topnav__links">
          ${link("scan", "/", "receipt-text", "Scan")}
          ${link("stats", "/statistics.html", "bar-chart-3", "Statistics")}
          ${link("cal", "/calendar.html", "calendar-days", "Calendar")}
          ${link("about", "/about.html", "info", "About")}
          <span class="topnav__divider"></span>
          ${coinsHtml}
        </div>
      </div>`;
    document.getElementById("ss-logout")?.addEventListener("click", () => SS.logout());
    if (window.ssIcons) window.ssIcons();
  },
};

window.SS = SS;
