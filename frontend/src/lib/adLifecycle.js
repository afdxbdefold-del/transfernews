import { SKYSCRAPER_MIN_WIDTH } from './adPolicy';

// Document-wide ownership also covers separate React trees and custom admin tags.
const owners = new Map();
const listeners = new Set();
const SKY_IDS = ['sas_container_26324_left', 'sas_container_26324_right'];
const FOOTER_IDS = ['sas_iframe_fixed_26328', 'sas_iframe_fixed_26328-1', 'sas_iframe_fixed_26328_multi', 'msna-ad'];
// setupExoticFS uses the normal loader as an overlay only after fixing its
// position, and also appends a separate creative iframe directly to <body>.
const EXOTIC_FOOTER_IDS = ['sas_26328', 'sas_relative_container_26328_1'];
const FOOTER_CLEANUP_IDS = [...FOOTER_IDS, ...EXOTIC_FOOTER_IDS, 'sas_relative_creative_26328'];
const CLOSE_ID = 'transfernews-close-footer-ad';
const SMART_IDS = { 4: 26324, 6: 26328 };
const equativFooterContainers = new Map();

function equativFooterRoots() {
  // The creative suffix changes. Establish ownership through this format's
  // exact iframe ID, never through a generic Equativ wrapper selector alone.
  document.querySelectorAll('iframe[id="sas_26328_iframe"]').forEach(iframe => {
    const fixed = iframe.closest('[id^="sas_fixedDiv_"]');
    const creativeId = fixed?.id.match(/^sas_fixedDiv_(\d+)$/)?.[1];
    if (!creativeId || getComputedStyle(fixed).position !== 'fixed') return;
    const container = fixed.closest(`[id="sas-container_${creativeId}"]`);
    equativFooterContainers.set(fixed, container || fixed);
  });
  for (const [fixed, container] of equativFooterContainers) {
    if (!fixed.isConnected && !container.isConnected) equativFooterContainers.delete(fixed);
  }
  return [...equativFooterContainers.keys()].filter(node => node.isConnected);
}

function cleanFooter() {
  // Discover late renders too; remembered containers still belong to us if a
  // native close already removed their identifying iframe.
  equativFooterRoots();
  equativFooterContainers.forEach(container => container.remove());
  equativFooterContainers.clear();
  removeNodes([...FOOTER_CLEANUP_IDS, 'tmzr_footer_slidein_css', CLOSE_ID]);
}

export function formatIdsForSlot(slot, format) {
  const ids = new Set(format ? [format.id] : []);
  const code = [slot?.html_code, slot?.embed_code, slot?.js_code].filter(Boolean).join('\n');
  for (const match of code.matchAll(/141912-(\d+)\b|(?:formatId=|gen\.js\?type=)(\d+)\b/g)) {
    ids.add(Number(match[1] || match[2]));
  }
  return [...ids];
}

function removeNodes(ids) {
  ids.forEach(id => document.getElementById(id)?.remove());
}

function cleanFormat(id) {
  if (id === 4) {
    removeNodes(SKY_IDS);
    const toolbox = window.tmzrToolbox;
    if (toolbox?._skyrailDisplayNoneInterval) {
      clearInterval(toolbox._skyrailDisplayNoneInterval);
      toolbox._skyrailDisplayNoneInterval = null;
    }
  }
  if (id === 6) cleanFooter();
  const unit = window.tmzrLocalToolbox?.adUnits?.[SMART_IDS[id]];
  stopUnit(unit, SMART_IDS[id]);
  // These are the secondary loaders injected into <head> by requestform.js.
  document.head.querySelectorAll('script[src]').forEach(script => {
    try {
      const url = new URL(script.src);
      if (url.hostname === 'ads.themoneytizer.com' && url.searchParams.get('siteId') === '141912' && Number(url.searchParams.get('formatId')) === id) script.remove();
    } catch { /* An unrelated non-URL script is not ours. */ }
  });
}

function stopUnit(unit, id) {
  window.tmzrLocalToolbox?.observers?.[id]?.disconnect?.();
  if (!unit) return;
  unit.isClosed = true;
  if (unit.queueRefresh) clearInterval(unit.queueRefresh);
  unit.observer?.disconnect?.();
}

export function cleanPlacement(container) {
  container.querySelectorAll('[id^="sas_"]').forEach(node => {
    const id = node.id.match(/^sas_(?:iframe_)?(\d+)$/)?.[1];
    if (id) stopUnit(window.tmzrLocalToolbox?.adUnits?.[id], id);
  });
}

