document.addEventListener('DOMContentLoaded', () => {
  const tableBody = document.getElementById('userTableBody');
  const loginTableBody = document.getElementById('loginTableBody');
  const userCount = document.getElementById('userCount');
  const search = document.getElementById('userSearch');
  const message = document.getElementById('adminMessage');
  let users = [];

  const renderLogins = (logins) => {
    loginTableBody.innerHTML = '';
    if (!logins.length) {
      loginTableBody.innerHTML = '<tr><td colspan="3" class="empty-cell">No logins recorded yet.</td></tr>';
      return;
    }

    logins.forEach((login) => {
      const row = document.createElement('tr');
      row.innerHTML = `
        <td class="user-name">${login.username}</td>
        <td>${login.email}</td>
        <td>${new Date(login.logged_in_at).toLocaleString()}</td>
      `;
      loginTableBody.appendChild(row);
    });
  };

  const setMessage = (text, isError = false) => {
    message.textContent = text;
    message.className = `admin-message${isError ? ' error' : ''}`;
  };

  const renderUsers = () => {
    const query = search.value.trim().toLowerCase();
    const visibleUsers = users.filter((user) =>
      `${user.username} ${user.email}`.toLowerCase().includes(query)
    );
    tableBody.innerHTML = '';

    if (!visibleUsers.length) {
      tableBody.innerHTML = '<tr><td colspan="4" class="empty-cell">No matching users.</td></tr>';
      return;
    }

    visibleUsers.forEach((user) => {
      const row = document.createElement('tr');
      row.innerHTML = `
        <td>${user.id}</td>
        <td class="user-name">${user.username}</td>
        <td>${user.email}</td>
        <td>${new Date(user.created_at).toLocaleString()}</td>
      `;
      tableBody.appendChild(row);
    });
  };

  const loadUsers = async () => {
    setMessage('Loading users...');
    const response = await fetch('/api/admin/users');
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Unable to load users.');
    users = data.users || [];
    userCount.textContent = users.length;
    renderUsers();
    const loginResponse = await fetch('/api/admin/logins');
    const loginData = await loginResponse.json();
    if (!loginResponse.ok) throw new Error(loginData.error || 'Unable to load login activity.');
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