import {
  login,
  sendOtp,
  verifyOtp,
  resendOtp,
  forgotPassword,
  resetPassword,
  resendResetOtp,
  clearSession,
  getStoredUser,
} from './api.js';

let mode = 'login';
let previouslyFocused = null;
let currentUser = getStoredUser();

// Registration OTP state
let pendingEmail = '';
let pendingName = '';
let otpCooldownTimer = null;
let otpCooldownSeconds = 0;

// Password Reset state
let resetPendingEmail = '';
let resetCooldownTimer = null;
let resetCooldownSeconds = 0;

const listeners = [];

const el = (id) => document.getElementById(id);

/** Subscribe to auth state changes (login/logout). Returns an unsubscribe fn. */
export function onAuthChange(fn) {
  listeners.push(fn);
  return () => {
    const i = listeners.indexOf(fn);
    if (i >= 0) listeners.splice(i, 1);
  };
}

function notify() {
  listeners.forEach((fn) => fn(currentUser));
}

export function getCurrentUser() {
  return currentUser;
}

function renderHeaderAuth() {
  const container = el('header-auth');
  if (!container) return;

  if (currentUser) {
    const initial = (currentUser.name || currentUser.email || '?')[0].toUpperCase();
    const label = currentUser.name || (currentUser.email ? currentUser.email.split('@')[0] : '');
    container.innerHTML = `
      <div class="flex items-center gap-2">
        <div class="flex items-center gap-2 px-3 py-1.5 rounded-lg" style="background: var(--bay-surface); border: 1px solid var(--bay-border);">
          <div class="w-6 h-6 rounded-md flex items-center justify-center text-xs font-bold" style="background: var(--scope-teal); color: var(--text-primary);">${initial}</div>
          <span class="text-xs font-medium max-w-[100px] truncate hidden sm:block" style="color: var(--text-primary);">${label}</span>
        </div>
        <button type="button" id="header-logout" class="btn-secondary text-xs py-1.5 px-3">Sign out</button>
      </div>
    `;
    el('header-logout').addEventListener('click', () => {
      clearSession();
      currentUser = null;
      renderHeaderAuth();
      notify();
    });
  } else {
    container.innerHTML = `
      <button type="button" id="header-signin" class="btn-secondary text-sm py-2 px-5">Sign in</button>
    `;
    el('header-signin').addEventListener('click', openAuthModal);
  }
}

function setStep(step) {
  const steps = ['credentials', 'otp', 'forgot', 'reset'];
  for (const s of steps) {
    const node = el(`auth-step-${s}`);
    if (!node) continue;
    const isActive = s === step;
    node.classList.toggle('hidden', !isActive);
    if (s !== 'credentials') {
      node.classList.toggle('flex', isActive);
    }
  }

  // Clear notices and focus primary input
  if (step === 'credentials') {
    hideError();
  } else if (step === 'otp') {
    hideOtpError();
    hideOtpSuccess();
    const input = el('otp-input');
    if (input) {
      input.value = '';
      setTimeout(() => input.focus(), 50);
    }
  } else if (step === 'forgot') {
    hideForgotError();
    const input = el('forgot-email');
    if (input) setTimeout(() => input.focus(), 50);
  } else if (step === 'reset') {
    hideResetError();
    hideResetSuccess();
    const input = el('reset-otp-input');
    if (input) {
      input.value = '';
      setTimeout(() => input.focus(), 50);
    }
  }
}

function setMode(newMode) {
  mode = newMode;
  const isLogin = mode === 'login';

  setStep('credentials');

  el('auth-title').textContent = isLogin ? 'Sign in' : 'Create account';
  el('auth-subtitle').textContent = isLogin ? 'Access your Chimera studio' : 'Start rendering videos';
  el('field-name').classList.toggle('hidden', isLogin);
  el('field-confirm').classList.toggle('hidden', isLogin);
  el('auth-name').required = !isLogin;
  el('auth-confirm').required = !isLogin;
  el('auth-submit').textContent = isLogin ? 'Sign in' : 'Send Verification Code';
  el('auth-toggle-text').textContent = isLogin ? "Don't have an account? " : 'Already registered? ';
  el('auth-toggle-mode').textContent = isLogin ? 'Create one' : 'Sign in';

  const forgotLink = el('auth-forgot-link');
  if (forgotLink) forgotLink.classList.toggle('hidden', !isLogin);

  const tabLogin = el('tab-login');
  const tabRegister = el('tab-register');
  for (const [tab, active] of [[tabLogin, isLogin], [tabRegister, !isLogin]]) {
    tab.setAttribute('aria-selected', String(active));
    tab.style.background = active ? 'var(--bay-surface)' : 'transparent';
    tab.style.color = active ? 'var(--text-primary)' : 'var(--text-muted)';
    tab.style.border = active ? '1px solid var(--bay-border)' : '1px solid transparent';
  }

  hideError();
  resetPasswordVisibility();
}

