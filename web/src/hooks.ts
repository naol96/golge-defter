import { useCallback, useEffect, useRef, useState, useSyncExternalStore } from "react";

export function safeStorage(key: string, value?: string): string | null {
  try {
    if (value === undefined) return localStorage.getItem(key);
    localStorage.setItem(key, value);
  } catch {
    /* Private mode / blocked storage: preferences simply don't persist. */
  }
  return null;
}

export interface PollState<T> {
  data: T | null;
  error: Error | null;
  loading: boolean;
  updatedAt: number | null;
  nextAt: number | null;
  refresh: () => void;
}

/**
 * Polls `load` every `intervalMs` while the tab is visible and `paused` is false.
 * Keeps the last good payload on failure so the UI can mark it stale instead of blanking.
 */
export function usePolling<T>(
  load: (signal: AbortSignal) => Promise<T>,
  intervalMs: number,
  { paused = false, deps = [] as unknown[] } = {},
): PollState<T> {
  const requestKey = JSON.stringify(deps);
  const [dataKey, setDataKey] = useState<string | null>(null);
  const [errorKey, setErrorKey] = useState<string | null>(null);
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [loading, setLoading] = useState(true);
  const [updatedAt, setUpdatedAt] = useState<number | null>(null);
  const [nextAt, setNextAt] = useState<number | null>(null);
  const loadRef = useRef(load);
  loadRef.current = load;
  const ctrlRef = useRef<AbortController | null>(null);
  const timerRef = useRef<number | undefined>(undefined);
  const pausedRef = useRef(paused);
  pausedRef.current = paused;

  const run = useCallback(async () => {
    window.clearTimeout(timerRef.current);
    ctrlRef.current?.abort();
    const ctrl = new AbortController();
    ctrlRef.current = ctrl;
    setLoading(true);
    try {
      const result = await loadRef.current(ctrl.signal);
      if (ctrl.signal.aborted) return;
      setData(result);
      setDataKey(requestKey);
      setError(null);
      setUpdatedAt(Date.now());
    } catch (err) {
      if (ctrl.signal.aborted || (err as Error).name === "AbortError") return;
      setError(err as Error);
      setErrorKey(requestKey);
    } finally {
      if (!ctrl.signal.aborted) {
        setLoading(false);
        if (!pausedRef.current && document.visibilityState === "visible") {
          setNextAt(Date.now() + intervalMs);
          timerRef.current = window.setTimeout(run, intervalMs);
        } else {
          setNextAt(null);
        }
      }
    }
  }, [intervalMs, requestKey]);

  useEffect(() => {
    void run();
    return () => {
      ctrlRef.current?.abort();
      window.clearTimeout(timerRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [run, ...deps]);

  const firstPauseEffect = useRef(true);
  useEffect(() => {
    if (firstPauseEffect.current) {
      firstPauseEffect.current = false;
      return;
    }
    if (paused) {
      window.clearTimeout(timerRef.current);
      setNextAt(null);
    } else {
      void run();
    }
  }, [paused, run]);

  useEffect(() => {
    const onVisible = () => {
      if (document.visibilityState === "visible" && !pausedRef.current) void run();
      else window.clearTimeout(timerRef.current);
    };
    document.addEventListener("visibilitychange", onVisible);
    return () => document.removeEventListener("visibilitychange", onVisible);
  }, [run]);

  const current = dataKey === requestKey;
  return { data: current ? data : null, error: errorKey === requestKey ? error : null,
    loading: loading || (!current && errorKey !== requestKey), updatedAt: current ? updatedAt : null,
    nextAt: current ? nextAt : null, refresh: run };
}

/** Wall clock in epoch seconds, ticking once per second (shared by all subscribers). */
const nowListeners = new Set<() => void>();
let nowValue = Math.floor(Date.now() / 1000);
let nowTimer: number | undefined;
function subscribeNow(cb: () => void) {
  nowListeners.add(cb);
  if (nowTimer === undefined) {
    nowTimer = window.setInterval(() => {
      nowValue = Math.floor(Date.now() / 1000);
      nowListeners.forEach((l) => l());
    }, 1000);
  }
  return () => {
    nowListeners.delete(cb);
    if (!nowListeners.size) {
      window.clearInterval(nowTimer);
      nowTimer = undefined;
    }
  };
}
export function useNow(): number {
  return useSyncExternalStore(subscribeNow, () => nowValue, () => nowValue);
}

export type ThemePref = "system" | "light" | "dark";

export function useTheme(): [ThemePref, (t: ThemePref) => void] {
  const [pref, setPref] = useState<ThemePref>(() => {
    const saved = safeStorage("golge-theme");
    return saved === "light" || saved === "dark" || saved === "system" ? saved : "dark";
  });
  useEffect(() => {
    const root = document.documentElement;
    if (pref === "system") delete root.dataset.theme;
    else root.dataset.theme = pref;
    safeStorage("golge-theme", pref);
  }, [pref]);
  return [pref, setPref];
}

export function useHashRoute<T extends string>(routes: readonly T[], fallback: T): [T, (r: T) => void] {
  const read = () => {
    let raw: string;
    try { raw = decodeURIComponent(window.location.hash.replace(/^#\/?/, "").split("?")[0] ?? ""); }
    catch { return fallback; }
    return (routes as readonly string[]).includes(raw) ? (raw as T) : fallback;
  };
  const [route, setRoute] = useState<T>(read);
  useEffect(() => {
    const onHash = () => setRoute(read());
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  const go = useCallback((r: T) => {
    window.location.hash = `/${r}`;
  }, []);
  return [route, go];
}

/** Single-key shortcuts, ignored while typing in a field or with modifiers held. */
export function useHotkeys(map: Record<string, () => void>) {
  const ref = useRef(map);
  ref.current = map;
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      const el = e.target as HTMLElement | null;
      if (el && (el.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName))) {
        if (e.key === "Escape") el.blur();
        return;
      }
      const fn = ref.current[e.key];
      if (fn) {
        e.preventDefault();
        fn();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);
}

export function useMediaQuery(query: string): boolean {
  return useSyncExternalStore(
    (cb) => {
      const mql = window.matchMedia(query);
      mql.addEventListener("change", cb);
      return () => mql.removeEventListener("change", cb);
    },
    () => window.matchMedia(query).matches,
  );
}
