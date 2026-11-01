import { createContext, useContext, useEffect, useLayoutEffect, useMemo, useRef, useState, useSyncExternalStore, Children, Fragment } from 'react';
import { useLocation } from 'react-router-dom';
import { FREESTAR_SLOTS, createPlacementRegistry, isAdvertisingPage, mountFreestarSlot } from '../lib/freestar';
import { consentAllowsPrimis, loadedPrimisPage, mountPrimis } from '../lib/primis';
import './FreestarAds.css';

const PageAds = createContext(null);
const PrimisPage = createContext(null);

export function consentAllowsFreestar(data, success) {
  if (!success || !data || !['tcloaded', 'useractioncomplete'].includes(data.eventStatus)) return false;
  if (data.gdprApplies === false) return true;
  return data.gdprApplies === true && [1, 3, 4, 10].every(id => data.purpose?.consents?.[id]) && [850, 755].every(id => data.vendor?.consents?.[id]);
}

export function FreestarPage({ children, enabled = true }) {
  const { pathname, search } = useLocation();
  const eligible = enabled && isAdvertisingPage(pathname);
  const registry = useMemo(() => createPlacementRegistry(`${pathname}${search}:${eligible}`), [pathname, search, eligible]);
  const [consent, setConsent] = useState({ registry: null, allowed: false, primis: false });
  const consented = consent.registry === registry && consent.allowed;
  const page = pathname + search;
  useEffect(() => {
    if (!eligible && loadedPrimisPage() === page) window.dispatchEvent(new Event('transfernews-ad-consent-revoked'));
  }, [eligible, page]);
  useEffect(() => {
    if (!eligible) return;
    let disposed = false;
    let listenerId;
    let subscribed = false;
    let previouslyAllowed = false;
    const subscribe = () => {
      if (subscribed || typeof window.__tcfapi !== 'function') return;
      subscribed = true;
      window.__tcfapi('addEventListener', 2, (data, success) => {
        listenerId = data?.listenerId ?? listenerId;
        if (disposed) return;
        if (success && data && data.cmpStatus !== 'error' && !['tcloaded', 'useractioncomplete'].includes(data.eventStatus)) return;
        const allowed = consentAllowsFreestar(data, success);
        const primis = consentAllowsPrimis(data, success);
        // The new document handles any simultaneous grant. Starting another
        // provider here would request the placement twice during the reload.
        if ((previouslyAllowed && !allowed) || (loadedPrimisPage() && !primis)) {
          disposed = true;
          setConsent({ registry, allowed: false, primis: false });
          window.dispatchEvent(new Event('transfernews-ad-consent-revoked'));
          return;
        }
        setConsent({ registry, allowed, primis });
        previouslyAllowed = allowed;
      });
    };
    subscribe();
    const timer = setInterval(subscribe, 500);
    return () => {
      disposed = true; clearInterval(timer);
      if (listenerId != null) window.__tcfapi?.('removeEventListener', 2, () => {}, listenerId);
    };
  }, [eligible, registry]);
  useEffect(() => {
    if (!eligible || !consented || !window.freestar) return;
    const fs = window.freestar;
    const page = pathname + search;
    let disposed = false;
    fs.queue.push(() => {
      if (disposed) return;
      if (fs.transfernewsPage && fs.transfernewsPage !== page) fs.trackPageview?.();
      fs.transfernewsPage = page;
    });
    return () => { disposed = true; };
  }, [pathname, search, eligible, consented]);
  return <PageAds.Provider value={eligible && consented ? registry : null}>
    <PrimisPage.Provider value={eligible && consent.registry === registry && consent.primis ? page : null}>{children}</PrimisPage.Provider>
  </PageAds.Provider>;
}

export function PrimisPlacement() {
  const page = useContext(PrimisPage);
  const container = useRef(null);
  useEffect(() => { if (page) mountPrimis(container.current, page); }, [page]);
  if (!page) return null;
  return <aside aria-label="Videoanzeige" className="mx-auto w-full max-w-[310px]">
    <span className="freestar-label">Anzeige</span>
    <div ref={container} id="transfernews-primis-placement" />
  </aside>;
}

