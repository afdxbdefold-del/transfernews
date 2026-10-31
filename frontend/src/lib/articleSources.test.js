import { articleSources } from './articleSources';
test('current article source takes precedence over the historical story source', () => {
  expect(articleSources({ source_name: 'Foot Mercato', primary_source: 'Gazzetta dello Sport', secondary_sources: ['Foot Mercato', 'Gazzetta dello Sport', 'gazzetta dello sport'] })).toEqual({ primary: 'Foot Mercato', previous: ['Gazzetta dello Sport'] });
});
test('exact live Pulisic record keeps the distinct historical primary in previous sources', () => {
  expect(articleSources({ source_name: 'Foot Mercato', primary_source: 'Gazzetta dello Sport', secondary_sources: ['Foot Mercato'] })).toEqual({ primary: 'Foot Mercato', previous: ['Gazzetta dello Sport'] });
});
test('old articles retain historical primary when no current source is present', () => {
  expect(articleSources({ primary_source: 'BBC Sport', secondary_sources: [' BBC Sport ', '', null] })).toEqual({ primary: 'BBC Sport', previous: [] });
});
