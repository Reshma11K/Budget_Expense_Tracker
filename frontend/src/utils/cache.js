export function bumpCacheVersion() {
  const v = Number(localStorage.getItem("cache_version") || 0);
  localStorage.setItem("cache_version", v + 1);
}

export function getCacheVersion() {
  return Number(localStorage.getItem("cache_version") || 0);
}