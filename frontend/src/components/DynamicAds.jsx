import { useEffect, useRef, useState, createContext, useContext } from 'react';
import { useLocation } from 'react-router-dom';
import { getActiveAdSlots } from '@/api';
import { canShowAd, hasAdCode, LEGACY_FORMATS, NO_AD_PAGES } from '@/lib/adPolicy';

const AdSlotsContext = createContext({ slots: [], loading: true });

export function AdSlotsProvider({ children }) {
  const [slots, setSlots] = useState([]);
  const [loading, setLoading] = useState(true);
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
  const [width, setWidth] = useState(() => window.innerWidth);
  useEffect(() => {
    const resize = () => setWidth(window.innerWidth);
    window.addEventListener('resize', resize);
    return () => window.removeEventListener('resize', resize);
  }, []);
  const allowed = !loading && canShowAd(slot, pathname, width);
  const format = LEGACY_FORMATS[slotKey];
  useEffect(() => {
    if (!allowed || !containerRef.current) return;
    const container = containerRef.current;
    const timer = setTimeout(() => {
      // Reject hidden parents and placements narrower than the requested format.
      const requiredWidth = hasAdCode(slot) ? 1 : format?.width;
      if (container.getBoundingClientRect().width < requiredWidth) return;
      container.replaceChildren();
      if (hasAdCode(slot)) {
        if (slot.html_code) appendCode(container, slot.html_code);
        if (slot.embed_code) appendCode(container, slot.embed_code);
        if (slot.js_code) {
          const script = document.createElement('script');
          script.textContent = slot.js_code;
          container.appendChild(script);
        }
      } else if (format) {
        const placement = document.createElement('div');
        placement.id = '141912-' + format.id;
        placement.style.width = format.width + 'px';
        placement.style.marginInline = 'auto';
        container.appendChild(placement);
        ['https://ads.themoneytizer.com/s/gen.js?type=' + format.id, 'https://ads.themoneytizer.com/s/requestform.js?siteId=141912&formatId=' + format.id].forEach(src => {
          const script = document.createElement('script');
          script.async = false;
          script.src = src;
          placement.appendChild(script);
        });
      }
    }, 200);
    return () => { clearTimeout(timer); container.replaceChildren(); };
  }, [allowed, pathname, slot, format, width]);
  if (!allowed) return null;
  return <div ref={containerRef} data-slot={slotKey} data-testid={'ad-slot-' + slotKey} className={'managed-ad-slot max-w-full overflow-hidden ' + className} style={{ minHeight: format?.height || minHeight, width: '100%' }} />;
}
