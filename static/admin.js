document.addEventListener('DOMContentLoaded', () => {
  const tableBody = document.getElementById('userTableBody');
  const userCount = document.getElementById('userCount');
  const search = document.getElementById('userSearch');
  const message = document.getElementById('adminMessage');
  let users = [];

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