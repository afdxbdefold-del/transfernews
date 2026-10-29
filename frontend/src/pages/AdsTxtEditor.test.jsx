import { act } from 'react';
import { createRoot } from 'react-dom/client';
import AdsTxtEditor from './AdsTxtEditor';

jest.mock('react-helmet-async', () => ({ Helmet: () => null }));

let host, root, authenticated, current, history, overrides;
const reply = (data, status = 200) => Promise.resolve({ ok: status < 400, status, json: async () => data });
const version = (revision, content = '# Bestand\nexample.com, existing, DIRECT\n') => ({ revision, content, bytes: content.length, created_at: '2026-10-29T12:00:00Z' });
const buttons = () => [...host.querySelectorAll('button')];
const button = label => buttons().find(item => item.textContent.includes(label));
const requests = path => fetch.mock.calls.filter(([url]) => url === '/api/ads-txt-editor' + path);
const click = async label => act(async () => { button(label).click(); });
const paste = async text => act(async () => {
  const event = new Event('paste', { bubbles: true, cancelable: true });
  Object.defineProperty(event, 'clipboardData', { value: { getData: () => text } });
  host.querySelector('textarea').dispatchEvent(event);
});
const login = async () => {
  await act(async () => {
    const input = host.querySelector('input[type="password"]');
    Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(input, 'offline-test-password');
    input.dispatchEvent(new Event('input', { bubbles: true }));
  });
  await act(async () => { host.querySelector('form').dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })); });
};

beforeEach(() => {
  global.IS_REACT_ACT_ENVIRONMENT = true;
  authenticated = true;
  current = version(4);
  history = [{ revision: 4, action: 'append', added_rows: 1, created_at: current.created_at }, { revision: 3, action: 'seed', created_at: current.created_at }];
  overrides = {};
  global.fetch = jest.fn((url, options) => {
    const path = url.replace('/api/ads-txt-editor', '');
    if (overrides[path]) return overrides[path](options);
    if (path === '/session') return reply({ authenticated, csrf_token: authenticated ? 'authenticated-csrf' : 'anonymous-csrf' });
    if (path === '/login') { authenticated = true; return reply({ authenticated, csrf_token: 'rotated-login-csrf' }); }
    if (path === '/logout') { authenticated = false; return reply({ authenticated }); }
    if (path === '/document') return reply(current);
    if (path === '/history') return reply({ revisions: history });
    if (path === '/revisions/3') return reply(version(3, '# Historischer Stand\n'));
    if (path === '/preview') return reply({ base_revision: current.revision, content: current.content + JSON.parse(options.body).text, appended_text: JSON.parse(options.body).text, added_rows: 1, duplicate_rows: 0, comment_lines: 1, blank_lines: 0, can_apply: true });
    if (path === '/append') { current = version(current.revision + 1, current.content + JSON.parse(options.body).text); return reply(current); }
    if (path === '/rollback') { current = version(current.revision + 1, '# Historischer Stand\n'); return reply(current); }
    throw new Error('Unexpected endpoint: ' + path);
  });
  host = document.createElement('div');
  document.body.appendChild(host);
  root = createRoot(host);
});

afterEach(async () => {
  await act(async () => { root.unmount(); });
  host.remove();
  jest.restoreAllMocks();
  delete global.fetch;
  delete global.IS_REACT_ACT_ENVIRONMENT;
});