function showError(msg) {
  const box = el('auth-error');
  box.textContent = msg;
  box.classList.remove('hidden');
}

function hideError() {
  const box = el('auth-error');
  box.classList.add('hidden');
  box.textContent = '';
}

function showOtpError(msg) {
  const box = el('otp-error');
  box.textContent = msg;
  box.classList.remove('hidden');
  hideOtpSuccess();
}

function hideOtpError() {
  const box = el('otp-error');
  box.classList.add('hidden');
  box.textContent = '';
}

function showOtpSuccess(msg) {
  const box = el('otp-success');
  box.textContent = msg;
  box.classList.remove('hidden');
  hideOtpError();
}

function hideOtpSuccess() {
  const box = el('otp-success');
  box.classList.add('hidden');
  box.textContent = '';
}

function showForgotError(msg) {
  const box = el('forgot-error');
  box.textContent = msg;
  box.classList.remove('hidden');
}

function hideForgotError() {
  const box = el('forgot-error');
  box.classList.add('hidden');
  box.textContent = '';
}

function showResetError(msg) {
  const box = el('reset-error');
  box.textContent = msg;
  box.classList.remove('hidden');
  hideResetSuccess();
}

function hideResetError() {
  const box = el('reset-error');
  box.classList.add('hidden');
  box.textContent = '';
}

function showResetSuccess(msg) {
  const box = el('reset-success');
  box.textContent = msg;
  box.classList.remove('hidden');
  hideResetError();
}

function hideResetSuccess() {
  const box = el('reset-success');
  box.classList.add('hidden');
  box.textContent = '';
}

function setLoading(isLoading) {
  const btn = el('auth-submit');
  btn.disabled = isLoading;
  if (isLoading) {
    btn.dataset.label = btn.textContent;
    btn.innerHTML = `<span class="flex items-center justify-center gap-2"><span class="spinner"></span>${mode === 'login' ? 'Signing in…' : 'Sending code…'}</span>`;
  } else if (btn.dataset.label) {
    btn.textContent = btn.dataset.label;
  }
}

function setOtpLoading(isLoading) {
  const btn = el('otp-submit');
  if (!btn) return;
  btn.disabled = isLoading;
  if (isLoading) {
    btn.dataset.label = btn.textContent;
    btn.innerHTML = `<span class="flex items-center justify-center gap-2"><span class="spinner"></span>Verifying…</span>`;
  } else if (btn.dataset.label) {
    btn.textContent = btn.dataset.label;
  }
}

function setForgotLoading(isLoading) {
  const btn = el('forgot-submit');
  if (!btn) return;
  btn.disabled = isLoading;
  if (isLoading) {
    btn.dataset.label = btn.textContent;
    btn.innerHTML = `<span class="flex items-center justify-center gap-2"><span class="spinner"></span>Sending code…</span>`;
  } else if (btn.dataset.label) {
    btn.textContent = btn.dataset.label;
  }
}

function setResetLoading(isLoading) {
  const btn = el('reset-submit');
  if (!btn) return;
  btn.disabled = isLoading;
  if (isLoading) {
    btn.dataset.label = btn.textContent;
    btn.innerHTML = `<span class="flex items-center justify-center gap-2"><span class="spinner"></span>Updating password…</span>`;
  } else if (btn.dataset.label) {
    btn.textContent = btn.dataset.label;
  }
}

