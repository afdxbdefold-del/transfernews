import { act, StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
let mockLocation = { pathname: '/', search: '' };
jest.mock('react-router-dom', () => ({ useLocation: () => mockLocation }));
import { FreestarPage, FreestarSlot, FreestarRails, RemainingContentAds, AdFeed, consentAllowsFreestar } from './FreestarAds';
import { FREESTAR_SLOTS, isAdvertisingPage } from '../lib/freestar';

let host, root, callbacks, navigate;
const granted = { eventStatus: 'tcloaded', gdprApplies: true, listenerId: 1, purpose: { consents: { 1: true, 3: true, 4: true, 10: true } }, vendor: { consents: { 850: true, 755: true } } };

function Page({ enabled = true }) {
  return <FreestarPage enabled={enabled}>
    <FreestarSlot name="leaderboard_1" />
    <AdFeed>{Array.from({ length: 14 }, (_, i) => <p key={i}>Article {i}</p>)}</AdFeed>
    <FreestarSlot name="incontent_4" /><FreestarSlot name="incontent_4" />
    <RemainingContentAds /><FreestarSlot name="leaderboard_2" /><FreestarRails />
  </FreestarPage>;
}
const render = async (path = '/', enabled = true) => act(async () => { mockLocation = { pathname: path, search: '' }; root.render(<StrictMode><Page enabled={enabled} /></StrictMode>); });
const signal = async data => act(async () => callbacks.forEach(callback => callback(data, true)));
const flush = () => { const queue = window.freestar?.queue; while (queue?.length) queue.shift()(); };
const loadProvider = () => {
  const fs = window.freestar;
  fs.newAdSlots = jest.fn(); fs.deleteAdSlots = jest.fn(); fs.trackPageview = jest.fn();
  flush();
};
beforeEach(() => {
  global.IS_REACT_ACT_ENVIRONMENT = true;
  callbacks = [];
  navigate = path => { mockLocation = { pathname: path, search: '' }; root.render(<StrictMode><Page /></StrictMode>); };
  Object.defineProperty(window, 'innerWidth', { value: 1440, configurable: true, writable: true });
  host = document.createElement('div'); document.body.appendChild(host); root = createRoot(host);
  window.__tcfapi = jest.fn((command, version, callback) => {
    if (command === 'addEventListener') callbacks.push(callback);
  });
});
afterEach(async () => {
  await act(async () => root.unmount());
  flush(); host.remove(); document.head.replaceChildren();
  delete window.freestar; delete window.__tcfapi;
});

test('missing or denied consent makes zero network loader and slot requests', async () => {
  await render();
  expect(window.freestar).toBeUndefined();
  await signal({ ...granted, vendor: { consents: { 755: true } } });
  expect(window.freestar).toBeUndefined();
  expect(host.querySelector('[data-freestar-ad]')).toBeNull();
});
test('purpose10 and both required vendors fail closed; non-GDPR requires explicit signal', () => {
  expect(consentAllowsFreestar(granted, true)).toBe(true);
  for (const id of [1, 3, 4, 10]) expect(consentAllowsFreestar({ ...granted, purpose: { consents: { ...granted.purpose.consents, [id]: false } } }, true)).toBe(false);
  for (const id of [850, 755]) expect(consentAllowsFreestar({ ...granted, vendor: { consents: { ...granted.vendor.consents, [id]: false } } }, true)).toBe(false);
  expect(consentAllowsFreestar({ eventStatus: 'tcloaded', gdprApplies: false }, true)).toBe(true);
  expect(consentAllowsFreestar({ eventStatus: 'tcloaded' }, true)).toBe(false);
});
test('all12 exact supplied IDs are owned once despite duplicate and fallback positions', async () => {
  await render(); await signal(granted); loadProvider();
  const ids = [...host.querySelectorAll('[data-freestar-ad]')].map(node => node.id);
  expect(ids.sort()).toEqual(FREESTAR_SLOTS.map(slot => slot.id).sort());
  expect(new Set(ids).size).toBe(12);
  expect(window.freestar.newAdSlots).toHaveBeenCalledTimes(12);
  expect(document.querySelectorAll('#transfernews-freestar-loader')).toHaveLength(1);
  expect(window.freestar.disableAutoTrackPageviews).toBe(true);
  await signal(granted); flush();
  expect(window.freestar.newAdSlots).toHaveBeenCalledTimes(12);
});
test('route changes delete stringIDs before new auctions and reject stale CMP callbacks', async () => {
  await render(); await signal(granted); loadProvider();
  const fs = window.freestar;
  const oldCallbacks = callbacks.slice();
  await act(async () => navigate('/news/another'));
  flush();
  expect(fs.deleteAdSlots).toHaveBeenCalledTimes(12);
  expect(fs.deleteAdSlots.mock.calls.every(([id]) => typeof id === 'string')).toBe(true);
  await act(async () => oldCallbacks.forEach(callback => callback(granted, true)));
  flush(); expect(fs.newAdSlots).toHaveBeenCalledTimes(12);
  await signal(granted); flush();
  expect(fs.newAdSlots).toHaveBeenCalledTimes(24);
  expect(fs.trackPageview).toHaveBeenCalledTimes(1);
});
test('navigation before external loader resolves cancels old queued auctions', async () => {
  await render(); await signal(granted);
  await act(async () => navigate('/impressum'));
  loadProvider();
  expect(window.freestar.newAdSlots).not.toHaveBeenCalled();
  expect(host.querySelector('[data-freestar-ad]')).toBeNull();
});
test('withdrawal deletes all slots and signals full document cleanup', async () => {
  await render(); await signal(granted); loadProvider();
  const revoke = jest.fn(); window.addEventListener('transfernews-ad-consent-revoked', revoke);
  await signal({ ...granted, eventStatus: 'useractioncomplete', purpose: { consents: {} } }); flush();
  expect(window.freestar.deleteAdSlots).toHaveBeenCalledTimes(12);
  expect(revoke).toHaveBeenCalledTimes(1);
  window.removeEventListener('transfernews-ad-consent-revoked', revoke);
});
test('a failed CMP response after consent destroys owned slots', async () => {
  await render(); await signal(granted); loadProvider();
  await act(async () => callbacks.forEach(callback => callback(undefined, false))); flush();
  expect(window.freestar.deleteAdSlots).toHaveBeenCalledTimes(12);
  expect(host.querySelector('[data-freestar-ad]')).toBeNull();
});
test('returning from an excluded route waits for a fresh consent response', async () => {
  await render(); await signal(granted); loadProvider();
  const fs = window.freestar;
  await act(async () => navigate('/datenschutz')); flush();
  await act(async () => navigate('/news/back')); flush();
  expect(fs.newAdSlots).toHaveBeenCalledTimes(12);
  await signal({ ...granted, vendor: { consents: {} } }); flush();
  expect(fs.newAdSlots).toHaveBeenCalledTimes(12);
  expect(fs.trackPageview).not.toHaveBeenCalled();
});
test('mobile retains all tags but does not auction unsupported desktop rails', async () => {
  window.innerWidth = 320;
  await render(); await signal(granted); loadProvider();
  expect(host.querySelectorAll('[data-freestar-ad]')).toHaveLength(12);
  expect(window.freestar.newAdSlots).toHaveBeenCalledTimes(8);
  window.innerWidth = 1000; await act(async () => window.dispatchEvent(new Event('resize'))); flush();
  expect(window.freestar.newAdSlots).toHaveBeenCalledTimes(12);
  window.innerWidth = 990; await act(async () => window.dispatchEvent(new Event('resize'))); flush();
  expect(window.freestar.deleteAdSlots).toHaveBeenCalledTimes(4);
});
test.each(['/impressum', '/datenschutz', '/ueber-uns', '/kontakt', '/admin', '/admin/articles', '/ads-txt-editor', '/missing', '/news/', '/news/a/b'])('excluded%s never installs advertising', async path => {
  await render(path); await signal(granted);
  expect(window.freestar).toBeUndefined();
  expect(host.querySelector('[data-freestar-ad]')).toBeNull();
});
test('error/loading pages at otherwise valid URLs do not load ads', async () => {
  await render('/news/missing', false); await signal(granted);
  expect(window.freestar).toBeUndefined();
});
test('every implemented content route is eligible', () => {
  for (const path of ['/', '/ticker', '/top-deals', '/abloesefrei', '/deadline-day', '/geruechte', '/transfers', '/suche', '/news/article', '/spieler/name', '/verein/name', '/wettbewerb/name', '/thema/name', '/autor/name']) expect(isAdvertisingPage(path)).toBe(true);
});
