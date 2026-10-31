export function articleSources(article) {
  const primary = article.source_name || article.primary_source || '';
  const seen = new Set([primary.trim().toLocaleLowerCase('de')]);
  const previous = [];
  for (const value of [article.primary_source, ...(article.secondary_sources || [])]) {
    if (typeof value !== 'string' || !value.trim()) continue;
    const key = value.trim().toLocaleLowerCase('de');
    if (!seen.has(key)) { previous.push(value.trim()); seen.add(key); }
  }
  return { primary, previous };
}