function startOtpCooldown(seconds = 30) {
  if (otpCooldownTimer) clearInterval(otpCooldownTimer);
  otpCooldownSeconds = seconds;
  const resendBtn = el('otp-resend');

  const update = () => {
    if (!resendBtn) return;
    if (otpCooldownSeconds > 0) {
      resendBtn.disabled = true;
      resendBtn.style.opacity = '0.5';
      resendBtn.style.cursor = 'not-allowed';
      resendBtn.textContent = `Resend in ${otpCooldownSeconds}s`;
      otpCooldownSeconds--;
    } else {
      clearInterval(otpCooldownTimer);
      otpCooldownTimer = null;
      resendBtn.disabled = false;
      resendBtn.style.opacity = '1';
      resendBtn.style.cursor = 'pointer';
      resendBtn.textContent = 'Resend code';
    }
  };

  update();
  otpCooldownTimer = setInterval(update, 1000);
}

function startResetCooldown(seconds = 30) {
  if (resetCooldownTimer) clearInterval(resetCooldownTimer);
  resetCooldownSeconds = seconds;
  const resendBtn = el('reset-resend');

  const update = () => {
    if (!resendBtn) return;
    if (resetCooldownSeconds > 0) {
      resendBtn.disabled = true;
      resendBtn.style.opacity = '0.5';
      resendBtn.style.cursor = 'not-allowed';
      resendBtn.textContent = `Resend in ${resetCooldownSeconds}s`;
      resetCooldownSeconds--;
    } else {
      clearInterval(resetCooldownTimer);
      resetCooldownTimer = null;
      resendBtn.disabled = false;
      resendBtn.style.opacity = '1';
      resendBtn.style.cursor = 'pointer';
      resendBtn.textContent = 'Resend code';
    }
  };

  update();
  resetCooldownTimer = setInterval(update, 1000);
}

function handleKeyDown(e) {
  if (e.key === 'Escape') closeAuthModal();
}

export function openAuthModal() {
  const modal = el('auth-modal');
  modal.classList.remove('hidden');
  modal.classList.add('flex');

  previouslyFocused = document.activeElement;
  document.addEventListener('keydown', handleKeyDown);
  setMode('login');
  el('auth-email').focus();
}

export function closeAuthModal() {
  const modal = el('auth-modal');
  modal.classList.add('hidden');
  modal.classList.remove('flex');
  document.removeEventListener('keydown', handleKeyDown);
  if (otpCooldownTimer) {
    clearInterval(otpCooldownTimer);
    otpCooldownTimer = null;
  }
  if (resetCooldownTimer) {
    clearInterval(resetCooldownTimer);
    resetCooldownTimer = null;
  }
  setStep('credentials');
  if (previouslyFocused && previouslyFocused.focus) previouslyFocused.focus();
}

// ── Submit Handlers ──────────────────────────────────────────

async function handleSubmit(e) {
  e.preventDefault();
  hideError();

  const name = el('auth-name').value.trim();
  const email = el('auth-email').value.trim();
  const password = el('auth-password').value;
  const confirm = el('auth-confirm').value;

  if (mode === 'register') {
    if (password !== confirm) return showError('Passwords do not match.');
    if (password.length < 6) return showError('Password must be at least 6 characters.');
  }

  setLoading(true);
  try {
    if (mode === 'login') {
      currentUser = await login(email, password);
      renderHeaderAuth();
      notify();
      closeAuthModal();
      el('auth-form').reset();
    } else {
      // Register flow: send OTP to verify email
      await sendOtp(name, email, password);
      pendingEmail = email;
      pendingName = name;
      el('otp-target-email').textContent = email;
      setStep('otp');
      startOtpCooldown(30);
    }
  } catch (err) {
    showError(err.message);
  } finally {
    setLoading(false);
  }
}

async function handleOtpSubmit(e) {
  e.preventDefault();
  hideOtpError();

  const otpInput = el('otp-input');
  const otp = otpInput ? otpInput.value.trim() : '';

  if (!otp || otp.length !== 6) {
    return showOtpError('Please enter the 6-digit verification code.');
  }

  setOtpLoading(true);
  try {
    currentUser = await verifyOtp(pendingEmail, otp);
    showOtpSuccess('Email verified! Logging you in…');
    setTimeout(() => {
      renderHeaderAuth();
      notify();
      closeAuthModal();
      el('auth-form').reset();
      if (el('otp-form')) el('otp-form').reset();
    }, 600);
  } catch (err) {
    showOtpError(err.message);
  } finally {
    setOtpLoading(false);
  }
}

