import { claimFormats, releaseFormats, cleanPlacement, enforceOverlaySafety, formatIdsForSlot, fitInlineCreative, requiresDocumentNavigation } from './adLifecycle';

afterEach(() => { document.body.replaceChildren(); delete window.tmzrLocalToolbox; });

test('custom copies cannot reserve a second instance of the same provider format', () => {
  const original = {};
  const copy = {};
  const ids = formatIdsForSlot({ embed_code: '<div id="141912-1"></div><script src="https://ads.themoneytizer.com/s/requestform.js?siteId=141912&formatId=1"></script>' });
  expect(ids).toEqual([1]);
  expect(claimFormats(ids, original)).toBe(true);
  expect(claimFormats(ids, copy)).toBe(false);
  releaseFormats(ids, copy);
  expect(claimFormats(ids, copy)).toBe(false);
  releaseFormats(ids, original);
  expect(claimFormats(ids, copy)).toBe(true);
  releaseFormats(ids, copy);
});

test('route cleanup stops owned refresh work and removes only known provider overlays, including late ones', () => {
  const owner = {};
  const disconnect = jest.fn();
  const clear = jest.spyOn(window, 'clearInterval');
  window.tmzrLocalToolbox = { adUnits: { 26328: { queueRefresh: 789 } }, observers: { 26328: { disconnect } } };
  claimFormats([6], owner);
  document.body.innerHTML = '<div id="sas_iframe_fixed_26328"><iframe></iframe></div><iframe id="unrelated"></iframe>';
  releaseFormats([6], owner);
  expect(clear).toHaveBeenCalledWith(789);
  expect(disconnect).toHaveBeenCalled();
  expect(window.tmzrLocalToolbox.adUnits[26328].isClosed).toBe(true);
  expect(document.getElementById('sas_iframe_fixed_26328')).toBeNull();
  document.body.insertAdjacentHTML('beforeend', '<div id="sas_iframe_fixed_26328-1"><iframe></iframe></div>');
  enforceOverlaySafety();
  expect(document.getElementById('sas_iframe_fixed_26328-1')).toBeNull();
  expect(document.getElementById('unrelated')).not.toBeNull();
  clear.mockRestore();
});

test('inline cleanup finds only ad units belonging to the placement', () => {
  const disconnect = jest.fn();
  window.tmzrLocalToolbox = { adUnits: { 26323: { observer: { disconnect } }, 999: { isClosed: false } } };
  const slot = document.createElement('div');
  slot.innerHTML = '<div id="sas_26323"></div>';
  cleanPlacement(slot);
  expect(disconnect).toHaveBeenCalledTimes(1);
  expect(window.tmzrLocalToolbox.adUnits[999].isClosed).toBe(false);
});

test('an oversized desktop creative is scaled fully into mobile width, not cropped', () => {
  const container = document.createElement('div');
  const content = document.createElement('div');
  Object.defineProperty(container, 'clientWidth', { value: 390 });
  Object.defineProperties(content, { scrollWidth: { value: 970 }, offsetWidth: { value: 390 }, offsetHeight: { value: 250 } });
  fitInlineCreative(container, content);
  expect(content.style.transform).toBe(`translateX(0px) scale(${390 / 970})`);
  expect(container.style.height).toBe('101px');
});

test('browser-normalized styles settle without a mutation loop and external changes are repaired', () => {
  const container = document.createElement('div');
  const content = document.createElement('div');
  Object.defineProperty(container, 'clientWidth', { value: 390 });
  Object.defineProperties(content, { scrollWidth: { value: 970 }, offsetWidth: { value: 390 }, offsetHeight: { value: 250 } });
  const originalSet = content.style.setProperty.bind(content.style);
  const writes = jest.spyOn(content.style, 'setProperty').mockImplementation((name, value, priority) => {
    const serialized = name === 'transform-origin' ? 'left top' :
      name === 'transform' ? value.replace(/scale\(([^)]+)\)/, (_, number) => `scale(${Number(number).toFixed(6)})`) : value;
    originalSet(name, serialized, priority);
  });
  fitInlineCreative(container, content);
  expect(writes).toHaveBeenCalledTimes(2);
  for (let i = 0; i < 20; i++) fitInlineCreative(container, content);
  expect(writes).toHaveBeenCalledTimes(2);
  originalSet('transform', 'none');
  fitInlineCreative(container, content);
  expect(writes).toHaveBeenCalledTimes(3);
  writes.mockRestore();
});

