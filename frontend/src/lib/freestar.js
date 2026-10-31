export const FREESTAR_SLOTS = [
  ...Array.from({ length: 6 }, (_, i) => ({ key: `incontent_${i + 1}`, sizes: '__336x280 __336x280', width: 336, height: 302 })),
  ...Array.from({ length: 2 }, (_, i) => ({ key: `leaderboard_${i + 1}`, sizes: '__320x100 __970x250', width: 970, height: 272 })),
  ...Array.from({ length: 4 }, (_, i) => ({ key: `siderail_${i + 1}`, sizes: '__160x600', width: 160, height: 622 })),
].map(slot => ({ ...slot, id: `transfernews.de_${slot.key}_33357` }));

// Positive route list: new administrative/legal routes cannot inherit ads.
export function isAdvertisingPage(pathname) {
  const path = pathname.replace(/\/+$/, '') || '/';
  return ['/', '/ticker', '/top-deals', '/abloesefrei', '/deadline-day', '/geruechte', '/transfers', '/suche'].includes(path)
    || /^\/(news|spieler|verein|wettbewerb|thema|autor)\/[^/]+$/.test(path);
}

export function ensureFreestar() {
  const fs = window.freestar = window.freestar || {};
  fs.queue = fs.queue || [];
  fs.config = fs.config || {};
  // The provider's history hook otherwise runs before our excluded-route and
  // consent checks. Pageviews are explicitly issued by FreestarPage instead.
  fs.disableAutoTrackPageviews = true;
  // React owns lifecycle; never also register the static-tag initCallback path.
  fs.config.enabled_slots = fs.config.enabled_slots || [];
  fs.transfernewsPage = fs.transfernewsPage || window.location.pathname + window.location.search;
  if (!document.getElementById('transfernews-freestar-loader')) {
    for (const href of ['https://a.pub.network/', 'https://d.pub.network/', 'https://btloader.com/', 'https://api.btloader.com/']) {
      const link = document.createElement('link');
      link.rel = 'preconnect'; link.href = href; link.crossOrigin = 'anonymous';
      document.head.appendChild(link);
    }
    const css = document.createElement('link');
    css.rel = 'stylesheet'; css.href = 'https://a.pub.network/transfernews-de/cls.css';
    document.head.appendChild(css);
    const script = document.createElement('script');
    script.id = 'transfernews-freestar-loader'; script.async = true;
    script.dataset.cfasync = 'false'; script.src = 'https://a.pub.network/transfernews-de/pubfig.min.js';
    document.head.appendChild(script);
  }
  return fs;
}

export function mountFreestarSlot(slot, element) {
  const fs = ensureFreestar();
  let disposed = false;
  let requested = false;
  fs.queue.push(() => {
    if (disposed || !element.isConnected) return;
    requested = true;
    fs.newAdSlots([{ placementName: slot.id, slotId: slot.id }]);
  });
  return () => {
    disposed = true;
    if (requested) fs.queue.push(() => fs.deleteAdSlots(slot.id));
  };
}

// Multiple legacy insertion points can name the same placement. Prefer the
// content placement to the footer fallback, with exactly one actual DOM ID.
export function createPlacementRegistry() {
  const entries = new Map();
  const listeners = new Set();
  const notify = () => listeners.forEach(listener => listener());
  return {
    subscribe(listener) { listeners.add(listener); return () => listeners.delete(listener); },
    owner(key) {
      let chosen;
      for (const [owner, entry] of entries) if (entry.key === key && (!chosen || entry.priority > chosen.priority)) chosen = { owner, ...entry };
      return chosen?.owner;
    },
    register(owner, key, priority) {
      entries.set(owner, { key, priority }); notify();
      return () => { entries.delete(owner); notify(); };
    },
  };
}
