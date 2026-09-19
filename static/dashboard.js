document.addEventListener('DOMContentLoaded', async () => {
  const fileListEl = document.getElementById('fileList');
  const dashboardUserEl = document.getElementById('dashboardUser');
  const fileTitleEl = document.getElementById('fileTitle');
  const editorEl = document.getElementById('editor');
  const saveFileBtn = document.getElementById('saveFileBtn');
  const deleteFileBtn = document.getElementById('deleteFileBtn');
  const newFileBtn = document.getElementById('newFileBtn');
  const logoutBtn = document.getElementById('logoutBtn');

  let selectedFileId = null;
  let files = [];

  const notify = (message, isError = false) => {
    const msg = document.createElement('div');
    msg.textContent = message;
    msg.style.marginTop = '12px';
    msg.style.fontSize = '0.9rem';
    msg.style.color = isError ? '#e24c5b' : '#2d6df6';
    document.body.appendChild(msg);
    setTimeout(() => msg.remove(), 2500);
  };

  const fetchJson = async (url, options = {}) => {
    const response = await fetch(url, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    });

    const contentType = response.headers.get('content-type') || '';
    let data = {};
    if (contentType.includes('application/json')) {
      data = await response.json();
    }

    if (!response.ok) {
      throw new Error(data.error || `Request failed (${response.status})`);
    }

    return data;
  };

  const getUser = async () => {
    try {
      const data = await fetchJson('/api/me');
      dashboardUserEl.textContent = data.user.username;
    } catch (error) {
      window.location.href = '/login';
    }
  };

  const renderFiles = () => {
    fileListEl.innerHTML = '';

    if (!files.length) {
      fileListEl.innerHTML = '<div class="file-item"><h4>No files yet</h4><small>Create a new file to get started.</small></div>';
      return;
    }

    files.forEach((file) => {
      const item = document.createElement('div');
      item.className = 'file-item' + (file.id === selectedFileId ? ' active' : '');
      item.innerHTML = `
        <h4>${file.title}</h4>
        <small>${new Date(file.updated_at).toLocaleString()}</small>
      `;
      item.addEventListener('click', () => openFile(file.id, file.title, file.content));
      fileListEl.appendChild(item);
    });
  };

  const loadFiles = async () => {
    const data = await fetchJson('/api/files');
    files = data.files || [];
    renderFiles();
  };

  const openFile = (fileId, title, content) => {
    selectedFileId = fileId;
    fileTitleEl.value = title;
    editorEl.value = content || '';
    renderFiles();
  };

  const createNewFile = () => {
    selectedFileId = null;
    fileTitleEl.value = '';
    editorEl.value = '';
    fileTitleEl.focus();
  };

  const saveFile = async () => {
    const title = fileTitleEl.value.trim() || 'Untitled document';
    const content = editorEl.value;

    try {
      let data;
      if (selectedFileId) {
        data = await fetchJson(`/api/files/${selectedFileId}`, {
          method: 'PUT',
          body: JSON.stringify({ title, content }),
        });
        notify('File updated successfully.');
      } else {
        data = await fetchJson('/api/files', {
          method: 'POST',
          body: JSON.stringify({ title, content }),
        });
        notify('File saved successfully.');
      }

      selectedFileId = data.file?.id || selectedFileId;
      await loadFiles();
      if (data.file) {
        openFile(data.file.id, data.file.title, data.file.content);
      }
    } catch (error) {
      notify(error.message || 'Unable to save file.', true);
    }
  };

  const deleteFile = async () => {
    if (!selectedFileId) {
      notify('Select a file to delete.', true);
      return;
    }

    try {
      await fetchJson(`/api/files/${selectedFileId}`, { method: 'DELETE' });
      selectedFileId = null;
      fileTitleEl.value = '';
      editorEl.value = '';
      notify('File deleted.');
      await loadFiles();
    } catch (error) {
      notify(error.message || 'Unable to delete file.', true);
    }
  };

  const logout = async () => {
    try {
      await fetchJson('/api/logout', { method: 'POST' });
    } finally {
      window.location.href = '/';
    }
  };

  newFileBtn.addEventListener('click', createNewFile);
  saveFileBtn.addEventListener('click', saveFile);
  deleteFileBtn.addEventListener('click', deleteFile);
  logoutBtn.addEventListener('click', logout);

  await getUser();
  await loadFiles();
});
