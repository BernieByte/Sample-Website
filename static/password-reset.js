document.addEventListener('DOMContentLoaded', () => {
  const forgotForm = document.getElementById('forgotPasswordForm');
  const resetForm = document.getElementById('resetPasswordForm');

  const submitJson = async (url, body) => {
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Request failed.');
    return data;
  };

  if (forgotForm) {
    forgotForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      const message = document.getElementById('forgotMessage');
      message.textContent = 'Sending...';
      try {
        const data = await submitJson('/api/password-reset/request', {
          email: document.getElementById('resetEmail').value.trim(),
        });
        message.textContent = data.message;
      } catch (error) {
        message.textContent = error.message;
        message.classList.add('error');
      }
    });
  }

  if (resetForm) {
    resetForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      const message = document.getElementById('resetMessage');
      const password = document.getElementById('resetPassword').value;
      const confirmation = document.getElementById('confirmPassword').value;
      if (password !== confirmation) {
        message.textContent = 'Passwords do not match.';
        message.classList.add('error');
        return;
      }
      try {
        const data = await submitJson('/api/password-reset/confirm', {
          token: new URLSearchParams(window.location.search).get('token'),
          new_password: password,
        });
        message.textContent = data.message;
        setTimeout(() => { window.location.href = '/login'; }, 1200);
      } catch (error) {
        message.textContent = error.message;
        message.classList.add('error');
      }
    });
  }
});