test('login rotates in-memory CSRF and preview/append preserve exact pasted text', async () => {
  authenticated = false;
  const storage = jest.spyOn(Storage.prototype, 'setItem');
  await act(async () => { root.render(<AdsTxtEditor />); });
  expect(host.querySelector('input').autocomplete).toBe('current-password');
  await login();
  expect(requests('/login')[0][1].headers['X-CSRF-Token']).toBe('anonymous-csrf');
  expect(JSON.parse(requests('/login')[0][1].body).password).toBe('offline-test-password');
  const raw = '  example.com, seller-42, DIRECT  \r\n# Kommentar mit Leerzeichen  \r\n';
  await paste(raw);
  await click('Änderungen prüfen');
  expect(JSON.parse(requests('/preview')[0][1].body)).toEqual({ text: raw, expected_revision: 4 });
  expect(requests('/preview')[0][1].headers['X-CSRF-Token']).toBe('rotated-login-csrf');
  expect(document.activeElement.id).toBe('preview-title');
  await click('Änderungen veröffentlichen');
  expect(JSON.parse(requests('/append')[0][1].body)).toEqual({ text: raw, expected_revision: 4 });
  expect(host.textContent).toContain('jetzt auf Version 5');
  expect(host.querySelector('textarea').value).toBe('');
  for (const [, options] of fetch.mock.calls) expect(options.credentials).toBe('same-origin');
  expect(storage).not.toHaveBeenCalled();
});

test('a concurrent revision prevents reuse of the preview and keeps the paste on refresh', async () => {
  await act(async () => { root.render(<AdsTxtEditor />); });
  const raw = 'example.com, new-seller, RESELLER\n';
  await paste(raw);
  await click('Änderungen prüfen');
  overrides['/append'] = () => { current = version(5); return reply({ error: 'revision_conflict' }, 409); };
  await click('Änderungen veröffentlichen');
  expect(host.textContent).toContain('zwischenzeitlich geändert');
  expect(button('Änderungen veröffentlichen')).toBeUndefined();
  expect(button('Änderungen prüfen').disabled).toBe(true);
  expect(host.querySelector('textarea').value).toBe(raw);
  await click('Aktuellen Stand laden');
  expect(host.querySelector('textarea').value).toBe(raw);
  await click('Änderungen prüfen');
  expect(JSON.parse(requests('/preview')[1][1].body).expected_revision).toBe(5);
  expect(requests('/append')).toHaveLength(1);
});

test('expired sessions return to login and retain the unsaved text after reauthentication', async () => {
  await act(async () => { root.render(<AdsTxtEditor />); });
  const raw = 'example.com, unsaved, DIRECT\n';
  await paste(raw);
  overrides['/preview'] = () => { authenticated = false; return reply({ error: 'authentication_required' }, 401); };
  await click('Änderungen prüfen');
  expect(host.querySelector('input[type="password"]')).not.toBeNull();
  expect(host.textContent).toContain('Deine Eingabe bleibt erhalten');
  await login();
  expect(host.querySelector('textarea').value).toBe(raw);
  expect(requests('/append')).toHaveLength(0);
});

test('historical versions are read first and rollback needs an explicit dialog confirmation', async () => {
  await act(async () => { root.render(<AdsTxtEditor />); });
  const compare = buttons().find(item => item.textContent.includes('Vergleichen') && !item.disabled);
  compare.focus();
  await act(async () => { compare.click(); });
  expect(host.querySelector('[role="dialog"]')).not.toBeNull();
  expect(host.querySelector('[role="dialog"]').textContent).toContain('Historischer Stand');
  expect(requests('/rollback')).toHaveLength(0);
  expect(document.activeElement.getAttribute('aria-label')).toBe('Vergleich schließen');
  await act(async () => { document.activeElement.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true })); });
  expect(host.querySelector('[role="dialog"]')).toBeNull();
  expect(document.activeElement).toBe(compare);
  await act(async () => { compare.click(); });
  await click('Version 3 wiederherstellen');
  expect(JSON.parse(requests('/rollback')[0][1].body)).toEqual({ target_revision: 3, expected_revision: 4 });
  expect(host.querySelector('[role="dialog"]')).toBeNull();
  expect(host.textContent).toContain('Version 3 wurde als neue Version 5 veröffentlicht');
});

