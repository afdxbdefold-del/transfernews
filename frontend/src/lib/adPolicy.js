export const NO_AD_PAGES = ['/impressum', '/datenschutz', '/ueber-uns', '/about', '/admin'];
// Only these eight established placements have a built-in provider format.
export const SKYSCRAPER_MIN_WIDTH = 1360;
export const LEGACY_FORMATS = {
  top_banner_above_header: { id: 1, width: 728, height: 90 },
  below_header: { id: 31, width: 970, height: 250 },
  sidebar_top: { id: 3, width: 300, height: 600 },
  sidebar_middle: { id: 2, width: 300, height: 250 },
  sidebar_bottom: { id: 19, width: 300, height: 250 },
  footer_top: { id: 28, width: 728, height: 90 },
  skyscraper: { id: 4, width: 120, height: 0 },
  global: { id: 6, width: 728, height: 0 },
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
  if (slot.slot_key === 'skyscraper' && width < SKYSCRAPER_MIN_WIDTH) return false;
  if (slot.device_type === 'desktop' && width < 1024) return false;
  if (slot.device_type === 'mobile' && width >= 768) return false;
  if (slot.device_type === 'tablet' && (width < 768 || width >= 1024)) return false;
  return hasAdCode(slot) || Boolean(LEGACY_FORMATS[slot.slot_key]);
}
