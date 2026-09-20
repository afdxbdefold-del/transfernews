export function safeRelatedLink(link) {
  const prefix = { player: '/spieler/', club: '/verein/' }[link?.type];
  if (!prefix || typeof link.url !== 'string' || !link.url.startsWith(prefix)) return '';
  try {
    const slug = decodeURIComponent(link.url.slice(prefix.length).replace(/\/$/, ''));
    return /^[\p{L}\p{N}_-]+$/u.test(slug) ? prefix + encodeURIComponent(slug) : '';
  } catch { return ''; }
}
