
const SS = {
  isAuthed() { return !!localStorage.getItem('ss_user'); },
  user() { return JSON.parse(localStorage.getItem('ss_user') || 'null'); },
  login(email) { localStorage.setItem('ss_user', JSON.stringify({ email })); },
  logout() { localStorage.removeItem('ss_user'); window.location.href = 'login.html'; },
  apiBase() {
    return `http://${window.location.hostname || '127.0.0.1'}:8000/api/v1`;
  },
  async apiError(response, fallbackMessage) {
    try {
      const payload = await response.json();
      return payload.detail || JSON.stringify(payload);
    } catch {
      return fallbackMessage;
    }
  },
  mapReceipt(r) {
    const items = Array.isArray(r.items)
      ? r.items.map(item => ({
        name: item.product_name || item.name || 'Item',
        price: Number(item.total_price || item.price || 0),
      }))
      : null;
    const itemCount = items
      ? items.length
      : Number(r.item_count || 0);
    return {
      id: r.id,
      shop: r.merchant_name || 'Unknown shop',
      date: r.receipt_date || r.created_at || new Date().toISOString(),
      total: Number(r.total_amount || 0),
      currency: r.currency || 'PLN',
      itemCount,
      items,
    };
  },
  async fetchReceipts() {
    const response = await fetch(`${SS.apiBase()}/receipts`);
    if (!response.ok) {
      throw new Error(await SS.apiError(response, 'Failed to load receipts'));
    }
    const payload = await response.json();
    return payload.map(SS.mapReceipt);
  },
  async fetchReceipt(id) {
    const response = await fetch(`${SS.apiBase()}/receipts/${id}`);
    if (!response.ok) {
      throw new Error(await SS.apiError(response, 'Failed to load receipt'));
    }
    const payload = await response.json();
    return SS.mapReceipt(payload);
  },
  async deleteReceipt(id) {
    const response = await fetch(`${SS.apiBase()}/receipts/${id}`, { method: 'DELETE' });
    if (!response.ok && response.status !== 204) {
      throw new Error(await SS.apiError(response, 'Failed to delete receipt'));
    }
  },
  guard() {
    if (!SS.isAuthed()) window.location.href = 'login.html';
  },
  fmt(n, currency = 'PLN') {
    return new Intl.NumberFormat('pl-PL', {
      style: 'currency',
      currency,
    }).format(Number(n || 0));
  },
};

$(function () {
  const path = location.pathname.split('/').pop() || 'index.html';
  const authed = SS.isAuthed();
  const links = [
    { href: 'scan.html', icon: 'camera', label: 'Scan' },
    { href: 'stats.html', icon: 'bar-chart', label: 'Statistics' },
    { href: 'calendar.html', icon: 'calendar3', label: 'Calendar' },
    { href: 'about.html', icon: 'people', label: 'About' },
  ];
  const linkHtml = links.map(l =>
    `<li class="nav-item"><a class="nav-link ${path === l.href ? 'active' : ''}" href="${l.href}"><i class="bi bi-${l.icon} me-1"></i>${l.label}</a></li>`
  ).join('');
  const right = authed
    ? `<button id="ssLogout" class="btn btn-outline-light btn-sm"><i class="bi bi-box-arrow-right me-1"></i>Logout</button>`
    : `<a href="login.html" class="btn btn-outline-light btn-sm me-2"><i class="bi bi-box-arrow-in-right me-1"></i>Login</a>
       <a href="register.html" class="btn btn-info btn-sm text-dark"><i class="bi bi-person-plus me-1"></i>Register</a>`;

  const nav = `
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark sticky-top shadow-sm">
      <div class="container">
        <a class="navbar-brand fw-bold" href="${authed ? 'scan.html' : 'index.html'}">
          <i class="bi bi-receipt-cutoff me-2 text-info"></i>SpendScan
        </a>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#nv">
          <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="nv">
          <ul class="navbar-nav me-auto">${linkHtml}</ul>
          <div class="d-flex align-items-center">${right}</div>
        </div>
      </div>
    </nav>`;
  $('#nav-placeholder').html(nav);
  $('#ssLogout').on('click', SS.logout);
});
