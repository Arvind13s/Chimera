/**
 * API + session layer for the static browser frontend.
 */

const TOKEN_KEY = 'chimera_token';
const USER_KEY = 'chimera_user';

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function getStoredUser() {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    return null;
  }
}

function setSession(token, user) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export async function login(email, password) {
  const res = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Login failed');
  setSession(data.token, data.user);
  return data.user;
}

export async function sendOtp(name, email, password) {
  const res = await fetch('/api/auth/send-otp', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, email, password }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || data.error || 'Failed to send verification code');
  return data;
}

export async function verifyOtp(email, otp) {
  const res = await fetch('/api/auth/verify-otp', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, otp }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || data.error || 'Verification failed');
  setSession(data.token, data.user);
  return data.user;
}

export async function resendOtp(email) {
  const res = await fetch('/api/auth/resend-otp', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || data.error || 'Failed to resend code');
  return data;
}

export async function forgotPassword(email) {
  const res = await fetch('/api/auth/forgot-password', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || data.error || 'Failed to send reset code');
  return data;
}

export async function resetPassword(email, otp, newPassword) {
  const res = await fetch('/api/auth/reset-password', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, otp, new_password: newPassword }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || data.error || 'Password reset failed');
  if (data.token && data.user) {
    setSession(data.token, data.user);
  }
  return data;
}

export async function resendResetOtp(email) {
  const res = await fetch('/api/auth/resend-reset-otp', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || data.error || 'Failed to resend reset code');
  return data;
}

export async function register(name, email, password) {
  const res = await fetch('/api/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, email, password }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Registration failed');
  setSession(data.token, data.user);
  return data.user;
}

export async function getCategories() {
  const res = await fetch('/api/config/categories');
  const data = await res.json();
  return data.categories || {};
}

export async function getVoices() {
  const res = await fetch('/api/config/voices');
  const data = await res.json();
  return data.voices || [];
}

/**
 * Starts a generation run and streams Server-Sent Events back.
 * Calls onMessage(data) for each parsed event, onError(err) on failure,
 * and always calls onDone() when the stream ends (success or failure).
 */
export async function streamGenerate({ niche, customTopic, voice }, onMessage, onError, onDone) {
  const token = getToken();
  const params = new URLSearchParams({ token, voice });
  if (niche) params.set('niche', niche);
  if (customTopic) params.set('custom_topic', customTopic);

  try {
    const response = await fetch(`/api/generate/stream?${params}`);
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      onError(err.detail || 'Generation failed');
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop();

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            onMessage(data);
          } catch {
            /* skip malformed SSE data */
          }
        }
      }
    }
  } catch (err) {
    onError(`Connection error: ${err.message}`);
  } finally {
    onDone();
  }
}
