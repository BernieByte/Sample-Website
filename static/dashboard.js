document.addEventListener('DOMContentLoaded', async () => {
  const fileListEl = document.getElementById('fileList');
  const dashboardUserEl = document.getElementById('dashboardUser');
  const userAvatarEl = document.getElementById('userAvatar');
  const fileTitleEl = document.getElementById('fileTitle');
  const breadcrumbTitleEl = document.getElementById('breadcrumbTitle');
  const editorEl = document.getElementById('editor');
  const saveFileBtn = document.getElementById('saveFileBtn');
  const solveMathBtn = document.getElementById('solveMathBtn');
  const exportFileBtn = document.getElementById('exportFileBtn');
  const duplicateFileBtn = document.getElementById('duplicateFileBtn');
  const deleteFileBtn = document.getElementById('deleteFileBtn');
  const newFileBtn = document.getElementById('newFileBtn');
  const logoutBtn = document.getElementById('logoutBtn');
  const fileSearchEl = document.getElementById('fileSearch');
  const saveStatusEl = document.getElementById('saveStatus');
  const wordCountEl = document.getElementById('wordCount');
  const charCountEl = document.getElementById('charCount');
  const documentCountEl = document.getElementById('documentCount');
  const moreMenuBtn = document.getElementById('moreMenuBtn');
  const moreMenuEl = document.getElementById('moreMenu');
  const mathToolsBtn = document.getElementById('mathToolsBtn');
  const mathToolsMenu = document.getElementById('mathToolsMenu');
  const changePasswordForm = document.getElementById('changePasswordForm');
  const passwordMessageEl = document.getElementById('passwordMessage');
  const toastRegion = document.getElementById('toastRegion');

  let selectedFileId = null;
  let files = [];
  let autosaveTimer = null;
  let saving = false;
  let saveAgain = false;
  let savedRange = null;

  const notify = (message, isError = false) => {
    const toast = document.createElement('div');
    toast.className = `writer-toast${isError ? ' error' : ''}`;
    toast.textContent = message;
    toastRegion.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
  };

  const setSaveStatus = (message, state = 'saved') => {
    saveStatusEl.classList.toggle('is-saving', state === 'saving');
    saveStatusEl.classList.toggle('is-error', state === 'error');
    saveStatusEl.lastChild.textContent = ` ${message}`;
  };

  const fetchJson = async (url, options = {}) => {
    const response = await fetch(url, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    });
    const contentType = response.headers.get('content-type') || '';
    let data = {};
    if (contentType.includes('application/json')) data = await response.json();
    if (!response.ok) throw new Error(data.error || `Request failed (${response.status})`);
    return data;
  };

  const setDocumentTitle = (value) => {
    const title = value || 'Untitled document';
    breadcrumbTitleEl.textContent = title;
    document.title = `${title} | ByteNest`;
  };

  const updateCounts = () => {
    const text = editorEl.innerText || '';
    const words = text.trim() ? text.trim().split(/\s+/).length : 0;
    wordCountEl.textContent = `${words} ${words === 1 ? 'word' : 'words'}`;
    charCountEl.textContent = `${text.replace(/\n/g, '').length} characters`;
  };

  const renderFiles = () => {
    fileListEl.replaceChildren();
    documentCountEl.textContent = files.length;
    const query = fileSearchEl.value.trim().toLowerCase();
    const visibleFiles = files.filter((file) => file.title.toLowerCase().includes(query));

    if (!visibleFiles.length) {
      const empty = document.createElement('p');
      empty.className = 'writer-empty-files';
      empty.textContent = files.length ? 'No documents match your search.' : 'Your saved documents will appear here.';
      fileListEl.appendChild(empty);
      return;
    }

    visibleFiles.forEach((file) => {
      const item = document.createElement('button');
      item.type = 'button';
      item.className = `writer-file-item${file.id === selectedFileId ? ' active' : ''}`;
      item.setAttribute('role', 'listitem');

      const icon = document.createElement('span');
      icon.className = 'writer-file-icon';
      icon.setAttribute('aria-hidden', 'true');
      icon.textContent = '▤';

      const copy = document.createElement('span');
      copy.className = 'writer-file-copy';
      const title = document.createElement('strong');
      title.textContent = file.title;
      const updated = document.createElement('small');
      updated.textContent = `Edited ${new Date(file.updated_at).toLocaleDateString()}`;
      copy.append(title, updated);
      item.append(icon, copy);
      item.addEventListener('click', () => openFile(file.id, file.title, file.content));
      fileListEl.appendChild(item);
    });
  };

  const loadFiles = async () => {
    const data = await fetchJson('/api/files');
    files = data.files || [];
    renderFiles();
  };

  const openFile = async (fileId, title, content) => {
    if (autosaveTimer) {
      clearTimeout(autosaveTimer);
      autosaveTimer = null;
      if (!await saveFile()) return;
    }
    selectedFileId = fileId;
    fileTitleEl.value = title;
    setDocumentTitle(title);
    const savedContent = content || '';
    editorEl.innerHTML = savedContent;
    setSaveStatus('All changes saved');
    savedRange = null;
    updateCounts();
    renderFiles();
  };

  const createNewFile = () => {
    if (autosaveTimer) clearTimeout(autosaveTimer);
    selectedFileId = null;
    fileTitleEl.value = '';
    setDocumentTitle('Untitled document');
    editorEl.replaceChildren();
    savedRange = null;
    setSaveStatus('New document');
    updateCounts();
    renderFiles();
    fileTitleEl.focus();
  };

  const saveFile = async () => {
    if (saving) {
      saveAgain = true;
      return false;
    }
    if (autosaveTimer) {
      clearTimeout(autosaveTimer);
      autosaveTimer = null;
    }

    const title = fileTitleEl.value.trim() || 'Untitled document';
    const content = editorEl.innerHTML;
    const fileIdAtStart = selectedFileId;
    saving = true;
    setSaveStatus('Saving…', 'saving');

    try {
      const data = fileIdAtStart
        ? await fetchJson(`/api/files/${fileIdAtStart}`, {
          method: 'PUT', body: JSON.stringify({ title, content }),
        })
        : await fetchJson('/api/files', {
          method: 'POST', body: JSON.stringify({ title, content }),
        });

      if (!fileIdAtStart) selectedFileId = data.file.id;
      await loadFiles();
      setDocumentTitle(title);
      const changedDuringSave = content !== editorEl.innerHTML || title !== fileTitleEl.value.trim();
      if (changedDuringSave) {
        saveAgain = true;
      }
      if (saveAgain) {
        saveAgain = false;
        scheduleAutosave();
      } else {
        setSaveStatus('All changes saved');
      }
      return !changedDuringSave;
    } catch (error) {
      setSaveStatus('Could not save', 'error');
      notify(error.message || 'Unable to save document.', true);
      return false;
    } finally {
      saving = false;
      if (saveAgain) {
        saveAgain = false;
        scheduleAutosave();
      }
    }
  };

  const scheduleAutosave = () => {
    setSaveStatus('Unsaved changes', 'saving');
    clearTimeout(autosaveTimer);
    autosaveTimer = setTimeout(saveFile, 1100);
  };

  const duplicateFile = async () => {
    if (!selectedFileId) {
      notify('Save this document before making a copy.', true);
      return;
    }
    if (autosaveTimer) {
      clearTimeout(autosaveTimer);
      autosaveTimer = null;
      if (!await saveFile()) return;
    }
    try {
      const data = await fetchJson(`/api/files/${selectedFileId}/duplicate`, { method: 'POST' });
      await loadFiles();
      await openFile(data.file.id, data.file.title, data.file.content);
      notify('A copy was created.');
    } catch (error) {
      notify(error.message || 'Unable to make a copy.', true);
    }
  };

  const deleteFile = async () => {
    if (!selectedFileId) {
      notify('Save the document before moving it to trash.', true);
      return;
    }
    if (!window.confirm(`Move “${fileTitleEl.value || 'Untitled document'}” to trash?`)) return;
    if (autosaveTimer) {
      clearTimeout(autosaveTimer);
      autosaveTimer = null;
    }
    try {
      await fetchJson(`/api/files/${selectedFileId}`, { method: 'DELETE' });
      selectedFileId = null;
      createNewFile();
      await loadFiles();
      notify('Document moved to trash.');
    } catch (error) {
      notify(error.message || 'Unable to delete document.', true);
    }
  };

  const logout = async () => {
    if (autosaveTimer) {
      clearTimeout(autosaveTimer);
      autosaveTimer = null;
      if (!await saveFile()) return;
    }
    try {
      await fetchJson('/api/logout', { method: 'POST' });
    } finally {
      window.location.href = '/';
    }
  };

  const changePassword = async (event) => {
    event.preventDefault();
    passwordMessageEl.textContent = 'Updating…';
    passwordMessageEl.classList.remove('error');
    try {
      const data = await fetchJson('/api/password/change', {
        method: 'POST',
        body: JSON.stringify({
          current_password: document.getElementById('currentPassword').value,
          new_password: document.getElementById('newPassword').value,
        }),
      });
      passwordMessageEl.textContent = data.message;
      changePasswordForm.reset();
    } catch (error) {
      passwordMessageEl.textContent = error.message;
      passwordMessageEl.classList.add('error');
    }
  };

  const rememberSelection = () => {
    const selection = window.getSelection();
    if (selection && selection.rangeCount && editorEl.contains(selection.anchorNode)) {
      savedRange = selection.getRangeAt(0).cloneRange();
    }
  };

  const restoreSelection = () => {
    editorEl.focus();
    if (!savedRange) return;
    const selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(savedRange);
  };

  const runCommand = (command, value = null) => {
    restoreSelection();
    document.execCommand(command, false, value);
    rememberSelection();
    updateCounts();
    scheduleAutosave();
  };

  const escapeMathText = (value) => value.replace(/[&<>"']/g, (character) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  })[character]);

  const insertMathHtml = (markup) => {
    restoreSelection();
    document.execCommand('insertHTML', false, markup);
    rememberSelection();
    updateCounts();
    scheduleAutosave();
    mathToolsMenu.hidden = true;
    mathToolsBtn.setAttribute('aria-expanded', 'false');
  };

  const insertFraction = () => {
    const numerator = window.prompt('Enter the numerator', 'a + b');
    if (numerator === null) return;
    const denominator = window.prompt('Enter the denominator', 'c');
    if (denominator === null) return;
    const fraction = `<span style="display:inline-flex;flex-direction:column;align-items:center;text-align:center;vertical-align:middle;line-height:1.15"><span style="padding:0 0.22em;border-bottom:1px solid currentColor">${escapeMathText(numerator)}</span><span style="padding:0 0.22em">${escapeMathText(denominator)}</span></span>`;
    insertMathHtml(fraction);
  };

  const insertRoot = () => {
    const expression = window.prompt('Enter the expression under the root', 'x + 1');
    if (expression === null) return;
    const index = window.prompt('Root index (leave blank for a square root)', '');
    if (index === null) return;
    const indexMarkup = index.trim() ? `<sup>${escapeMathText(index.trim())}</sup>` : '';
    const root = `<span style="display:inline-flex;align-items:center;vertical-align:middle;white-space:nowrap">${indexMarkup}<span style="font-size:1.25em">√</span><span style="border-top:1px solid currentColor;padding:0 0.14em">${escapeMathText(expression)}</span></span>`;
    insertMathHtml(root);
  };

  const insertEquation = () => {
    const expression = window.prompt('Enter one equation or step of working', 'x + 2 = 5');
    if (expression === null || !expression.trim()) return;
    insertMathHtml(`<div style="text-align:center;font-size:14pt;line-height:1.8">${escapeMathText(expression.trim())}</div><p><br></p>`);
  };

  const insertTable = () => {
    const rowsInput = window.prompt('How many rows? (1–12)', '3');
    if (rowsInput === null) return;
    const columnsInput = window.prompt('How many columns? (1–8)', '3');
    if (columnsInput === null) return;
    const rows = Math.max(1, Math.min(12, Number.parseInt(rowsInput, 10) || 1));
    const columns = Math.max(1, Math.min(8, Number.parseInt(columnsInput, 10) || 1));
    let tableHtml = '<table><tbody>';
    for (let row = 0; row < rows; row += 1) {
      tableHtml += '<tr>';
      for (let col = 0; col < columns; col += 1) {
        tableHtml += row === 0 ? '<th>Heading</th>' : '<td><br></td>';
      }
      tableHtml += '</tr>';
    }
    tableHtml += '</tbody></table><p><br></p>';
    runCommand('insertHTML', tableHtml);
  };

  const exportHtml = () => {
    const title = fileTitleEl.value.trim() || 'Untitled document';
    const safeTitle = title.replace(/[&<>"']/g, (character) => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
    })[character]);
    const html = `<!doctype html><html lang="en"><head><meta charset="utf-8"><title>${safeTitle}</title><style>body{max-width:760px;margin:60px auto;padding:0 36px;font:12pt/1.7 Arial,sans-serif;color:#252a34}table{width:100%;border-collapse:collapse}td,th{border:1px solid #aaa;padding:8px}blockquote{border-left:3px solid #777;padding-left:16px;color:#555}pre{white-space:pre-wrap}</style></head><body>${editorEl.innerHTML}</body></html>`;
    const blob = new Blob([html], { type: 'text/html;charset=utf-8' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `${title.replace(/[\\/:*?"<>|]/g, '-').slice(0, 100) || 'document'}.html`;
    link.click();
    URL.revokeObjectURL(link.href);
    notify('Document exported as an HTML file.');
  };

  const getUser = async () => {
    try {
      const data = await fetchJson('/api/me');
      dashboardUserEl.textContent = data.user.username;
      userAvatarEl.textContent = (data.user.username[0] || 'U').toUpperCase();
    } catch (_error) {
      window.location.href = '/login';
    }
  };

  newFileBtn.addEventListener('click', async () => {
    if (autosaveTimer) {
      clearTimeout(autosaveTimer);
      autosaveTimer = null;
      if (!await saveFile()) return;
    }
    createNewFile();
  });
  saveFileBtn.addEventListener('click', saveFile);
  solveMathBtn.addEventListener('mousedown', (event) => event.preventDefault());
  solveMathBtn.addEventListener('click', async () => {
    const selection = window.getSelection();
    const hasEditorSelection = selection && !selection.isCollapsed
      && editorEl.contains(selection.anchorNode) && editorEl.contains(selection.focusNode);
    const expression = (hasEditorSelection ? selection.toString() : editorEl.innerText).trim();
    if (!expression) {
      notify('Type a math expression or equation in the document first.', true);
      return;
    }

    solveMathBtn.disabled = true;
    solveMathBtn.textContent = 'Solving…';
    try {
      const result = await fetchJson('/api/math/solve', {
        method: 'POST',
        body: JSON.stringify({ expression }),
      });
      const line = document.createElement('p');
      line.className = 'math-solve-result';
      const label = document.createElement('strong');
      label.textContent = 'Solution: ';
      line.append(label, document.createTextNode(result.answer));
      editorEl.appendChild(line);
      line.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      rememberSelection();
      updateCounts();
      scheduleAutosave();
      notify('Solution added to your document.');
    } catch (error) {
      notify(error.message || 'This input could not be solved as written.', true);
    } finally {
      solveMathBtn.disabled = false;
      solveMathBtn.textContent = 'Solve';
    }
  });
  exportFileBtn.addEventListener('click', exportHtml);
  document.getElementById('printFileBtn').addEventListener('click', () => window.print());
  duplicateFileBtn.addEventListener('click', duplicateFile);
  deleteFileBtn.addEventListener('click', deleteFile);
  logoutBtn.addEventListener('click', logout);
  changePasswordForm.addEventListener('submit', changePassword);
  fileSearchEl.addEventListener('input', renderFiles);
  fileTitleEl.addEventListener('input', () => {
    setDocumentTitle(fileTitleEl.value.trim() || 'Untitled document');
    scheduleAutosave();
  });
  editorEl.addEventListener('input', () => {
    updateCounts();
    scheduleAutosave();
  });
  editorEl.addEventListener('keyup', rememberSelection);
  editorEl.addEventListener('mouseup', rememberSelection);
  document.addEventListener('selectionchange', rememberSelection);

  document.querySelectorAll('[data-command]').forEach((button) => {
    button.addEventListener('mousedown', (event) => event.preventDefault());
    button.addEventListener('click', () => runCommand(button.dataset.command));
  });

  document.getElementById('blockStyle').addEventListener('change', (event) => {
    runCommand('formatBlock', event.target.value.toLowerCase());
  });
  document.getElementById('fontFamily').addEventListener('change', (event) => runCommand('fontName', event.target.value));
  document.getElementById('fontSize').addEventListener('change', (event) => runCommand('fontSize', event.target.value));
  document.getElementById('lineSpacing').addEventListener('change', (event) => {
    restoreSelection();
    const selection = window.getSelection();
    let node = selection && selection.rangeCount ? selection.anchorNode : editorEl;
    if (node && node.nodeType === Node.TEXT_NODE) node = node.parentElement;
    let block = node && node.closest ? node.closest('p,div,h1,h2,h3,h4,h5,h6,li,blockquote,pre') : null;
    if (!block || !editorEl.contains(block)) {
      document.execCommand('formatBlock', false, 'p');
      const updatedSelection = window.getSelection();
      node = updatedSelection && updatedSelection.rangeCount ? updatedSelection.anchorNode : editorEl;
      if (node && node.nodeType === Node.TEXT_NODE) node = node.parentElement;
      block = node && node.closest ? node.closest('p,div,h1,h2,h3,h4,h5,h6,li,blockquote,pre') : null;
    }
    if (block && editorEl.contains(block)) block.style.lineHeight = event.target.value;
    rememberSelection();
    scheduleAutosave();
  });
  document.getElementById('textColor').addEventListener('input', (event) => runCommand('foreColor', event.target.value));
  document.getElementById('highlightColor').addEventListener('input', (event) => {
    restoreSelection();
    document.execCommand('styleWithCSS', false, true);
    document.execCommand('hiliteColor', false, event.target.value);
    rememberSelection();
    scheduleAutosave();
  });
  document.getElementById('insertLinkBtn').addEventListener('mousedown', (event) => event.preventDefault());
  document.getElementById('insertLinkBtn').addEventListener('click', () => {
    const url = window.prompt('Enter a web address (https://…) or email link (mailto:…)');
    if (url && /^(https?:\/\/|mailto:)/i.test(url.trim())) runCommand('createLink', url.trim());
    else if (url) notify('Use a web link starting with https:// or an email link starting with mailto:.', true);
  });
  document.getElementById('insertTableBtn').addEventListener('mousedown', (event) => event.preventDefault());
  document.getElementById('insertTableBtn').addEventListener('click', insertTable);
  document.getElementById('findTextBtn').addEventListener('mousedown', (event) => event.preventDefault());
  document.getElementById('findTextBtn').addEventListener('click', () => {
    const query = window.prompt('Find text in this document');
    if (!query) return;
    editorEl.focus();
    if (!window.find(query)) notify('No matching text was found.', true);
    rememberSelection();
  });
  mathToolsBtn.addEventListener('mousedown', (event) => event.preventDefault());
  mathToolsBtn.addEventListener('click', () => {
    const opening = mathToolsMenu.hidden;
    mathToolsMenu.hidden = !opening;
    mathToolsBtn.setAttribute('aria-expanded', String(opening));
    if (opening) {
      const rect = mathToolsBtn.getBoundingClientRect();
      const menuWidth = Math.min(310, window.innerWidth - 24);
      const left = Math.min(Math.max(12, rect.left), window.innerWidth - menuWidth - 12);
      const menuHeight = mathToolsMenu.getBoundingClientRect().height;
      const below = rect.bottom + 8;
      const top = below + menuHeight < window.innerHeight - 10
        ? below
        : Math.max(10, rect.top - menuHeight - 8);
      mathToolsMenu.style.left = `${left}px`;
      mathToolsMenu.style.top = `${top}px`;
    }
  });
  [
    document.getElementById('insertFractionBtn'),
    document.getElementById('insertRootBtn'),
    document.getElementById('insertEquationBtn'),
    ...document.querySelectorAll('[data-math-symbol]'),
  ].forEach((button) => button.addEventListener('mousedown', (event) => event.preventDefault()));
  document.getElementById('insertFractionBtn').addEventListener('click', insertFraction);
  document.getElementById('insertRootBtn').addEventListener('click', insertRoot);
  document.getElementById('insertEquationBtn').addEventListener('click', insertEquation);
  document.querySelectorAll('[data-math-symbol]').forEach((button) => {
    button.addEventListener('click', () => runCommand('insertText', button.dataset.mathSymbol));
  });

  moreMenuBtn.addEventListener('click', () => {
    const opening = moreMenuEl.hidden;
    moreMenuEl.hidden = !opening;
    moreMenuBtn.setAttribute('aria-expanded', String(opening));
  });
  document.addEventListener('click', (event) => {
    if (!event.target.closest('.writer-more-menu')) {
      moreMenuEl.hidden = true;
      moreMenuBtn.setAttribute('aria-expanded', 'false');
    }
    if (!event.target.closest('.math-tools-wrap')) {
      mathToolsMenu.hidden = true;
      mathToolsBtn.setAttribute('aria-expanded', 'false');
    }
  });
  document.querySelector('.writer-canvas-scroll').addEventListener('scroll', () => {
    mathToolsMenu.hidden = true;
    mathToolsBtn.setAttribute('aria-expanded', 'false');
  });

  document.addEventListener('keydown', (event) => {
    const key = event.key.toLowerCase();
    if ((event.ctrlKey || event.metaKey) && key === 's') {
      event.preventDefault();
      saveFile();
    }
    if ((event.ctrlKey || event.metaKey) && key === 'k') {
      event.preventDefault();
      fileSearchEl.focus();
    }
    if (key === 'escape') {
      mathToolsMenu.hidden = true;
      mathToolsBtn.setAttribute('aria-expanded', 'false');
    }
  });

  try {
    await getUser();
    await loadFiles();
  } catch (error) {
    notify(error.message || 'Unable to load documents.', true);
  }
  updateCounts();
});