test('footer keeps a legitimate 300x250 creative and can be closed while skyrails stay off mobile', () => {
  window.innerWidth = 390;
  window.innerHeight = 844;
  const dismiss = jest.fn();
  const owner = { dismiss };
  claimFormats([6], owner);
  document.body.innerHTML = '<div id="sas_iframe_fixed_26328-1"><iframe></iframe></div><div id="sas_container_26324_left"></div>';
  const node = document.getElementById('sas_iframe_fixed_26328-1');
  Object.defineProperties(node, { offsetWidth: { value: 300 }, scrollWidth: { value: 300 }, offsetHeight: { value: 250 } });
  enforceOverlaySafety();
  expect(node.style.transform).toBe('translateX(-50%) scale(1)');
  expect(node.style.height).toBe('');
  expect(document.getElementById('sas_container_26324_left')).toBeNull();
  document.getElementById('transfernews-close-footer-ad').click();
  expect(dismiss).toHaveBeenCalledTimes(1);
  releaseFormats([6], owner);
});

test('normal internal links reset provider globals with a document navigation; ads, new tabs and anchors retain their behavior', () => {
  const owner = {};
  claimFormats([1], owner);
  const link = document.createElement('a');
  link.href = '/news/article';
  const event = { target: link, button: 0 };
  expect(requiresDocumentNavigation(event)).toBe(link.href);
  expect(requiresDocumentNavigation({ ...event, ctrlKey: true })).toBeNull();
  link.target = '_blank';
  expect(requiresDocumentNavigation(event)).toBeNull();
  link.target = '';
  link.href = '#section';
  expect(requiresDocumentNavigation(event)).toBeNull();
  releaseFormats([1], owner);
});

test('nested footer containers are transformed only once', () => {
  window.innerWidth = 390;
  const owner = {};
  claimFormats([6], owner);
  document.body.innerHTML = '<div id="sas_iframe_fixed_26328_multi"><div id="sas_iframe_fixed_26328"><iframe></iframe></div></div>';
  const outer = document.getElementById('sas_iframe_fixed_26328_multi');
  const inner = document.getElementById('sas_iframe_fixed_26328');
  Object.defineProperties(outer, { offsetWidth: { value: 728 }, scrollWidth: { value: 728 }, offsetHeight: { value: 90 } });
  enforceOverlaySafety();
  expect(outer.style.transform).toBe(`translateX(-50%) scale(${374 / 728})`);
  expect(inner.style.transform).toBe('');
  releaseFormats([6], owner);
});

test('exotic footer cleanup removes its loose body iframe and late containers without touching unrelated iframes', () => {
  const owner = {};
  claimFormats([6], owner);
  document.body.innerHTML = '<div id="sas_26328"><script></script></div><iframe id="sas_relative_creative_26328"></iframe><iframe id="unrelated"></iframe>';
  const loader = document.getElementById('sas_26328');
  enforceOverlaySafety();
  // The active, still ordinary loader is neither removed nor repositioned.
  expect(loader.isConnected).toBe(true);
  expect(loader.style.position).toBe('');
  expect(document.getElementById('sas_relative_creative_26328')).not.toBeNull();
  releaseFormats([6], owner);
  expect(loader.isConnected).toBe(false);
  expect(document.getElementById('sas_relative_creative_26328')).toBeNull();
  document.body.insertAdjacentHTML('beforeend', '<div id="sas_relative_container_26328_1"></div><iframe id="sas_relative_creative_26328"></iframe>');
  enforceOverlaySafety();
  expect(document.getElementById('sas_relative_container_26328_1')).toBeNull();
  expect(document.getElementById('sas_relative_creative_26328')).toBeNull();
  expect(document.getElementById('unrelated')).not.toBeNull();
});

test.each(['sas_26328', 'sas_relative_container_26328_1'])('active exotic overlay %s is bounded only after provider fixes its position', id => {
  window.innerWidth = 390;
  const owner = {};
  claimFormats([6], owner);
  const node = document.createElement('div');
  node.id = id;
  node.innerHTML = '<iframe></iframe>';
  node.style.position = 'fixed';
  Object.defineProperties(node, { offsetWidth: { value: 728 }, scrollWidth: { value: 728 }, offsetHeight: { value: 90 } });
  document.body.appendChild(node);
  enforceOverlaySafety();
  expect(node.style.transform).toBe(`translateX(-50%) scale(${374 / 728})`);
  expect(document.getElementById('transfernews-close-footer-ad')).not.toBeNull();
  releaseFormats([6], owner);
  expect(node.isConnected).toBe(false);
});
