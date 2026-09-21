import { act, useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import { useArticlePagination } from './useArticlePagination';

test('overlapping pages display each article once and still load the remaining raw page', async () => {
  global.IS_REACT_ACT_ENVIRONMENT = true;
  const article = id => ({ id: String(id), slug: `article-${id}`, title: `News ${id}` });
  const range = (start, end) => Array.from({ length: end - start + 1 }, (_, i) => article(start + i));
  let finishSecondPage;
  const fetchPage = jest.fn(({ skip }) => {
    if (skip === 0) return Promise.resolve({ data: range(1, 30) });
    if (skip === 30) return new Promise(resolve => { finishSecondPage = resolve; });
    if (skip === 60) return Promise.resolve({ data: range(59, 63) });
    throw new Error(`Unexpected offset ${skip}`);
  });
  function NewsList() {
    const { articles, reload, loadMore, hasMore } = useArticlePagination(fetchPage);
    useEffect(() => { reload(); }, [reload]);
    return <>
      {articles.map(item => <a key={item.id} href={`/news/${item.slug}`}>{item.title}</a>)}
      {hasMore && <button onClick={loadMore}>Mehr</button>}
    </>;
  }
  const container = document.createElement('div');
  const root = createRoot(container);
  try {
    await act(async () => { root.render(<NewsList />); });
    await act(async () => {
      container.querySelector('button').click();
      container.querySelector('button').click();
    });
    expect(fetchPage).toHaveBeenCalledTimes(2);
    await act(async () => {
      finishSecondPage({ data: [article(30), { ...article(29), id: 'duplicate-slug' }, ...range(31, 58)] });
    });
    expect(container.querySelectorAll('a')).toHaveLength(58);
    await act(async () => { container.querySelector('button').click(); });
    expect(Array.from(container.querySelectorAll('a'), link => link.textContent))
      .toEqual(range(1, 63).map(item => item.title));
    expect(fetchPage.mock.calls.map(([params]) => params.skip)).toEqual([0, 30, 60]);
    expect(container.querySelector('button')).toBeNull();
  } finally {
    await act(async () => { root.unmount(); });
    delete global.IS_REACT_ACT_ENVIRONMENT;
  }
});
