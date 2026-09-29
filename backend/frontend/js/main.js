import { renderPipelineSection } from './pipeline.js';
import { initAuth } from './auth.js';
import { initStudio } from './studio.js';

function initHeaderScroll() {
  const header = document.getElementById('site-header');
  const onScroll = () => {
    const scrolled = window.scrollY > 20;
    if (scrolled) {
      header.style.background = 'var(--header-bg-scrolled)';
      header.style.borderBottom = '1px solid var(--bay-border-hover)';
      header.style.boxShadow = '0 4px 20px rgba(0,0,0,0.1)';
    } else {
      header.style.background = 'var(--header-bg)';
      header.style.borderBottom = '1px solid var(--bay-border)';
      header.style.boxShadow = 'none';
    }
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
}

function initMobileNav() {
  const toggle = document.getElementById('mobile-nav-toggle');
  const menu = document.getElementById('mobile-nav');

  toggle.addEventListener('click', () => {
    const isOpen = !menu.classList.contains('hidden');
    menu.classList.toggle('hidden');
    toggle.setAttribute('aria-expanded', String(!isOpen));
    toggle.textContent = isOpen ? '☰' : '✕';
  });

  menu.querySelectorAll('a').forEach((link) => {
    link.addEventListener('click', () => {
      menu.classList.add('hidden');
      toggle.setAttribute('aria-expanded', 'false');
      toggle.textContent = '☰';
    });
  });
}
function initTheme() {
  const toggle = document.getElementById('theme-toggle');
  if (!toggle) return;

  const currentTheme = localStorage.getItem('theme') || 'dark';
  document.documentElement.setAttribute('data-theme', currentTheme);
  
  toggle.addEventListener('click', () => {
    const isLight = document.documentElement.getAttribute('data-theme') === 'light';
    const newTheme = isLight ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
  });
}

document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  renderPipelineSection();
  initAuth();
  initStudio();
  initHeaderScroll();
  initMobileNav();

  const yearEl = document.getElementById('footer-year');
  if (yearEl) yearEl.textContent = new Date().getFullYear();
});