function OwnedSlot({ slot, registry, priority, className }) {
  const owner = useRef(Symbol(slot.key)).current;
  useLayoutEffect(() => registry.register(owner, slot.key, priority), [registry, owner, slot.key, priority]);
  const selected = useSyncExternalStore(registry.subscribe, () => registry.owner(slot.key) === owner, () => false);
  const outer = useRef(null);
  const inner = useRef(null);
  const [supported, setSupported] = useState(() => !slot.key.startsWith('siderail') || window.innerWidth >= 1000);
  useEffect(() => {
    const resize = () => setSupported(!slot.key.startsWith('siderail') || window.innerWidth >= 1000);
    window.addEventListener('resize', resize);
    return () => window.removeEventListener('resize', resize);
  }, [slot.key]);
  useEffect(() => {
    if (!selected || !supported || !inner.current) return;
    const container = outer.current;
    const creative = inner.current;
    const fit = () => {
      const available = container.getBoundingClientRect().width;
      const baseWidth = slot.key.startsWith('leaderboard') ? (window.innerWidth >= 1000 ? 970 : 320) : slot.width;
      const frames = [...creative.querySelectorAll('iframe, img, [width]')];
      // Centered iframes can overflow to the left: scrollWidth alone loses
      // that portion. Measure the actual creative, independent of transforms.
      const widths = (frames.length ? frames : [...creative.children]).map(node => Math.max(node.offsetWidth || 0, node.scrollWidth || 0));
      const natural = Math.max(baseWidth, ...widths);
      if (!available || !natural) return;
      if (creative.style.width !== `${natural}px`) creative.style.setProperty('width', `${natural}px`, 'important');
      const scale = Math.min(1, available / natural);
      if (creative.style.transformOrigin !== 'center top') creative.style.transformOrigin = 'center top';
      if (creative.style.transform !== `scale(${scale})`) creative.style.transform = `scale(${scale})`;
      const height = `${Math.ceil(creative.offsetHeight * scale)}px`;
      if (container.style.height !== height) container.style.height = height;
    };
    const observer = typeof ResizeObserver === 'undefined' ? null : new ResizeObserver(fit);
    observer?.observe(container); observer?.observe(creative);
    const mutations = new MutationObserver(fit);
    mutations.observe(creative, { childList: true, subtree: true, attributes: true, attributeFilter: ['width', 'height', 'style'] });
    const dispose = mountFreestarSlot(slot, creative);
    fit();
    window.addEventListener('resize', fit);
    return () => { observer?.disconnect(); mutations.disconnect(); window.removeEventListener('resize', fit); dispose(); };
  }, [selected, supported, slot, registry]);
  if (!selected) return null;
  return <div className={`freestar-placement ${slot.key.split('_')[0]} ${className}`} data-ad-placement={slot.key} data-supported={supported}>
    <span className="freestar-label">Anzeige</span>
    <div className="freestar-frame" ref={outer}>
      <div id={slot.id} data-freestar-ad={slot.sizes} ref={inner} className="freestar-creative" />
    </div>
  </div>;
}

export function FreestarSlot({ name, priority = 10, className = '' }) {
  const registry = useContext(PageAds);
  const slot = FREESTAR_SLOTS.find(item => item.key === name);
  return registry && slot ? <OwnedSlot slot={slot} registry={registry} priority={priority} className={className} /> : null;
}

export function RemainingContentAds() {
  return <div className="freestar-completion">{FREESTAR_SLOTS.filter(slot => slot.key.startsWith('incontent')).map(slot => <FreestarSlot key={slot.key} name={slot.key} priority={0} />)}</div>;
}

export function FreestarRails() {
  return <div className="freestar-rails">
    <div className="freestar-rail-column freestar-rail-left"><div className="freestar-rail-segment"><FreestarSlot name="siderail_1" /></div><div className="freestar-rail-segment"><FreestarSlot name="siderail_2" /></div></div>
    <div className="freestar-rail-column freestar-rail-right"><div className="freestar-rail-segment"><FreestarSlot name="siderail_3" /></div><div className="freestar-rail-segment"><FreestarSlot name="siderail_4" /></div></div>
  </div>;
}

// Insert three distinct placements between groups, retaining stable article
// keys as more results load. Remaining slots are supplied once by the layout.
export function AdFeed({ children }) {
  const items = Children.toArray(children);
  return <>{items.map((child, index) => <Fragment key={child.key || index}>{child}{[3, 7, 11].includes(index) && <FreestarSlot name={`incontent_${[3, 7, 11].indexOf(index) + 1}`} />}</Fragment>)}</>;
}
