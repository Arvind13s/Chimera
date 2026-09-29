/**
 * Shared utilities used across modules.
 */

const reducedMotionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');

/** Returns whether the user currently prefers reduced motion. */
export function prefersReducedMotion() {
  return reducedMotionQuery.matches;
}

/** Subscribes to changes in the reduced-motion preference. Returns an unsubscribe fn. */
export function onReducedMotionChange(handler) {
  reducedMotionQuery.addEventListener('change', handler);
  return () => reducedMotionQuery.removeEventListener('change', handler);
}

/** Minimal HTML-escaping for text interpolated into innerHTML. */
export function escapeHTML(str) {
  const div = document.createElement('div');
  div.textContent = str ?? '';
  return div.innerHTML;
}
