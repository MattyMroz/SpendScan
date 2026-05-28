function ssIcons() {
  if (window.lucide && typeof window.lucide.createIcons === "function") {
    window.lucide.createIcons();
  }
}
document.addEventListener("DOMContentLoaded", ssIcons);
window.ssIcons = ssIcons;
