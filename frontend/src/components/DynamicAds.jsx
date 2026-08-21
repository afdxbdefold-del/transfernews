import { useEffect, useRef, useState, createContext, useContext } from 'react';
import { useLocation } from 'react-router-dom';
import { getActiveAdSlots } from '@/api';

// Context for ad slots data
const AdSlotsContext = createContext({ slots: [], loading: true });

// Pages without ads
const NO_AD_PAGES = ['/impressum', '/datenschutz', '/ueber-uns', '/about', '/admin'];

// Provider that fetches ad slots once
export function AdSlotsProvider({ children }) {
  const [slots, setSlots] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSlots = async () => {
      try {
        const res = await getActiveAdSlots();
        setSlots(res.data || []);
      } catch (e) {
        console.error('Failed to load ad slots:', e);
        setSlots([]);
      } finally {
        setLoading(false);
      }
    };
    fetchSlots();
  }, []);

  return (
    <AdSlotsContext.Provider value={{ slots, loading }}>
      {children}
    </AdSlotsContext.Provider>
  );
}

// Hook to get a specific ad slot
export function useAdSlot(slotKey) {
  const { slots, loading } = useContext(AdSlotsContext);
  const slot = slots.find(s => s.slot_key === slotKey);
  return { slot, loading };
}

// Hook to check if we should show ads
export function useShouldShowAds() {
  const location = useLocation();
  return !NO_AD_PAGES.some(p => location.pathname.startsWith(p));
}

// Dynamic ad component that renders code from database
function DynamicAdSlot({ slotKey, minHeight = '90px', className = '' }) {
  const location = useLocation();
  const containerRef = useRef(null);
  const { slot, loading } = useAdSlot(slotKey);
  const shouldShow = !NO_AD_PAGES.some(p => location.pathname.startsWith(p));
  const loadedRef = useRef(false);

  useEffect(() => {
    if (!shouldShow || !slot || loading || !containerRef.current) return;
    
    const container = containerRef.current;
    
    // Clear old content on route change
    container.innerHTML = '';
    loadedRef.current = false;

    const timer = setTimeout(() => {
      if (loadedRef.current) return;
      loadedRef.current = true;

      // Add HTML code
      if (slot.html_code) {
        const htmlDiv = document.createElement('div');
        htmlDiv.innerHTML = slot.html_code;
        container.appendChild(htmlDiv);
      }

      // Add embed code (can contain scripts)
      if (slot.embed_code) {
        const embedDiv = document.createElement('div');
        embedDiv.innerHTML = slot.embed_code;
        
        // Execute any scripts in embed code
        const scripts = embedDiv.querySelectorAll('script');
        scripts.forEach(oldScript => {
          const newScript = document.createElement('script');
          Array.from(oldScript.attributes).forEach(attr => {
            newScript.setAttribute(attr.name, attr.value);
          });
          newScript.textContent = oldScript.textContent;
          oldScript.parentNode.replaceChild(newScript, oldScript);
        });
        
        container.appendChild(embedDiv);
      }

      // Add JS code
      if (slot.js_code) {
        const script = document.createElement('script');
        script.textContent = slot.js_code;
        container.appendChild(script);
      }
    }, 200);

    return () => clearTimeout(timer);
  }, [location.pathname, slot, loading, shouldShow]);

  if (!shouldShow || loading) return null;
  if (!slot) {
    // Fallback to hardcoded if slot not in DB
    return null;
  }

  return (
    <div
      ref={containerRef}
      data-slot={slotKey}
      data-testid={`ad-slot-${slotKey}`}
      className={className}
      style={{ minHeight }}
    />
  );
}

// Specific ad slot components using database
export function MegabannerAd() {
  return <DynamicAdSlot slotKey="megabanner" minHeight="90px" className="flex justify-center" />;
}

export function BillboardAd() {
  return <DynamicAdSlot slotKey="billboard" minHeight="250px" className="text-center" />;
}

export function SidebarAd300x600() {
  return <DynamicAdSlot slotKey="sidebar_300x600" minHeight="600px" />;
}

export function MrecAd() {
  return <DynamicAdSlot slotKey="mrec" minHeight="250px" />;
}

export function MrecAd2() {
  return <DynamicAdSlot slotKey="mrec_2" minHeight="250px" />;
}

export function AboveFooterAd() {
  return <DynamicAdSlot slotKey="above_footer" minHeight="90px" />;
}

export function StickySkyscraperAd() {
  const { slot } = useAdSlot('skyscraper');
  
  return (
    <>
      <style>{`
        @media (min-width: 1024px) {
          [data-slot="skyscraper"] {
            position: fixed;
            left: 0px;
            top: 90px;
            z-index: 99999999;
          }
        }
      `}</style>
      <DynamicAdSlot slotKey="skyscraper" minHeight="600px" className="hidden lg:block" />
    </>
  );
}

export function GlobalAd() {
  return <DynamicAdSlot slotKey="global" minHeight="0" />;
}

// In-Feed ad component
export function InFeedAd({ position = 0 }) {
  return <DynamicAdSlot slotKey={`infeed_${position}`} minHeight="250px" className="my-4" />;
}

// Generic ad slot by key
export function AdSlot({ slotKey, minHeight = '90px', className = '' }) {
  return <DynamicAdSlot slotKey={slotKey} minHeight={minHeight} className={className} />;
}

// Hook for global ads (skyscraper, floating)
export function useGlobalAds() {
  const location = useLocation();
  const { slots, loading } = useContext(AdSlotsContext);
  
  useEffect(() => {
    if (loading || NO_AD_PAGES.some(p => location.pathname.startsWith(p))) return;
    
    // Find global slots
    const globalSlots = slots.filter(s => 
      s.slot_key === 'skyscraper' || s.slot_key === 'global'
    );
    
    globalSlots.forEach(slot => {
      const container = document.getElementById(`global-${slot.slot_key}`);
      if (!container || container.childElementCount > 0) return;
      
      if (slot.embed_code) {
        container.innerHTML = slot.embed_code;
        // Execute scripts
        const scripts = container.querySelectorAll('script');
        scripts.forEach(oldScript => {
          const newScript = document.createElement('script');
          Array.from(oldScript.attributes).forEach(attr => {
            newScript.setAttribute(attr.name, attr.value);
          });
          newScript.textContent = oldScript.textContent;
          oldScript.parentNode.replaceChild(newScript, oldScript);
        });
      }
    });
  }, [location.pathname, slots, loading]);
}

export default DynamicAdSlot;
