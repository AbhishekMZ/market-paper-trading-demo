import { useEffect, useState } from 'react';

/**
 * Fetch a JSON file from the static data folder.
 *
 * URLs are built from import.meta.env.BASE_URL so the app works both at the
 * site root (dev) and under a GitHub Pages repo subpath (build with base: './').
 *
 * Returns { data, loading, error }. A missing or malformed file never throws to
 * the render tree — callers get error !== null and can show a placeholder.
 *
 * @param {string} file  e.g. "latest_report.json"
 */
export function useData(file) {
  const [state, setState] = useState({ data: null, loading: true, error: null });

  useEffect(() => {
    let cancelled = false;
    setState({ data: null, loading: true, error: null });

    const base = import.meta.env.BASE_URL || '/';
    const url = `${base}data/${file}`;

    fetch(url, { cache: 'no-cache' })
      .then(async (res) => {
        if (!res.ok) {
          throw new Error(`Could not load ${file} (HTTP ${res.status})`);
        }
        try {
          return await res.json();
        } catch {
          throw new Error(`${file} is not valid JSON`);
        }
      })
      .then((data) => {
        if (!cancelled) setState({ data, loading: false, error: null });
      })
      .catch((err) => {
        if (!cancelled) {
          setState({ data: null, loading: false, error: err.message || String(err) });
        }
      });

    return () => {
      cancelled = true;
    };
  }, [file]);

  return state;
}
