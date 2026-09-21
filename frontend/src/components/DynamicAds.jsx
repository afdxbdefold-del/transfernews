import { useEffect, useRef, useState, createContext, useContext } from 'react';
import { useLocation } from 'react-router-dom';
import { getActiveAdSlots } from '../api';
import { canShowAd, hasAdCode, LEGACY_FORMATS, NO_AD_PAGES } from '../lib/adPolicy';
import { claimFormats, releaseFormats, cleanPlacement, formatIdsForSlot, fitInlineCreative, watchProviderOverlays, requiresDocumentNavigation } from '../lib/adLifecycle';

const AdSlotsContext = createContext({ slots: [], loading: true });

export function AdSlotsProvider({ children }) {
  const [slots, setSlots] = useState([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    const stop = watchProviderOverlays();
    // The provider has document-scoped auctions/listeners. Navigation with ads
    // uses a new document, as the existing header links already do.
    const navigate = event => {
      const url = requiresDocumentNavigation(event);
      if (!url) return;
      event.preventDefault();
      event.stopPropagation();
      window.location.assign(url);
    };
    document.addEventListener('click', navigate, true);
    return () => { stop(); document.removeEventListener('click', navigate, true); };
  }, []);
  useEffect(() => {
    let cancelled = false;
    const refresh = async () => {
      try {
        const res = await getActiveAdSlots();
        if (!cancelled) setSlots(Array.isArray(res.data) ? res.data : []);
      } catch {
        if (!cancelled) setSlots([]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    refresh();
    window.addEventListener('ad-slots-updated', refresh);
    return () => { cancelled = true; window.removeEventListener('ad-slots-updated', refresh); };
  }, []);
  return <AdSlotsContext.Provider value={{ slots, loading }}>{children}</AdSlotsContext.Provider>;
}

export function useAdSlot(slotKey) {
  const { slots, loading } = useContext(AdSlotsContext);
  return { slot: slots.find(s => s.slot_key === slotKey), loading };
}
export function useShouldShowAds() {
  const { pathname } = useLocation();
  return !NO_AD_PAGES.some(p => pathname === p || pathname.startsWith(p + '/'));
}

function appendCode(container, html) {
  const wrapper = document.createElement('div');
  wrapper.innerHTML = html;
  container.appendChild(wrapper);
  wrapper.querySelectorAll('script').forEach(oldScript => {
    const script = document.createElement('script');
    script.async = false;
    Array.from(oldScript.attributes).forEach(attr => script.setAttribute(attr.name, attr.value));
    script.textContent = oldScript.textContent;
    oldScript.replaceWith(script);
  });
}

export default function DynamicAdSlot({ slotKey, minHeight = '90px', className = '' }) {
  const { pathname } = useLocation();
  const { slot, loading } = useAdSlot(slotKey);
  const containerRef = useRef(null);
  const [dismissedPath, setDismissedPath] = useState(null);
  const [width, setWidth] = useState(() => window.innerWidth);
  useEffect(() => {
    const resize = () => setWidth(window.innerWidth);
    window.addEventListener('resize', resize);
    return () => window.removeEventListener('resize', resize);
  }, []);
  const allowed = !loading && dismissedPath !== pathname && canShowAd(slot, pathname, width);
  const format = LEGACY_FORMATS[slotKey];
  // Primitive config dependencies prevent an equivalent API refresh or pixel
  // resize from starting a second auction.
  const htmlCode = slot?.html_code || '';
  const embedCode = slot?.embed_code || '';
  const jsCode = slot?.js_code || '';
  useEffect(() => {
    if (!allowed || !containerRef.current) return;
    const container = containerRef.current;
    const config = { html_code: htmlCode, embed_code: embedCode, js_code: jsCode };
    const ids = formatIdsForSlot(config, format);
    const owner = { dismiss: () => setDismissedPath(pathname) };
    let claimed = false;
    let content;
    let disposed = false;
    const fit = () => { if (content && !disposed) fitInlineCreative(container, content); };
    const load = () => {
      if (claimed || disposed) { fit(); return; }
      // Hidden or too narrow placements must not create an auction. A resize
      // observer retries when the actual parent becomes usable.
      const available = container.getBoundingClientRect().width;
      const requiredWidth = hasAdCode(config) ? 1 : (format?.id === 4 ? 120 : 300);
      if (available < requiredWidth) return;
      if (!claimFormats(ids, owner)) return;
      claimed = true;
      container.replaceChildren();
      content = document.createElement('div');
      content.className = 'managed-ad-content';
      content.style.width = Math.min(format?.width || available, available) + 'px';
      content.style.position = 'relative';
      container.appendChild(content);
      if (hasAdCode(config)) {
        if (htmlCode) appendCode(content, htmlCode);
        if (embedCode) appendCode(content, embedCode);
        if (jsCode) {
          const script = document.createElement('script');
          script.textContent = jsCode;
          content.appendChild(script);
        }
      } else if (format) {
        const placement = document.createElement('div');
        placement.id = '141912-' + format.id;
        placement.style.width = '100%';
        placement.style.marginInline = 'auto';
        content.appendChild(placement);
        ['https://ads.themoneytizer.com/s/gen.js?type=' + format.id, 'https://ads.themoneytizer.com/s/requestform.js?siteId=141912&formatId=' + format.id].forEach(src => {
          const script = document.createElement('script');
          script.async = false;
          script.src = src;
          placement.appendChild(script);
        });
      }
      fit();
      if (resizeObserver) resizeObserver.observe(content);
    };
    const resizeObserver = typeof ResizeObserver === 'undefined' ? null : new ResizeObserver(load);
    resizeObserver?.observe(container);
    const mutations = new MutationObserver(fit);
    mutations.observe(container, { childList: true, subtree: true, attributes: true, attributeFilter: ['style', 'width', 'height'] });
    const timer = setTimeout(load, 200);
    window.addEventListener('resize', load);
    return () => {
      disposed = true;
      clearTimeout(timer);
      resizeObserver?.disconnect();
      mutations.disconnect();
      window.removeEventListener('resize', load);
      cleanPlacement(container);
      if (claimed) releaseFormats(ids, owner);
      container.replaceChildren();
    };
  }, [allowed, pathname, format, htmlCode, embedCode, jsCode]);
  if (!allowed) return null;
  return <div ref={containerRef} data-slot={slotKey} data-testid={'ad-slot-' + slotKey} className={'managed-ad-slot max-w-full overflow-hidden relative ' + className} style={{ minHeight: format?.height ?? minHeight, width: '100%', minWidth: 0 }} />;
}