async function handleResendOtp(e) {
  if (e) e.preventDefault();
  if (otpCooldownSeconds > 0) return;

  hideOtpError();
  const resendBtn = el('otp-resend');
  if (resendBtn) resendBtn.textContent = 'Sending…';

  try {
    const res = await resendOtp(pendingEmail);
    showOtpSuccess(res.message || 'New verification code sent.');
    startOtpCooldown(30);
  } catch (err) {
    showOtpError(err.message);
    if (resendBtn) resendBtn.textContent = 'Resend code';
  }
}

// ── Forgot Password Handlers ─────────────────────────────────

async function handleForgotSubmit(e) {
  e.preventDefault();
  hideForgotError();

  const emailInput = el('forgot-email');
  const email = emailInput ? emailInput.value.trim() : '';

  if (!email) return showForgotError('Please enter your registered email address.');

  setForgotLoading(true);
  try {
    await forgotPassword(email);
    resetPendingEmail = email;
    el('reset-target-email').textContent = email;
    setStep('reset');
    startResetCooldown(30);
  } catch (err) {
    showForgotError(err.message);
  } finally {
    setForgotLoading(false);
  }
}

async function handleResetSubmit(e) {
  e.preventDefault();
  hideResetError();

  const otpInput = el('reset-otp-input');
  const newPasswordInput = el('reset-new-password');
  const confirmPasswordInput = el('reset-confirm-password');

  const otp = otpInput ? otpInput.value.trim() : '';
  const newPassword = newPasswordInput ? newPasswordInput.value : '';
  const confirmPassword = confirmPasswordInput ? confirmPasswordInput.value : '';

  if (!otp || otp.length !== 6) {
    return showResetError('Please enter the 6-digit reset code.');
  }
  if (newPassword.length < 6) {
    return showResetError('New password must be at least 6 characters.');
  }
  if (newPassword !== confirmPassword) {
    return showResetError('Passwords do not match.');
  }

  setResetLoading(true);
  try {
    const res = await resetPassword(resetPendingEmail, otp, newPassword);
    showResetSuccess('Password updated successfully! Signing you in…');
    currentUser = res.user;
    setTimeout(() => {
      renderHeaderAuth();
      notify();
      closeAuthModal();
      if (el('reset-form')) el('reset-form').reset();
      if (el('forgot-form')) el('forgot-form').reset();
      el('auth-form').reset();
    }, 600);
  } catch (err) {
    showResetError(err.message);
  } finally {
    setResetLoading(false);
  }
}

async function handleResetResend(e) {
  if (e) e.preventDefault();
  if (resetCooldownSeconds > 0) return;

  hideResetError();
  const resendBtn = el('reset-resend');
  if (resendBtn) resendBtn.textContent = 'Sending…';

  try {
    const res = await resendResetOtp(resetPendingEmail);
    showResetSuccess(res.message || 'New reset code sent.');
    startResetCooldown(30);
  } catch (err) {
    showResetError(err.message);
    if (resendBtn) resendBtn.textContent = 'Resend code';
  }
}

function handleBackToDetails(e) {
  if (e) e.preventDefault();
  if (otpCooldownTimer) {
    clearInterval(otpCooldownTimer);
    otpCooldownTimer = null;
  }
  setStep('credentials');
  el('auth-email').focus();
}

function handleBackToSignIn(e) {
  if (e) e.preventDefault();
  if (resetCooldownTimer) {
    clearInterval(resetCooldownTimer);
    resetCooldownTimer = null;
  }
  setMode('login');
  el('auth-email').focus();
}

// ── Password Visibility Toggles ─────────────────────────────

const EYE_CLOSED_SVG = `
  <svg class="w-4 h-4 pointer-events-none" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M 3 9.5 C 6 15, 18 15, 21 9.5"></path>
    <path d="M 4.8 11.2 L 2.2 16"></path>
    <path d="M 9.5 13.5 L 8 18.5"></path>
    <path d="M 14.5 13.5 L 16 18.5"></path>
    <path d="M 19.2 11.2 L 21.8 16"></path>
  </svg>
`;

const EYE_OPEN_SVG = `
  <svg class="w-4 h-4 pointer-events-none" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M 2 12 C 5 5.5, 19 5.5, 22 12 C 19 18.5, 5 18.5, 2 12 Z"></path>
    <circle cx="12" cy="12" r="3.4"></circle>
  </svg>
`;

