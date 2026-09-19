import { useSyncExternalStore } from "react";

function subscribe(onChange: () => void) {
  window.addEventListener("hashchange", onChange);
  window.addEventListener("popstate", onChange);
  return () => {
    window.removeEventListener("hashchange", onChange);
    window.removeEventListener("popstate", onChange);
  };
}

export function viewLink(values: Record<string, string>) {
  return `#${new URLSearchParams(values)}`;
}

export function updateView(values: Record<string, string>) {
  const params = new URLSearchParams(window.location.hash.slice(1));
  for (const [key, value] of Object.entries(values)) params.set(key, value);
  const hash = `#${params}`;
  if (hash === window.location.hash) return;
  window.history.pushState(null, "", hash);
  window.dispatchEvent(new HashChangeEvent("hashchange"));
}

// Fragments work on static hosting without server-side route rewrites.
export function useViewValue(
  key: string,
  fallback: string,
  allowed: readonly string[],
): [string, (value: string) => void] {
  const hash = useSyncExternalStore(subscribe, () => window.location.hash, () => "");
  const requested = new URLSearchParams(hash.slice(1)).get(key);
  const value = requested !== null && allowed.includes(requested) ? requested : fallback;
  return [value, (next) => updateView({ [key]: next })];
}
