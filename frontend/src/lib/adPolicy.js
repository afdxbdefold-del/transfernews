export const NO_AD_PAGES = ['/impressum', '/datenschutz', '/ueber-uns', '/about', '/admin'];
// Active admin slots own the existing inline formats. Missing/disabled slots never render.
export const LEGACY_FORMATS = {
  top_banner_above_header: { id: 1, width: 728, height: 90 },
  below_header: { id: 31, width: 970, height: 250 },
  sidebar_top: { id: 3, width: 300, height: 600 },
  sidebar_middle: { id: 2, width: 300, height: 250 },
  sidebar_bottom: { id: 19, width: 300, height: 250 },
  footer_top: { id: 28, width: 728, height: 90 },
};
export function pageType(path) {
  if (path === '/') return 'homepage';
  const prefixes = {'/news/':'news_detail','/spieler/':'player','/verein/':'club','/wettbewerb/':'competition','/thema/':'topic','/suche':'search','/transfers':'transfers','/geruechte':'rumours'};
  return Object.entries(prefixes).find(([prefix]) => path.startsWith(prefix))?.[1] || 'news_list';
}
export function hasAdCode(slot) {
  return Boolean(slot?.html_code?.trim() || slot?.embed_code?.trim() || slot?.js_code?.trim());
}
export function canShowAd(slot, path, width) {
  if (!slot?.is_active || NO_AD_PAGES.some(p => path === p || path.startsWith(p + '/'))) return false;
  if (slot.page_type && slot.page_type !== 'all' && slot.page_type !== pageType(path)) return false;
  if (LEGACY_FORMATS[slot.slot_key] && width < 1024) return false;
  // Mobile/tablet scripts require an explicitly configured placement. Desktop
  // scripts must never execute inside a CSS-hidden sidebar or mobile viewport.
  if (slot.device_type === 'mobile') return width < 768 && hasAdCode(slot);
  if (slot.device_type === 'tablet') return width >= 768 && width < 1024 && hasAdCode(slot);
  return width >= 1024 && (hasAdCode(slot) || Boolean(LEGACY_FORMATS[slot.slot_key]));
}
