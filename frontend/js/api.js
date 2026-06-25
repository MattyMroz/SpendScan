/**
 * @file api.js
 * @description SpendScan frontend API layer. Exposes a global `SS` namespace
 * that wraps all REST calls to the backend, manages session state via HttpOnly
 * cookies, handles CSRF protection, and provides navigation and UI helpers.
 */

// One-time cleanup for sessions created by older localStorage-based versions.
localStorage.removeItem("ss_token");
localStorage.removeItem("ss_user");

/**
 * @namespace SS
 * @description Global SpendScan namespace. Contains all API wrappers, session
 * helpers, auth guards, folder/receipt management, analytics, and navigation
 * rendering. Attach to `window.SS` at the bottom of this file so every page
 * can access it as a plain script dependency (no module bundler required).
 */
const SS = {
  /** @type {string} Base URL for all API requests, derived from the current origin. */
  apiBase: `${location.origin}/api/v1`,

  /** @type {string} Currently active UI language ("PL" or "EN"), persisted in localStorage. */
  currentLanguage: localStorage.getItem("ss_language") || "PL",

  /** @type {Object|null} The authenticated user object returned by the server, or null when logged out. */
  currentUser: null,

  /**
   * @type {boolean|null}
   * Authentication state: `true` when logged in, `false` when explicitly
   * logged out, `null` when not yet determined (initial page load).
   */
  authenticated: null,

  /**
   * Return the currently authenticated user object.
   * @returns {Object|null} The user object, or null if not authenticated.
   */
  user() {
    return SS.currentUser;
  },

  /**
   * Check whether the current session is authenticated.
   * @returns {boolean} `true` only when `authenticated` is strictly `true`.
   */
  isAuthed() {
    return SS.authenticated === true;
  },

  /**
   * Persist an authenticated user in memory and clear any stale localStorage
   * tokens left over from older app versions.
   * @param {Object|null} user - The user object returned by the server after login or registration.
   * @returns {void}
   */
  setSession(user) {
    localStorage.removeItem("ss_token");
    localStorage.removeItem("ss_user");
    SS.currentUser = user || null;
    SS.authenticated = true;
  },

  /**
   * Destroy the in-memory session and remove stale localStorage artefacts.
   * Call this on logout or when the server returns 401.
   * @returns {void}
   */
  clearSession() {
    localStorage.removeItem("ss_token");
    localStorage.removeItem("ss_user");
    SS.currentUser = null;
    SS.authenticated = false;
  },

  /**
   * Read the CSRF token from the `ss_csrf_token` cookie set by the server.
   * The token is sent as the `X-CSRF-Token` header on every mutating request
   * so the backend can reject cross-site forgery attempts.
   * @returns {string|null} The decoded CSRF token, or null if the cookie is absent.
   */
  csrfToken() {
    const prefix = "ss_csrf_token=";
    const cookie = document.cookie
      .split("; ")
      .find((entry) => entry.startsWith(prefix));
    return cookie ? decodeURIComponent(cookie.slice(prefix.length)) : null;
  },

  /**
   * Log the current user out on the server and redirect to the login page.
   * Errors are silently swallowed because an already-expired session still
   * counts as logged out from the browser's perspective.
   * @returns {Promise<void>}
   */
  async logout() {
    try {
      await SS.api("/auth/logout", { method: "POST", redirectOnUnauthorized: false });
    } catch {
      // An already expired session is still logged out from the browser's perspective.
    } finally {
      SS.clearSession();
      location.href = "/login.html";
    }
  },

  /**
   * Switch the active UI language and notify all listeners.
   * Persists the choice to localStorage and updates the `<html lang>` attribute
   * so screen readers announce the correct language immediately.
   * @param {"PL"|"EN"} lang - The language code to activate.
   * @returns {void}
   */
  setLanguage(lang) {
    if (!["PL", "EN"].includes(lang)) return;
    SS.currentLanguage = lang;
    localStorage.setItem("ss_language", lang);
    document.documentElement.lang = lang === "PL" ? "pl" : "en";
    // Dispatch event so pages can listen and update content
    window.dispatchEvent(new CustomEvent("languageChange", { detail: { language: lang } }));
  },

  /**
   * Low-level fetch wrapper used by every public API method.
   * Automatically attaches the CSRF token for mutating methods, sets
   * `Content-Type: application/json` when the body is not FormData, and
   * redirects to `/login.html` on 401 responses (unless suppressed).
   * @param {string} path - API path relative to `SS.apiBase` (e.g. `"/auth/login"`).
   * @param {Object} [opts={}] - Options forwarded to `fetch`, plus an extra
   *   `{boolean} redirectOnUnauthorized` flag (default `true`).
   * @returns {Promise<Response>} The raw fetch `Response` object.
   * @throws {Error} Throws `"Unauthorized"` when the server returns 401.
   */
  async api(path, opts = {}) {
    const { redirectOnUnauthorized = true, ...fetchOpts } = opts;
    const headers = new Headers(fetchOpts.headers || {});
    const method = (fetchOpts.method || "GET").toUpperCase();
    if (!["GET", "HEAD", "OPTIONS", "TRACE"].includes(method)) {
      const csrfToken = SS.csrfToken();
      if (csrfToken) headers.set("X-CSRF-Token", csrfToken);
    }
    if (fetchOpts.body && !headers.has("Content-Type") && !(fetchOpts.body instanceof FormData)) {
      headers.set("Content-Type", "application/json");
    }
    const res = await fetch(`${SS.apiBase}${path}`, {
      credentials: "same-origin",
      ...fetchOpts,
      headers,
    });
    if (res.status === 401) {
      SS.clearSession();
      const here = location.pathname.split("/").pop();
      if (
        redirectOnUnauthorized &&
        here !== "login.html" &&
        here !== "register.html" &&
        here !== "index.html" &&
        here !== ""
      ) {
        location.href = "/login.html";
      }
      throw new Error("Unauthorized");
    }
    return res;
  },

  /**
   * Log the user in with email and password credentials.
   * Stores the returned user in the in-memory session on success.
   * @param {string} email - The user's email address.
   * @param {string} password - The user's plain-text password.
   * @returns {Promise<Object>} The server response body containing `user` and session metadata.
   * @throws {Error} Throws with the server's error detail when credentials are invalid.
   */
  async login(email, password) {
    const res = await SS.api("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
    if (!res.ok) throw new Error((await res.json()).detail || "Invalid credentials");
    const data = await res.json();
    SS.setSession(data.user);
    return data;
  },

  /**
   * Register a new user account and immediately start a session.
   * @param {string} username - The desired display name.
   * @param {string} email - The user's email address.
   * @param {string} password - The chosen plain-text password.
   * @returns {Promise<Object>} The server response body containing the newly created `user`.
   * @throws {Error} Throws with the server's error detail when registration fails.
   */
  async register(username, email, password) {
    const res = await SS.api("/auth/register", {
      method: "POST",
      body: JSON.stringify({ username, email, password }),
    });
    if (!res.ok) throw new Error((await res.json()).detail || "Registration failed");
    const data = await res.json();
    SS.setSession(data.user);
    return data;
  },

  /**
   * Fetch the currently authenticated user's profile from the server.
   * Updates the in-memory session so subsequent calls to `SS.user()` return
   * fresh data without a full page reload.
   * @returns {Promise<Object>} The user object from the server.
   * @throws {Error} Throws when the session cookie is absent or expired.
   */
  async me() {
    const res = await SS.api("/auth/me", { redirectOnUnauthorized: false });
    if (!res.ok) throw new Error("Failed to load profile");
    const user = await res.json();
    SS.setSession(user);
    return user;
  },

  /**
   * Resolve authentication state, refreshing it from the server if not yet known.
   * Prefer this over `SS.isAuthed()` on page load because the cookie-based
   * session is invisible to JavaScript and must be validated server-side.
   * @returns {Promise<boolean>} `true` if the user is authenticated, `false` otherwise.
   */
  async ensureAuth() {
    if (SS.isAuthed()) return true;
    try {
      await SS.me();
      return true;
    } catch {
      return false;
    }
  },

  /**
   * Fetch the list of receipts, optionally filtered by date range.
   * @param {Object} [params={}] - Optional filter parameters.
   * @param {string} [params.start_date] - ISO date string for the start of the range (e.g. `"2024-01-01"`).
   * @param {string} [params.end_date] - ISO date string for the end of the range (e.g. `"2024-12-31"`).
   * @returns {Promise<Array<Object>>} Array of receipt objects.
   * @throws {Error} Throws when the request fails.
   */
  async listReceipts(params = {}) {
    const qs = new URLSearchParams();
    if (params.start_date) qs.set("start_date", params.start_date);
    if (params.end_date) qs.set("end_date", params.end_date);
    const suffix = qs.toString() ? `?${qs}` : "";
    const res = await SS.api(`/receipts${suffix}`);
    if (!res.ok) throw new Error("Failed to load receipts");
    return res.json();
  },

  /**
   * Fetch aggregated analytics data for the dashboard.
   * @param {"monthly"|"weekly"|"yearly"} [period_type="monthly"] - The aggregation period.
   * @returns {Promise<Object>} Dashboard analytics payload from the server.
   * @throws {Error} Throws when the request fails.
   */
  async getDashboard(period_type = "monthly") {
    const res = await SS.api(`/analytics/dashboard?period_type=${period_type}`);
    if (!res.ok) throw new Error("Failed to load dashboard");
    return res.json();
  },

  /**
   * Upload one or more receipt image files for OCR processing.
   * Uses a multipart `FormData` body so the server can receive binary files
   * without base64 encoding overhead.
   * @param {FileList|Array<File>} files - The image files to upload.
   * @returns {Promise<Object>} The server response body describing the created receipts.
   * @throws {Error} Throws with the server's error detail when the upload fails.
   */
  async uploadReceipt(files) {
    const form = new FormData();
    for (const f of files) form.append("files", f, f.name);
    const res = await SS.api("/receipts", { method: "POST", body: form });
    if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || "Upload failed");
    return res.json();
  },

  /**
   * Fetch a single receipt by its unique identifier.
   * @param {string|number} id - The receipt ID.
   * @returns {Promise<Object>} The receipt object.
   * @throws {Error} Throws when the receipt is not found or the request fails.
   */
  async getReceipt(id) {
    const res = await SS.api(`/receipts/${id}`);
    if (!res.ok) throw new Error("Failed to load receipt");
    return res.json();
  },

  /**
   * Partially update a receipt with the provided fields.
   * Sends a PATCH request so only the supplied keys are changed server-side.
   * @param {string|number} id - The receipt ID to update.
   * @param {Object} payload - Key/value pairs of fields to update (e.g. `{ store_name: "Lidl" }`).
   * @returns {Promise<Object>} The updated receipt object returned by the server.
   * @throws {Error} Throws with the server's error detail when the save fails.
   */
  async updateReceipt(id, payload) {
    const res = await SS.api(`/receipts/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || "Save failed");
    return res.json();
  },

  /**
   * Permanently delete a receipt.
   * Treats a 204 No Content response as success because some server versions
   * return 204 instead of 200 on deletion.
   * @param {string|number} id - The receipt ID to delete.
   * @returns {Promise<void>}
   * @throws {Error} Throws when deletion fails and the response is not 204.
   */
  async deleteReceipt(id) {
    const res = await SS.api(`/receipts/${id}`, { method: "DELETE" });
    if (!res.ok && res.status !== 204) throw new Error("Delete failed");
  },

  /**
   * Fetch all folders belonging to the current user.
   * @returns {Promise<Array<Object>>} Array of folder objects.
   * @throws {Error} Throws when the request fails.
   */
  async listFolders() {
    const res = await SS.api("/folders");
    if (!res.ok) throw new Error("Failed to load folders");
    return res.json();
  },

  /**
   * Create a new folder with the given name.
   * @param {string} name - The display name for the new folder.
   * @returns {Promise<Object>} The newly created folder object.
   * @throws {Error} Throws when the folder cannot be created.
   */
  async createFolder(name) {
    const res = await SS.api("/folders", {
      method: "POST",
      body: JSON.stringify({ name }),
    });

    if (!res.ok) throw new Error("Failed to create folder");
    return res.json();
  },

  /**
   * Add a receipt to a folder by creating the many-to-many association.
   * @param {string|number} folderId - The folder ID to add the receipt to.
   * @param {string|number} receiptId - The receipt ID to assign.
   * @returns {Promise<void>}
   * @throws {Error} Throws when the association cannot be created.
   */
  async addReceiptToFolder(folderId, receiptId) {
    const res = await SS.api(`/folders/${folderId}/receipts/${receiptId}`, {
      method: "POST",
    });

    if (!res.ok) throw new Error("Failed to assign receipt");
  },

  /**
   * Remove a receipt from a folder without deleting the receipt itself.
   * @param {string|number} folderId - The folder ID.
   * @param {string|number} receiptId - The receipt ID to disassociate.
   * @returns {Promise<boolean>} `true` when the removal succeeds.
   * @throws {Error} Throws when the removal fails.
   */
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

  /**
   * Permanently delete a folder and all its associations.
   * Receipts inside the folder are NOT deleted — only the folder itself is removed.
   * @param {string|number} folderId - The folder ID to delete.
   * @returns {Promise<boolean>} `true` when the deletion succeeds.
   * @throws {Error} Throws when the deletion fails.
   */
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

  /**
   * Update a folder's description.
   * @param {string|number} folderId - The folder ID to update.
   * @param {string} description - The new description text.
   * @returns {Promise<Object>} The updated folder object returned by the server.
   * @throws {Error} Throws when the update fails.
   */
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

  /**
   * Guard a page so only authenticated users can view it.
   * Redirects unauthenticated visitors to `/login.html`. Call this at the
   * top of every protected page's script.
   * @returns {Promise<boolean>} `true` if authenticated (page may proceed), `false` after redirect.
   */
  async guard() {
    const authenticated = await SS.ensureAuth();
    if (!authenticated) location.href = "/login.html";
    return authenticated;
  },

  /**
   * Guard a page so only guests (unauthenticated users) can view it.
   * Redirects already-logged-in users to the home page. Use on login and
   * register pages to avoid showing them to authenticated users.
   * @returns {Promise<boolean>} `true` if authenticated (triggers redirect), `false` if guest.
   */
  async guestOnly() {
    const authenticated = await SS.ensureAuth();
    if (authenticated) location.href = "/";
    return authenticated;
  },

  /**
   * Return the navigation label translation map for all supported languages.
   * Kept as a method (not a constant) so the object is always freshly created
   * and cannot be mutated by external code between renders.
   * @returns {Object} Map of language code to label key/value pairs.
   */
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

  /**
   * Render the top navigation bar into the `#topnav` element.
   * Fetches the current user from the server on every call so the nav always
   * reflects live auth state. Also wires up language switcher buttons, the
   * theme toggle, and the logout button. Re-initialises Lucide icons after
   * injecting HTML so newly added `data-lucide` attributes are rendered.
   * @param {string} [active] - The key of the currently active nav link
   *   (e.g. `"scan"`, `"stats"`, `"cal"`, `"about"`). Adds the `is-active`
   *   CSS class to the matching anchor.
   * @returns {Promise<void>}
   */
  async paintNav(active) {
    const root = document.getElementById("topnav");
    if (!root) return;
    let user = SS.user();
    if (SS.authenticated !== false) {
      try {
        user = await SS.me();
      } catch {
        user = null;
      }
    }
    const isAuthed = SS.isAuthed();

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
