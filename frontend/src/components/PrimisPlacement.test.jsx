import { act, StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { FreestarPage, FreestarSlot, PrimisPlacement } from './FreestarAds';
import { consentAllowsPrimis, loadedPrimisPage, PRIMIS_SRC } from '../lib/primis';

let mockLocation, root, host, listeners;
jest.mock('react-router-dom', () => ({ useLocation: () => mockLocation }));
const primisOnly = {
  eventStatus: 'tcloaded', cmpStatus: 'loaded', gdprApplies: true,
  vendor: { consents: { 228: true }, legitimateInterests: { 228: true } },
  purpose: { consents: Object.fromEntries([1, 2, 3, 4, 5, 6].map(p => [p, true])),
             legitimateInterests: { 7: true, 8: true, 10: true } },
};
const freestarOnly = { ...primisOnly, vendor: { consents: { 850: true, 755: true } },
  purpose: { consents: { 1: true, 3: true, 4: true, 10: true } } };
const draw = (pathname, enabled = true) => act(async () => {
  mockLocation = { pathname, search: '' };
  root.render(<StrictMode><FreestarPage enabled={enabled}><PrimisPlacement /><FreestarSlot name="leaderboard_1" /></FreestarPage></StrictMode>);
});
const signal = (data, ok = true) => act(async () => {
  for (const [listenerId, callback] of listeners) callback({ ...data, listenerId }, ok);
});
const tags = () => [...document.body.querySelectorAll('script')].filter(el => el.src === PRIMIS_SRC);

beforeEach(() => {
  global.IS_REACT_ACT_ENVIRONMENT = true;
  host = document.body.appendChild(document.createElement('div'));
  root = createRoot(host);
  listeners = new Map();
  let id = 0;
  window.__tcfapi = (action, version, callback, which) => {
    if (action === 'addEventListener') { listeners.set(++id, callback); callback({ listenerId: id, eventStatus: 'cmpuishown' }, true); }
    if (action === 'removeEventListener') listeners.delete(which);
  };
});
afterEach(async () => {
  await act(async () => root.unmount());
  host.remove();
  document.getElementById('transfernews-freestar-loader')?.remove();
  delete document.documentElement.dataset.transfernewsPrimisPage;
  delete window.__tcfapi;
  delete window.freestar;
});

test('only an affirmative vendor-specific CMP signal can start the exact body tag, once', async () => {
  await draw('/news/first');
  expect(tags()).toHaveLength(0);
  await signal({ ...primisOnly, vendor: {} });
  expect(tags()).toHaveLength(0);
  await signal(primisOnly);
  await signal({ ...primisOnly, eventStatus: 'useractioncomplete' });
  expect(tags()).toHaveLength(1);
  expect(tags()[0].parentNode.id).toBe('transfernews-primis-placement');
  expect(tags()[0].type).toBe('text/javascript');
  expect(tags()[0].getAttribute('language')).toBe('javascript');
  expect(loadedPrimisPage()).toBe('/news/first');
});

test('switching from Freestar to Primis waits for the fresh document', async () => {
  const reset = jest.fn();
  window.addEventListener('transfernews-ad-consent-revoked', reset);
  try {
    await draw('/');
    await signal(freestarOnly);
    expect(window.freestar).toBeDefined();
    await signal(primisOnly);
    await signal({ ...primisOnly, eventStatus: 'useractioncomplete' });
    expect(reset).toHaveBeenCalledTimes(1);
    expect(tags()).toHaveLength(0);
    expect(loadedPrimisPage()).toBeUndefined();
  } finally { window.removeEventListener('transfernews-ad-consent-revoked', reset); }
});

test('Primis works without Freestar permission, and withdrawal requests full provider cleanup', async () => {
  const reset = jest.fn();
  window.addEventListener('transfernews-ad-consent-revoked', reset);
  try {
    await draw('/');
    await signal(primisOnly);
    expect(tags()).toHaveLength(1);
    expect(window.freestar).toBeUndefined();
    await signal({ ...primisOnly, vendor: {}, eventStatus: 'useractioncomplete' });
    expect(tags()).toHaveLength(0);
    expect(reset).toHaveBeenCalledTimes(1);
  } finally { window.removeEventListener('transfernews-ad-consent-revoked', reset); }
});

test.each(['/impressum', '/datenschutz', '/ueber-uns', '/ads-txt-editor', '/admin', '/does-not-exist'])(
  'excluded page %s never mounts Primis', async (path) => {
    await draw(path); await signal(primisOnly);
    expect(tags()).toHaveLength(0); expect(loadedPrimisPage()).toBeUndefined();
  });

test('no requests on empty/loading pages and no start on interim or failed CMP data', async () => {
  await draw('/suche', false); await signal(primisOnly);
  expect(tags()).toHaveLength(0);
  await draw('/suche', true);
  await signal({ ...primisOnly, eventStatus: 'cmpuishown' }); await signal(primisOnly, false);
  expect(tags()).toHaveLength(0);
});

test('checks the Primis vendor choices, purposes and publisher restrictions', () => {
  expect(consentAllowsPrimis(primisOnly, true)).toBe(true);
  expect(consentAllowsPrimis({ ...primisOnly, cmpStatus: 'error' }, true)).toBe(false);
  expect(consentAllowsPrimis({ eventStatus: 'tcloaded', gdprApplies: false }, true)).toBe(true);
  expect(consentAllowsPrimis({ eventStatus: 'tcloaded' }, true)).toBe(false);
  expect(consentAllowsPrimis({ ...primisOnly, vendor: { consents: { 228: true } } }, true)).toBe(false);
  for (const [type, ids] of [['consents', [1,2,3,4,5,6]], ['legitimateInterests',[7,8,10]]]) {
    for (const id of ids) {
      expect(consentAllowsPrimis({ ...primisOnly, purpose: { ...primisOnly.purpose,
        [type]: { ...primisOnly.purpose[type], [id]: false } } }, true)).toBe(false);
    }
  }
  for (const [id, restriction] of [[1,0],[1,2],[7,1]]) {
    expect(consentAllowsPrimis({ ...primisOnly, publisher: { restrictions: { [id]: { 228: restriction } } } }, true)).toBe(false);
  }
});
