'use client';

import { useSyncExternalStore } from 'react';

export type Theme = 'light' | 'dark';

function subscribe(onChange: () => void) {
  const observer = new MutationObserver(onChange);
  observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });
  return () => observer.disconnect();
}

/** Reads the theme the inline script in layout.tsx put on <html>. */
export function useTheme(): Theme {
  return useSyncExternalStore<Theme>(
    subscribe,
    () => (document.documentElement.classList.contains('dark') ? 'dark' : 'light'),
    () => 'dark',
  );
}

export function setTheme(theme: Theme) {
  document.documentElement.classList.toggle('dark', theme === 'dark');
  try { localStorage.setItem('theme', theme); } catch { /* storage may be blocked */ }
}
