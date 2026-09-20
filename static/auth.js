document.addEventListener('DOMContentLoaded', () => {
  const signupForm = document.getElementById('signupForm');
  const loginForm = document.getElementById('loginForm');

  const setMessage = (nodeId, text, isError = false) => {
    const node = document.getElementById(nodeId);
    if (!node) return;
    node.textContent = text;
    node.style.color = isError ? '#e24c5b' : '#2d6df6';
  };

  const getBrowserLocation = () => new Promise((resolve) => {
    if (!navigator.geolocation) {
      resolve(null);
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => resolve({
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
      }),
      () => resolve(null),
      { enableHighAccuracy: true, timeout: 5000, maximumAge: 300000 }
    );
  });

  if (signupForm) {
    signupForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      const username = document.getElementById('signupUsername').value.trim();
      const email = document.getElementById('signupEmail').value.trim();
      const password = document.getElementById('signupPassword').value;

      if (!username || !email || !password) {
        setMessage('signupMessage', 'Please fill in all fields.', true);
        return;
      }

      try {
        setMessage('signupMessage', 'Creating account...');
        const location = await getBrowserLocation();
        const response = await fetch('/api/signup', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username, email, password, location })
        });

        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.error || 'Signup failed.');
        }

        setMessage('signupMessage', 'Account created! Redirecting...');
        window.location.href = data.user.is_admin ? '/admin' : '/dashboard';
      } catch (error) {
        setMessage('signupMessage', error.message || 'Signup failed.', true);
      }
    });
  }

  if (loginForm) {
    loginForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      const loginField = document.getElementById('loginField').value.trim();
      const password = document.getElementById('loginPassword').value;

      if (!loginField || !password) {
        setMessage('loginMessage', 'Please enter your username/email and password.', true);
        return;
      }

      try {
        setMessage('loginMessage', 'Logging in...');
        const location = await getBrowserLocation();
        const response = await fetch('/api/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username_or_email: loginField, password, location })
        });

        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.error || 'Login failed.');
        }

        setMessage('loginMessage', 'Login successful! Redirecting...');
        window.location.href = data.user.is_admin ? '/admin' : '/dashboard';
      } catch (error) {
        setMessage('loginMessage', error.message || 'Login failed.', true);
      }
    });
  }
});