export function requiresDocumentNavigation(event) {
  if (!owners.size || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return null;
  const link = event.target.closest?.('a[href]');
  if (!link || link.hasAttribute('download') || (link.target && link.target !== '_self') || link.closest('.managed-ad-slot')) return null;
  const url = new URL(link.href, window.location.href);
  return url.origin === window.location.origin && (url.pathname !== window.location.pathname || url.search !== window.location.search) ? url.href : null;
}

export function claimFormats(ids, owner) {
  if (ids.some(id => owners.has(id) && owners.get(id) !== owner)) return false;
  ids.forEach(id => {
    owners.set(id, owner);
    const unit = window.tmzrLocalToolbox?.adUnits?.[SMART_IDS[id]];
    if (unit) unit.isClosed = false;
  });
  listeners.forEach(fn => fn());
  return true;
}

export function releaseFormats(ids, owner) {
  ids.forEach(id => {
    if (owners.get(id) !== owner) return;
    owners.delete(id);
    cleanFormat(id);
  });
  listeners.forEach(fn => fn());
}

const styleWrites = new WeakMap();
function setStyle(node, property, value) {
  let properties = styleWrites.get(node);
  if (!properties) { properties = new Map(); styleWrites.set(node, properties); }
  const previous = properties.get(property);
  const current = node.style.getPropertyValue(property);
  const priority = node.style.getPropertyPriority(property);
  // CSSOM may reorder origins or round transform values. Compare with the
  // browser's last serialization so our mutation observer can reach a rest.
  if (previous?.requested === value && previous.serialized === current && priority === 'important') return;
  if (current !== value || priority !== 'important') node.style.setProperty(property, value, 'important');
  properties.set(property, { requested: value, serialized: node.style.getPropertyValue(property) });
}

export function fitInlineCreative(container, content) {
  const available = container.clientWidth || container.getBoundingClientRect().width;
  const natural = Math.max(content.scrollWidth, content.offsetWidth);
  if (!available || !natural) return;
  const scale = Math.min(1, available / natural);
  const left = Math.max(0, (available - natural * scale) / 2);
  setStyle(content, 'transform-origin', 'top left');
  setStyle(content, 'transform', `translateX(${left}px) scale(${scale})`);
  setStyle(container, 'height', `${Math.ceil(content.offsetHeight * scale)}px`);
}

// Only provider IDs verified in the site's own current integration are touched.
// No CMP, third-party iframe, or unrelated fixed element is removed.
export function enforceOverlaySafety() {
  if (!owners.has(4) || window.innerWidth < SKYSCRAPER_MIN_WIDTH) removeNodes(SKY_IDS);
  for (const id of SKY_IDS) {
    const node = document.getElementById(id);
    if (!node) continue;
    setStyle(node, 'top', '90px');
    setStyle(node, 'z-index', '30');
  }
  if (!owners.has(6)) {
    cleanFooter();
    return;
  }
  let visible = false;
  let maxHeight = 0;
  const overlayIds = [...FOOTER_IDS, ...EXOTIC_FOOTER_IDS.filter(id => {
    const node = document.getElementById(id);
    return node && getComputedStyle(node).position === 'fixed';
  })];
  const overlays = [...overlayIds.map(id => document.getElementById(id)).filter(Boolean), ...equativFooterRoots()];
  for (const node of overlays) {
    if (!node || !node.childElementCount || getComputedStyle(node).display === 'none') continue;
    if (overlays.some(parent => parent !== node && parent.contains(node))) continue;
    visible = true;
    const width = Math.max(node.offsetWidth, node.scrollWidth, 1);
    const scale = Math.min(1, (window.innerWidth - 16) / width);
    const height = node.offsetHeight;
    maxHeight = Math.max(maxHeight, height * scale);
    // Scale the full creative, rather than crop a desktop ad on a narrow screen.
    setStyle(node, 'position', 'fixed');
    setStyle(node, 'width', `${width}px`);
    setStyle(node, 'left', '50%');
    setStyle(node, 'right', 'auto');
    setStyle(node, 'top', 'auto');
    setStyle(node, 'bottom', '0px');
    setStyle(node, 'margin', '0px');
    setStyle(node, 'transform-origin', 'bottom center');
    setStyle(node, 'transform', `translateX(-50%) scale(${scale})`);
    setStyle(node, 'z-index', '30');
  }
  let close = document.getElementById(CLOSE_ID);
  if (!visible) { close?.remove(); return; }
  if (!close) {
    close = document.createElement('button');
    close.id = CLOSE_ID;
    close.type = 'button';
    close.textContent = 'Werbung schließen ×';
    close.setAttribute('aria-label', 'Fußwerbung schließen');
    close.style.cssText = 'position:fixed;right:8px;z-index:31;padding:6px 10px;background:white;color:#222;border:1px solid #aaa;border-radius:3px;cursor:pointer;';
    close.addEventListener('click', () => owners.get(6)?.dismiss?.());
    document.body.appendChild(close);
  }
  setStyle(close, 'bottom', `${Math.min(maxHeight + 4, window.innerHeight - 40)}px`);
}

export function watchProviderOverlays() {
  let scheduled = false;
  let stopped = false;
  const refresh = () => {
    if (scheduled || stopped) return;
    scheduled = true;
    queueMicrotask(() => {
      scheduled = false;
      if (!stopped) enforceOverlaySafety();
    });
  };
  const observer = new MutationObserver(refresh);
  observer.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ['style', 'width', 'height'] });
  window.addEventListener('resize', refresh);
  listeners.add(refresh);
  refresh();
  return () => {
    stopped = true;
    observer.disconnect();
    listeners.delete(refresh);
    window.removeEventListener('resize', refresh);
  };
}
