/**
 * @file icons.js
 * @description Lucide icon initialisation helper. Exposes `ssIcons` globally
 * so any page or component can call it after injecting new `data-lucide`
 * attributes into the DOM (e.g. after a navigation re-render).
 */

/**
 * Render all `data-lucide` icon placeholders in the current document.
 * Safe to call multiple times — if Lucide is not yet loaded the call is a
 * no-op, preventing errors during lazy script loading.
 * @returns {void}
 */
function ssIcons() {
  if (window.lucide && typeof window.lucide.createIcons === "function") {
    window.lucide.createIcons();
  }
}
document.addEventListener("DOMContentLoaded", ssIcons);
window.ssIcons = ssIcons;
