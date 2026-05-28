const SS = {
  apiBase: `${location.origin}/api/v1`,

  token() { return localStorage.getItem('ss_token'); },
  user()  { return JSON.parse(localStorage.getItem('ss_user') || 'null'); },
  isAuthed() { return !!SS.token(); },

  setSession(token, user) {
    localStorage.setItem('ss_token', token);
    if (user) localStorage.setItem('ss_user', JSON.stringify(user));
  },
  clearSession() {
    localStorage.removeItem('ss_token');
    localStorage.removeItem('ss_user');
  },
  logout() {
    SS.clearSession();
    location.href = '/login.html';
  },

  async api(path, opts = {}) {
    const headers = new Headers(opts.headers || {});
    const token = SS.token();
    if (token) headers.set('Authorization', `Bearer ${token}`);
    if (opts.body && !headers.has('Content-Type') && !(opts.body instanceof FormData)) {
      headers.set('Content-Type', 'application/json');
    }
    const res = await fetch(`${SS.apiBase}${path}`, { ...opts, headers });
    if (res.status === 401) {
      SS.clearSession();
      const here = location.pathname.split('/').pop();
      if (here !== 'login.html' && here !== 'register.html' && here !== 'index.html') {
        location.href = '/login.html';
      }
      throw new Error('Unauthorized');
    }
    return res;
  },

  async login(email, password) {
    const res = await SS.api('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) });
    if (!res.ok) throw new Error((await res.json()).detail || 'Invalid credentials');
    const data = await res.json();
    SS.setSession(data.access_token, null);
    return data;
  },

  async register(username, email, password) {
    const res = await SS.api('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, email, password }),
    });
    if (!res.ok) throw new Error((await res.json()).detail || 'Registration failed');
    const data = await res.json();
    SS.setSession(data.access_token, null);
    return data;
  },

  async me() {
    const res = await SS.api('/auth/me');
    if (!res.ok) throw new Error('Failed to load profile');
    const user = await res.json();
    localStorage.setItem('ss_user', JSON.stringify(user));
    return user;
  },

  guard() {
    if (!SS.isAuthed()) location.href = '/login.html';
  },

  guestOnly() {
    if (SS.isAuthed()) location.href = '/scan.html';
  },
};

window.SS = SS;
