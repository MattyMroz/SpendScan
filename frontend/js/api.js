const SS = {
  apiBase: `${location.origin}/api/v1`,
  currentLanguage: localStorage.getItem("ss_language") || "PL",

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

  setLanguage(lang) {
    if (!["PL", "EN"].includes(lang)) return;
    SS.currentLanguage = lang;
    localStorage.setItem("ss_language", lang);
    document.documentElement.lang = lang === "PL" ? "pl" : "en";
    // Dispatch event so pages can listen and update content
    window.dispatchEvent(new CustomEvent("languageChange", { detail: { language: lang } }));
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

  async listFolders() {
    const res = await SS.api("/folders");
    if (!res.ok) throw new Error("Failed to load folders");
    return res.json();
  },

  async createFolder(name) {
    const res = await SS.api("/folders", {
      method: "POST",
      body: JSON.stringify({ name }),
    });

    if (!res.ok) throw new Error("Failed to create folder");
    return res.json();
  },

  async addReceiptToFolder(folderId, receiptId) {
    const res = await SS.api(`/folders/${folderId}/receipts/${receiptId}`, {
      method: "POST",
    });

    if (!res.ok) throw new Error("Failed to assign receipt");
  },

  async removeReceiptFromFolder(
    folderId,
    receiptId
  ) {
    const res = await SS.api(
      `/folders/${folderId}/receipts/${receiptId}`,
      {
        method: "DELETE",
      }
    );

    if (!res.ok) {
      throw new Error(
        "Failed to remove folder"
      );
    }

    return true;
  },

  async deleteFolder(folderId) {
    const res = await SS.api(
      `/folders/${folderId}`,
      {
        method: "DELETE",
      }
    );

    if (!res.ok) {
      throw new Error(
        "Failed to delete folder"
      );
    }

    return true;
  },

  async updateFolder(folderId, description) {
    const res = await SS.api(
      `/folders/${folderId}`,
      {
        method: "PATCH",
        body: JSON.stringify({ description }),
      }
    );

    if (!res.ok) {
      throw new Error("Failed to update folder");
    }

    return res.json();
  },

  guard() {
    if (!SS.isAuthed()) location.href = "/login.html";
  },

  guestOnly() {
    if (SS.isAuthed()) location.href = "/";
  },

  // Navbar translations
  navTranslations() {
    return {
      PL: {
        scan: "Skanuj",
        statistics: "Statystyki",
        calendar: "Kalendarz",
        about: "O nas",
        sign_in: "Zaloguj się",
        sign_up: "Załóż konto",
        sign_out: "Wyloguj się",
        back_to_home: "Powrót do domu",
      },
      EN: {
        scan: "Scan",
        statistics: "Statistics",
        calendar: "Calendar",
        about: "About",
        sign_in: "Sign in",
        sign_up: "Sign up",
        sign_out: "Sign out",
        back_to_home: "Back to home",
      },
    };
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

    const navT = SS.navTranslations()[SS.currentLanguage];

    const link = (key, href, icon, label) => `
      <a href="${href}" class="topnav__link${active === key ? " is-active" : ""}" data-nav-key="${key}">
        <i data-lucide="${icon}"></i><span>${label}</span>
      </a>`;

    const languageSwitcher = `
      <div style="display: flex; gap: 4px; align-items: center; flex-shrink: 0;">
        <button type="button" class="topnav__lang-btn" data-lang="PL" style="
          padding: 6px 12px;
          border: 1px solid ${SS.currentLanguage === "PL" ? "#078896" : "#ccc"};
          background: ${SS.currentLanguage === "PL" ? "#078896" : "transparent"};
          color: ${SS.currentLanguage === "PL" ? "white" : "#078896"};
          border-radius: 4px;
          font-weight: 600;
          font-size: 13px;
          cursor: pointer;
          transition: all 0.2s ease;
          min-width: 44px;
        ">PL</button>
        <button type="button" class="topnav__lang-btn" data-lang="EN" style="
          padding: 6px 12px;
          border: 1px solid ${SS.currentLanguage === "EN" ? "#078896" : "#ccc"};
          background: ${SS.currentLanguage === "EN" ? "#078896" : "transparent"};
          color: ${SS.currentLanguage === "EN" ? "white" : "#078896"};
          border-radius: 4px;
          font-weight: 600;
          font-size: 13px;
          cursor: pointer;
          transition: all 0.2s ease;
          min-width: 44px;
        ">EN</button>
      </div>`;

    const themeSwitcher = `
      <button
        type="button"
        id="theme-toggle"
        class="theme-toggle"
      >
        <i data-lucide="moon"></i>
      </button>
    `;

    const coinsHtml =
      isAuthed && user
        ? `
      <div class="topnav__user">
        <span class="topnav__username">${user.username || ""}</span>
        <button type="button" class="btn btn--ghost btn--sm" id="ss-logout">
          <i data-lucide="log-out"></i><span>${navT.sign_out}</span>
        </button>
      </div>`
        : `
      <div class="topnav__user">
        <a href="/login.html" class="topnav__link"><i data-lucide="log-in"></i><span>${navT.sign_in}</span></a>
        <a href="/register.html" class="topnav__cta"><i data-lucide="user-plus"></i><span>${navT.sign_up}</span></a>
      </div>`;

    root.innerHTML = `
      <div class="topnav__inner">
        <a href="/" class="topnav__brand">
          <img class="icon" src="/assets/icon.png" alt="">
          <img class="wordmark" src="/assets/logo.png" alt="SpendScan">
        </a>
        <div class="topnav__links">
          ${link("scan", "/", "receipt-text", navT.scan)}
          ${link("stats", "/statistics.html", "bar-chart-3", navT.statistics)}
          ${link("cal", "/calendar.html", "calendar-days", navT.calendar)}
          ${link("about", "/about.html", "info", navT.about)}
          <span class="topnav__divider"></span>
          ${coinsHtml}
        </div>
        ${themeSwitcher}
        ${languageSwitcher}
      </div>`;

    // Add language button event listeners
    document.querySelectorAll(".topnav__lang-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        const lang = btn.dataset.lang;
        SS.setLanguage(lang);
        SS.paintNav(active); // Refresh nav to update button states
      });
    });

    const themeBtn = document.getElementById("theme-toggle");

    if (themeBtn) {
      const dark = document.body.classList.contains("dark");

      themeBtn.innerHTML = dark
        ? '<i data-lucide="sun"></i>'
        : '<i data-lucide="moon"></i>';

      if (window.ssIcons) window.ssIcons();

      themeBtn.addEventListener("click", () => {
        document.body.classList.toggle("dark");

        const isDark = document.body.classList.contains("dark");

        localStorage.setItem("ss_theme", isDark ? "dark" : "light");

        themeBtn.innerHTML = isDark
          ? '<i data-lucide="sun"></i>'
          : '<i data-lucide="moon"></i>';

        if (window.ssIcons) window.ssIcons();
      });
    }

    document.getElementById("ss-logout")?.addEventListener("click", () => SS.logout());
    if (window.ssIcons) window.ssIcons();
  },
};

const savedTheme = localStorage.getItem("ss_theme");

if (savedTheme === "dark") {
  document.body.classList.add("dark");
}

window.SS = SS;
