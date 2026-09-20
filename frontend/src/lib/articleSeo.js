export const SITE_URL = 'https://transfernews.de';
export function absoluteImageUrl(value) {
  if (!value) return '';
  try {
    const url = new URL(value, SITE_URL + '/');
    return ['https:', 'http:'].includes(url.protocol) ? url.href : '';
  } catch { return ''; }
}
export function articleImage(article) {
  return [article.og_image, article.hero_image, article.feature_image].map(absoluteImageUrl).find(Boolean) || '';
}
export function articleAuthorPath(article) {
  return '/autor/' + encodeURIComponent(article.author_slug || 'redaktion');
}
export function articleHasNamedAuthor(article) {
  return Boolean(article.author_slug && article.author_slug !== 'redaktion');
}
export function articleAuthorName(article) {
  return articleHasNamedAuthor(article) ? (article.author_name || 'Redaktion') : 'Redaktion';
}
export function articleCanonical(slug) {
  return SITE_URL + '/news/' + encodeURIComponent(slug);
}
