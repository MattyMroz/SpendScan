/*
 * Dark/light toggle that works from the local file system (file://).
 *
 * Material's palette toggle stores the chosen scheme in localStorage, but browsers block
 * localStorage on file:// pages, so clicking the moon/sun icon appears to do nothing.
 * This script flips `data-md-color-scheme` directly on every click, independent of storage.
 */
(function () {
  function currentScheme() {
    return document.body.getAttribute("data-md-color-scheme") || "default";
  }

  function applyScheme(scheme) {
    document.body.setAttribute("data-md-color-scheme", scheme);
    try {
      localStorage.setItem("ss-scheme", scheme);
    } catch (e) {
      /* file:// may block storage - that's fine, the attribute is already applied */
    }
  }

  function wire() {
    // Restore a previously chosen scheme (works when storage is available).
    try {
      var saved = localStorage.getItem("ss-scheme");
      if (saved) applyScheme(saved);
    } catch (e) {}

    // The palette form contains the radio inputs that drive the toggle. Listen on the
    // whole document so it keeps working after instant navigation (if ever enabled).
    document.addEventListener("change", function (ev) {
      var t = ev.target;
      if (t && t.matches && t.matches('[data-md-component="palette"] input')) {
        var scheme = t.getAttribute("data-md-color-scheme");
        if (scheme) applyScheme(scheme);
      }
    });

    // Also handle a plain click on the toggle label as a fallback: just flip the scheme.
    document.addEventListener("click", function (ev) {
      var label = ev.target.closest && ev.target.closest('label[for^="__palette"]');
      if (label) {
        // Defer so Material's own handler runs first, then enforce the flip.
        setTimeout(function () {
          var next = currentScheme() === "slate" ? "default" : "slate";
          applyScheme(next);
        }, 0);
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", wire);
  } else {
    wire();
  }
})();
