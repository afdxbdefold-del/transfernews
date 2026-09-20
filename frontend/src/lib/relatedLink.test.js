import { safeRelatedLink } from './relatedLink';
test('related links stay on their declared public profile route', () => {
  expect(safeRelatedLink({type: 'player', url: '/spieler/florian-wirtz'})).toBe('/spieler/florian-wirtz');
  expect(safeRelatedLink({type: 'club', url: '/verein/1-fc-k%C3%B6ln/'})).toBe('/verein/1-fc-k%C3%B6ln');
  for (const url of ['//example.com', '/\\example.com', 'javascript:alert(1)', '/spieler/%5cexample.com', '/spieler/../../admin', '/verein/club']) {
    expect(safeRelatedLink({type: 'player', url})).toBe('');
  }
});
