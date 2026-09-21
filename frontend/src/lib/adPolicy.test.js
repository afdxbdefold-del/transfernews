import { canShowAd, LEGACY_FORMATS } from './adPolicy';
const active = { slot_key: 'top_banner_above_header', is_active: true, page_type: 'all', device_type: 'all' };
test('all eight unique formats are restored and responsive inline ads run on mobile', () => {
  expect(Object.values(LEGACY_FORMATS).map(format => format.id).sort((a, b) => a - b)).toEqual([1, 2, 3, 4, 6, 19, 28, 31]);
  for (const slot_key of ['top_banner_above_header', 'below_header', 'footer_top', 'global']) {
    for (const width of [390, 768, 1023, 1440]) expect(canShowAd({ ...active, slot_key }, '/', width)).toBe(true);
  }
  for (const width of [390, 767, 1024, 1359]) expect(canShowAd({ ...active, slot_key: 'skyscraper' }, '/', width)).toBe(false);
  expect(canShowAd({ ...active, slot_key: 'skyscraper' }, '/', 1360)).toBe(true);
});

test('existing explicit desktop-only settings and empty unused placeholders are respected', () => {
  expect(canShowAd({ ...active, device_type: 'desktop' }, '/', 390)).toBe(false);
  expect(canShowAd({ ...active, slot_key: 'mobile_banner' }, '/', 390)).toBe(false);
});
test('disabling a configured slot disables its built-in format', () => {
  expect(canShowAd({ ...active, is_active: false }, '/', 1440)).toBe(false);
  expect(canShowAd(undefined, '/', 1440)).toBe(false);
});
test('admin and legal pages never load ad scripts', () => {
  for (const path of ['/admin', '/admin/articles', '/datenschutz', '/impressum']) expect(canShowAd(active, path, 1440)).toBe(false);
});
test('custom slots respect page and explicit device configuration', () => {
  const mobile = { ...active, slot_key: 'mobile_sticky_bottom', device_type: 'mobile', embed_code: '<div>mobile</div>', page_type: 'news_detail' };
  expect(canShowAd(mobile, '/news/article', 390)).toBe(true);
  expect(canShowAd(mobile, '/', 390)).toBe(false);
  expect(canShowAd(mobile, '/news/article', 1440)).toBe(false);
  expect(canShowAd({ ...mobile, embed_code: '' }, '/news/article', 390)).toBe(false);
});
