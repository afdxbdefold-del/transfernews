import { useCallback, useEffect, useRef, useState } from 'react';

function mergeArticles(existing, incoming) {
  const ids = new Set();
  const slugs = new Set();
  return [...existing, ...incoming].filter(article => {
    const duplicate = (article.id && ids.has(article.id)) ||
      (article.slug && slugs.has(article.slug));
    if (article.id) ids.add(article.id);
    if (article.slug) slugs.add(article.slug);
    return !duplicate;
  });
}

export function useArticlePagination(fetchPage, limit = 30) {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState('');
  const [hasMore, setHasMore] = useState(true);
  const request = useRef({ version: 0, inFlight: false, offset: 0, hasMore: true });

  useEffect(() => () => {
    // Ignore responses from an earlier mount or a superseded reload.
    request.current.version += 1;
    request.current.inFlight = false;
  }, []);

  const requestPage = useCallback(async (reset) => {
    const cursor = request.current;
    if (!reset && (cursor.inFlight || !cursor.hasMore)) return;
    const version = ++cursor.version;
    const skip = reset ? 0 : cursor.offset;
    cursor.inFlight = true;
    if (reset) {
      setLoading(true);
      setLoadingMore(false);
      setError('');
    } else {
      setLoadingMore(true);
    }
    try {
      const response = await fetchPage({ skip, limit });
      if (version !== cursor.version) return;
      const data = Array.isArray(response.data) ? response.data : [];
      // Advance by rows consumed from the API, including hidden duplicates.
      cursor.offset = skip + data.length;
      cursor.hasMore = data.length === limit;
      setArticles(previous => mergeArticles(reset ? [] : previous, data));
      setHasMore(cursor.hasMore);
    } catch (failure) {
      if (version !== cursor.version) return;
      if (reset) setError('Die Nachrichten konnten gerade nicht geladen werden.');
      else console.error('Load more error:', failure);
    } finally {
      if (version === cursor.version) {
        cursor.inFlight = false;
        setLoading(false);
        setLoadingMore(false);
      }
    }
  }, [fetchPage, limit]);

  const reload = useCallback(() => requestPage(true), [requestPage]);
  const loadMore = useCallback(() => requestPage(false), [requestPage]);
  return { articles, loading, loadingMore, error, hasMore, reload, loadMore };
}
