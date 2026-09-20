import { canShowAd, LEGACY_FORMATS } from './adPolicy';
const active = { slot_key: 'top_banner_above_header', is_active: true, page_type: 'all', device_type: 'all' };
test('desktop formats do not run at mobile/tablet widths, regardless of CSS', () => {
  for (const slot_key of Object.keys(LEGACY_FORMATS)) {
    for (const width of [390, 767, 768, 1023]) expect(canShowAd({ ...active, slot_key }, '/', width)).toBe(false);
    expect(canShowAd({ ...active, slot_key }, '/', 1440)).toBe(true);
  }
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