function setupPasswordToggle(btnId, inputId) {
  const btn = el(btnId);
  const input = el(inputId);
  if (!btn || !input) return;

  btn.addEventListener('click', (e) => {
    e.preventDefault();
    const isShowing = input.type === 'text';
    input.type = isShowing ? 'password' : 'text';
    btn.innerHTML = isShowing ? EYE_CLOSED_SVG : EYE_OPEN_SVG;
    btn.title = isShowing ? 'Show password' : 'Hide password';
    btn.setAttribute('aria-label', isShowing ? 'Show password' : 'Hide password');
    input.focus();
  });
}

function resetPasswordVisibility() {
  const fields = [
    { btnId: 'toggle-password', inputId: 'auth-password' },
    { btnId: 'toggle-confirm', inputId: 'auth-confirm' },
    { btnId: 'toggle-reset-password', inputId: 'reset-new-password' },
    { btnId: 'toggle-reset-confirm', inputId: 'reset-confirm-password' },
  ];
  for (const { btnId, inputId } of fields) {
    const input = el(inputId);
    const btn = el(btnId);
    if (input) input.type = 'password';
    if (btn) {
      btn.innerHTML = EYE_CLOSED_SVG;
      btn.title = 'Show password';
      btn.setAttribute('aria-label', 'Show password');
    }
  }
}

// ── Initialization ──────────────────────────────────────────

export function initAuth() {
  renderHeaderAuth();

  el('auth-backdrop').addEventListener('click', closeAuthModal);
  el('auth-close').addEventListener('click', closeAuthModal);
  el('tab-login').addEventListener('click', () => setMode('login'));
  el('tab-register').addEventListener('click', () => setMode('register'));
  el('auth-toggle-mode').addEventListener('click', () => setMode(mode === 'login' ? 'register' : 'login'));
  el('auth-form').addEventListener('submit', handleSubmit);

  // Registration OTP step
  const otpForm = el('otp-form');
  if (otpForm) otpForm.addEventListener('submit', handleOtpSubmit);

  const otpResend = el('otp-resend');
  if (otpResend) otpResend.addEventListener('click', handleResendOtp);

  const otpBack = el('otp-btn-back');
  if (otpBack) otpBack.addEventListener('click', handleBackToDetails);

  const otpChangeEmail = el('otp-change-email');
  if (otpChangeEmail) otpChangeEmail.addEventListener('click', handleBackToDetails);

  // Forgot password trigger link
  const forgotLink = el('auth-forgot-link');
  if (forgotLink) {
    forgotLink.addEventListener('click', (e) => {
      e.preventDefault();
      const currentEmail = el('auth-email') ? el('auth-email').value.trim() : '';
      if (currentEmail && el('forgot-email')) {
        el('forgot-email').value = currentEmail;
      }
      setStep('forgot');
    });
  }

  // Forgot password step
  const forgotForm = el('forgot-form');
  if (forgotForm) forgotForm.addEventListener('submit', handleForgotSubmit);

  const forgotBack = el('forgot-btn-back');
  if (forgotBack) forgotBack.addEventListener('click', handleBackToSignIn);

  const forgotBackLink = el('forgot-back-link');
  if (forgotBackLink) forgotBackLink.addEventListener('click', handleBackToSignIn);

  // Reset password step
  const resetForm = el('reset-form');
  if (resetForm) resetForm.addEventListener('submit', handleResetSubmit);

  const resetResend = el('reset-resend');
  if (resetResend) resetResend.addEventListener('click', handleResetResend);

  const resetBack = el('reset-btn-back');
  if (resetBack) resetBack.addEventListener('click', handleBackToSignIn);

  const resetBackLink = el('reset-back-link');
  if (resetBackLink) resetBackLink.addEventListener('click', handleBackToSignIn);

  // Auto-clean inputs for 6-digit numeric OTPs
  ['otp-input', 'reset-otp-input'].forEach((id) => {
    const inp = el(id);
    if (inp) {
      inp.addEventListener('input', (e) => {
        e.target.value = e.target.value.replace(/[^0-9]/g, '').slice(0, 6);
      });
    }
  });

  // Password toggle buttons
  setupPasswordToggle('toggle-password', 'auth-password');
  setupPasswordToggle('toggle-confirm', 'auth-confirm');
  setupPasswordToggle('toggle-reset-password', 'reset-new-password');
  setupPasswordToggle('toggle-reset-confirm', 'reset-confirm-password');
}
