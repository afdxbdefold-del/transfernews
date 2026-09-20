import { absoluteImageUrl, articleImage, articleAuthorPath, articleCanonical, articleAuthorName } from './articleSeo';
test('hero-only articles retain the actual image in structured data', () => {
  expect(articleImage({ hero_image: 'https://images.example/image.jpg', feature_image: null })).toBe('https://images.example/image.jpg');
});
test('absolute image URLs are not prefixed twice; relative URLs resolve to production', () => {
  expect(absoluteImageUrl('https://images.example/image.jpg')).toBe('https://images.example/image.jpg');
  expect(absoluteImageUrl('/images/photo.jpg')).toBe('https://transfernews.de/images/photo.jpg');
  expect(absoluteImageUrl('javascript:alert(1)')).toBe('');
  expect(articleImage({ og_image: 'javascript:bad', hero_image: '/hero.jpg' })).toBe('https://transfernews.de/hero.jpg');
});
test('public author links use the slug, never an internal author ID', () => {
  expect(articleAuthorPath({ author_id: 'anna-schmidt' })).toBe('/autor/redaktion');
  expect(articleAuthorPath({ author_id: 'uuid', author_slug: 'anna-schmidt' })).toBe('/autor/anna-schmidt');
  expect(articleAuthorName({ author_name: 'Unknown', author_id: 'uuid' })).toBe('Redaktion');
  expect(articleAuthorName({ author_name: 'Unknown', author_slug: 'redaktion' })).toBe('Redaktion');
  expect(articleAuthorName({ author_name: 'Anna', author_slug: 'anna-schmidt' })).toBe('Anna');
});
test('canonical article URLs ignore preview hosts and query parameters', () => {
  expect(articleCanonical('transfer-news')).toBe('https://transfernews.de/news/transfer-news');
});