test('invalid rows are explained without enabling publication or interpreting pasted HTML', async () => {
  await act(async () => { root.render(<AdsTxtEditor />); });
  await paste('<script>bad()</script>\n');
  overrides['/preview'] = () => reply({ error: 'invalid_rows', invalid_count: 1, errors: [{ line: 1, code: 'field_count' }] }, 422);
  await click('Änderungen prüfen');
  expect(host.querySelector('textarea').getAttribute('aria-invalid')).toBe('true');
  expect(host.textContent).toContain('drei oder vier durch Kommas getrennte Felder');
  expect(host.querySelector('script')).toBeNull();
  expect(button('Änderungen veröffentlichen')).toBeUndefined();
  expect(requests('/append')).toHaveLength(0);
});

test('editing a checked paste invalidates the previous approval', async () => {
  await act(async () => { root.render(<AdsTxtEditor />); });
  await paste('example.com, first, DIRECT\n');
  await click('Änderungen prüfen');
  expect(button('Änderungen veröffentlichen')).toBeDefined();
  await paste('example.com, another, DIRECT\n');
  expect(button('Änderungen veröffentlichen')).toBeUndefined();
  expect(requests('/append')).toHaveLength(0);
});

test('CSRF renewal requires another explicit check and never automatically publishes', async () => {
  await act(async () => { root.render(<AdsTxtEditor />); });
  await paste('example.com, pending, DIRECT\n');
  overrides['/preview'] = () => reply({ error: 'csrf_failed' }, 403);
  overrides['/session'] = () => reply({ authenticated: true, csrf_token: 'renewed-csrf' });
  await click('Änderungen prüfen');
  expect(host.textContent).toContain('Sicherheitsfreigabe wurde erneuert');
  expect(requests('/preview')).toHaveLength(1);
  expect(requests('/append')).toHaveLength(0);
  delete overrides['/preview'];
  await click('Änderungen prüfen');
  expect(requests('/preview')[1][1].headers['X-CSRF-Token']).toBe('renewed-csrf');
});

test('older versions remain accessible through the server history cursor', async () => {
  overrides['/history'] = () => reply({ revisions: [history[0]], next_before: 4 });
  overrides['/history?before=4'] = () => reply({ revisions: [history[1]], next_before: null });
  await act(async () => { root.render(<AdsTxtEditor />); });
  expect(host.querySelectorAll('tbody tr')).toHaveLength(1);
  await click('Ältere Versionen laden');
  expect(host.querySelectorAll('tbody tr')).toHaveLength(2);
  expect(button('Ältere Versionen laden')).toBeUndefined();
  await act(async () => { buttons().find(item => item.textContent.includes('Vergleichen') && !item.disabled).click(); });
  expect(host.querySelector('[role="dialog"]').textContent).toContain('Version 3 wiederherstellen');
  expect(requests('/rollback')).toHaveLength(0);
});

test('validation reports the full invalid count when the API limits error details', async () => {
  await act(async () => { root.render(<AdsTxtEditor />); });
  await paste('invalid\n');
  overrides['/preview'] = () => reply({ error: 'invalid_rows', invalid_count: 150, errors: [{ line: 1, code: 'field_count' }] }, 422);
  await click('Änderungen prüfen');
  expect(host.textContent).toContain('150 ungültige Zeilen');
  expect(host.textContent).toContain('Angezeigt: 1 von 150 Fehlern');
});

test('a conflicting directive explains why an existing ownership entry cannot be replaced by append', async () => {
  await act(async () => { root.render(<AdsTxtEditor />); });
  await paste('OWNERDOMAIN=another.example\n');
  overrides['/preview'] = () => reply({ error: 'invalid_rows', invalid_count: 1, errors: [{ line: 1, code: 'conflicting_directive' }] }, 422);
  await click('Änderungen prüfen');
  expect(host.textContent).toContain('widerspricht einer bestehenden Zuordnung');
  expect(button('Änderungen veröffentlichen')).toBeUndefined();
  expect(requests('/append')).toHaveLength(0);
});
