document.addEventListener('DOMContentLoaded', () => {
  const tableBody = document.getElementById('userTableBody');
  const loginTableBody = document.getElementById('loginTableBody');
  const userCount = document.getElementById('userCount');
  const search = document.getElementById('userSearch');
  const message = document.getElementById('adminMessage');
  let users = [];

  const addCell = (row, value, className = '') => {
    const cell = document.createElement('td');
    if (className) cell.className = className;
    cell.textContent = value == null || value === '' ? 'Unavailable' : String(value);
    row.appendChild(cell);
  };

  const renderLogins = (logins) => {
    loginTableBody.innerHTML = '';
    if (!logins.length) {
      loginTableBody.innerHTML = '<tr><td colspan="8" class="empty-cell">No logins recorded yet.</td></tr>';
      return;
    }

    logins.forEach((login) => {
      const row = document.createElement('tr');
      addCell(row, login.username, 'user-name');
      addCell(row, login.email);
      addCell(row, login.ip_address);
      addCell(row, login.town);
      addCell(row, login.country);
      addCell(row, login.state);
      addCell(row, login.source);
      addCell(row, new Date(login.logged_in_at).toLocaleString());
      loginTableBody.appendChild(row);
    });
  };

  const setMessage = (text, isError = false) => {
    message.textContent = text;
    message.className = `admin-message${isError ? ' error' : ''}`;
  };

  const fetchJson = async (url) => {
    const response = await fetch(url, {
      headers: { Accept: 'application/json' },
    });
    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      throw new Error(`Admin API unavailable (${response.status}). Redeploy the latest Render commit.`);
    }
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || `Request failed (${response.status}).`);
    return data;
  };

  const renderUsers = () => {
    const query = search.value.trim().toLowerCase();
    const visibleUsers = users.filter((user) =>
      `${user.username} ${user.email}`.toLowerCase().includes(query)
    );
    tableBody.innerHTML = '';

    if (!visibleUsers.length) {
      tableBody.innerHTML = '<tr><td colspan="9" class="empty-cell">No matching users.</td></tr>';
      return;
    }

    visibleUsers.forEach((user) => {
      const row = document.createElement('tr');
      addCell(row, user.id);
      addCell(row, user.username, 'user-name');
      addCell(row, user.email);
      addCell(row, user.signup_ip);
      addCell(row, user.town);
      addCell(row, user.country);
      addCell(row, user.state);
      addCell(row, user.source);
      addCell(row, new Date(user.created_at).toLocaleString());
      tableBody.appendChild(row);
    });
  };

  const loadUsers = async () => {
    setMessage('Loading users...');
    const data = await fetchJson('/api/admin/users');
    users = data.users || [];
    userCount.textContent = users.length;
    renderUsers();
    const loginData = await fetchJson('/api/admin/logins');
    renderLogins(loginData.logins || []);
    setMessage(`Updated ${new Date().toLocaleTimeString()}.`);
  };

  document.getElementById('refreshUsers').addEventListener('click', () => {
    loadUsers().catch((error) => setMessage(error.message, true));
  });
  document.getElementById('logoutAdmin').addEventListener('click', async () => {
    await fetch('/api/logout', { method: 'POST' });
    window.location.href = '/';
  });
  search.addEventListener('input', renderUsers);
  loadUsers().catch((error) => setMessage(error.message, true));
});
