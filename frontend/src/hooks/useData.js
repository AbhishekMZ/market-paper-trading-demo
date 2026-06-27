import { useEffect, useState } from 'react';

/**
 * Fetch a JSON file from the static data folder, then keep it fresh.
 *
 * URLs are built from import.meta.env.BASE_URL so the app works both at the
 * site root (dev) and under a GitHub Pages repo subpath (build with base: './').
 *
 * The data is regenerated server-side a few times each weekday (the analyze
 * workflow commits new JSON and Pages redeploys). To stop an open tab from
 * sitting on a stale first paint, this hook re-fetches on an interval and
 * whenever the tab regains focus. Background refreshes update silently: they
 * never show the loading placeholder and never blank the view on a transient
 * failure (e.g. a 404 mid-redeploy) — the last good data stays on screen.
 *
 * Returns { data, loading, error }. A missing or malformed file never throws to
 * the render tree — callers get error !== null and can show a placeholder.
 *
 * @param {string} file  e.g. "latest_report.json"
 */
const POLL_INTERVAL_MS = 60_000; // re-fetch every 60s so an open tab picks up redeploys

export function useData(file) {
  const [state, setState] = useState({ data: null, loading: true, error: null });

  useEffect(() => {
    let cancelled = false;

    const base = import.meta.env.BASE_URL || '/';
    const url = `${base}data/${file}`;

    // initial=true shows the loading placeholder and surfaces load errors.
    // Background refreshes (initial=false) update data in place and keep the
    // last good data when a request fails, instead of flashing an error.
    async function load(initial) {
      if (initial && !cancelled) {
        setState({ data: null, loading: true, error: null });
      }
      try {
        const res = await fetch(url, { cache: 'no-cache' });
        if (!res.ok) {
          throw new Error(`Could not load ${file} (HTTP ${res.status})`);
        }
        let data;
        try {
          data = await res.json();
        } catch {
          throw new Error(`${file} is not valid JSON`);
        }
        if (!cancelled) setState({ data, loading: false, error: null });
      } catch (err) {
        if (cancelled) return;
        const message = err.message || String(err);
        // Surface the error only on the first load (or if we never got data).
        // A failed background refresh keeps whatever is already on screen.
        setState((prev) =>
          initial || prev.data == null
            ? { data: prev.data, loading: false, error: message }
            : prev
        );
      }
    }

    load(true);

    const timer = setInterval(() => load(false), POLL_INTERVAL_MS);

    const onVisible = () => {
      if (document.visibilityState === 'visible') load(false);
    };
    document.addEventListener('visibilitychange', onVisible);

    return () => {
      cancelled = true;
      clearInterval(timer);
      document.removeEventListener('visibilitychange', onVisible);
    };
  }, [file]);

  return state;
}
