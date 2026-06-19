import { useCallback, useEffect, useState } from 'react';

const STORAGE_KEY = 'volcano-gallery-theme';

function getPreferredColorScheme() {
  return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
}

function parsePreference(stored) {
  if (stored === 'light' || stored === 'dark') {
    return stored;
  }
  return 'auto';
}

function getStoredPreference() {
  if (typeof localStorage === 'undefined') {
    return 'auto';
  }
  return parsePreference(localStorage.getItem(STORAGE_KEY));
}

function resolveTheme(preference) {
  if (preference === 'auto') {
    return getPreferredColorScheme();
  }
  return preference;
}

function applyTheme(preference) {
  const effective = resolveTheme(preference);
  document.documentElement.dataset.theme = effective;
  return effective;
}

export function useTheme() {
  const [preference, setPreference] = useState(getStoredPreference);
  const [resolvedTheme, setResolvedTheme] = useState(() => applyTheme(getStoredPreference()));

  useEffect(() => {
    const effective = applyTheme(preference);
    setResolvedTheme(effective);

    if (preference === 'auto') {
      localStorage.removeItem(STORAGE_KEY);
    } else {
      localStorage.setItem(STORAGE_KEY, preference);
    }
  }, [preference]);

  useEffect(() => {
    if (preference !== 'auto') {
      return undefined;
    }

    const media = window.matchMedia('(prefers-color-scheme: light)');
    function handleChange() {
      const effective = applyTheme('auto');
      setResolvedTheme(effective);
    }

    media.addEventListener('change', handleChange);
    return () => media.removeEventListener('change', handleChange);
  }, [preference]);

  const toggleTheme = useCallback(() => {
    const effective = document.documentElement.dataset.theme;
    if (effective === 'dark') {
      setPreference('light');
    } else if (effective === 'light') {
      setPreference('dark');
    } else {
      setPreference('auto');
    }
  }, []);

  return { preference, resolvedTheme, toggleTheme };
}
