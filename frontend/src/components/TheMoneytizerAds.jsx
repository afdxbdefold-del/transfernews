import { useEffect, useRef, useCallback, useState } from 'react';
import { useLocation } from 'react-router-dom';

// Pages without ads
const NO_AD_PAGES = ['/impressum', '/datenschutz', '/ueber-uns', '/about'];

// Hook to check if we should show ads
export function useShouldShowAds() {
  const location = useLocation();
  return !NO_AD_PAGES.some(p => location.pathname.startsWith(p));
}

// Unique ID generator for ad containers
let adIdCounter = 0;
const generateAdId = () => `tm-ad-${++adIdCounter}-${Date.now()}`;

// Component that loads ad scripts fresh on each mount
function AdUnit({ formatId, minHeight, className = "", style = {} }) {
  const location = useLocation();
  const containerRef = useRef(null);
  const [containerId] = useState(() => generateAdId());
  const [loaded, setLoaded] = useState(false);
  
  const shouldShow = !NO_AD_PAGES.some(p => location.pathname.startsWith(p));
  
  const loadAd = useCallback(() => {
    const container = containerRef.current;
    if (!container || !shouldShow) return;
    
    // Clear any existing content
    container.innerHTML = '';
    setLoaded(false);
    
    // Create script elements
    const script1 = document.createElement('script');
    script1.src = `//ads.themoneytizer.com/s/gen.js?type=${formatId}`;
    script1.async = true;
    
    const script2 = document.createElement('script');
    script2.src = `//ads.themoneytizer.com/s/requestform.js?siteId=141912&formatId=${formatId}`;
    script2.async = true;
    script2.onload = () => {
      // Give the ad time to render
      setTimeout(() => setLoaded(true), 500);
    };
    
    container.appendChild(script1);
    container.appendChild(script2);
  }, [formatId, shouldShow]);
  
  // Load ad on mount and route change
  useEffect(() => {
    // Small delay to ensure DOM is ready
    const timer = setTimeout(loadAd, 100);
    
    return () => {
      clearTimeout(timer);
      // Cleanup on unmount
      if (containerRef.current) {
        containerRef.current.innerHTML = '';
      }
    };
  }, [loadAd, location.pathname]);
  
  if (!shouldShow) return null;
  
  return (
    <div 
      ref={containerRef}
      id={containerId}
      className={className}
      style={{ 
        minHeight, 
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        ...style 
      }}
    />
  );
}

// Hook for PageLayout to load global/sticky ads
export function useTheMoneytizerAds() {
  const location = useLocation();
  
  useEffect(() => {
    if (NO_AD_PAGES.some(p => location.pathname.startsWith(p))) {
      return;
    }
    
    const loadGlobalAds = () => {
      // Skyscraper (Format 4)
      const skyscraper = document.getElementById('tm-skyscraper');
      if (skyscraper && skyscraper.childElementCount === 0) {
        const script1 = document.createElement('script');
        script1.src = '//ads.themoneytizer.com/s/gen.js?type=4';
        script1.async = true;
        
        const script2 = document.createElement('script');
        script2.src = '//ads.themoneytizer.com/s/requestform.js?siteId=141912&formatId=4';
        script2.async = true;
        
        skyscraper.appendChild(script1);
        skyscraper.appendChild(script2);
      }
      
      // Global (Format 6)
      const global = document.getElementById('tm-global');
      if (global && global.childElementCount === 0) {
        const g1 = document.createElement('script');
        g1.src = '//ads.themoneytizer.com/s/gen.js?type=6';
        g1.async = true;
        
        const g2 = document.createElement('script');
        g2.src = '//ads.themoneytizer.com/s/requestform.js?siteId=141912&formatId=6';
        g2.async = true;
        
        global.appendChild(g1);
        global.appendChild(g2);
      }
    };
    
    const timer = setTimeout(loadGlobalAds, 200);
    return () => clearTimeout(timer);
  }, [location.pathname]);
}

// Megabanner 970x90 (Format 1)
export function MegabannerAd() {
  const location = useLocation();
  return (
    <div data-testid="megabanner-ad" key={`megabanner-${location.pathname}`}>
      <AdUnit formatId={1} minHeight="90px" />
    </div>
  );
}

// Billboard 970x250 (Format 31)
export function BillboardAd() {
  const location = useLocation();
  return (
    <div data-testid="billboard-ad" key={`billboard-${location.pathname}`}>
      <AdUnit formatId={31} minHeight="250px" />
    </div>
  );
}

// Sidebar 300x600 (Format 3)
export function SidebarAd300x600() {
  const location = useLocation();
  return (
    <div data-testid="sidebar-ad-300x600" key={`sidebar-${location.pathname}`}>
      <AdUnit formatId={3} minHeight="600px" />
    </div>
  );
}

// MREC 300x250 (Format 2)
export function MrecAd() {
  const location = useLocation();
  return (
    <div data-testid="mrec-ad" key={`mrec-${location.pathname}`}>
      <AdUnit formatId={2} minHeight="250px" />
    </div>
  );
}

// MREC 2 (Format 19)
export function MrecAd2() {
  const location = useLocation();
  return (
    <div data-testid="mrec-ad-2" key={`mrec2-${location.pathname}`}>
      <AdUnit formatId={19} minHeight="250px" />
    </div>
  );
}

// Above Footer (Format 28)
export function AboveFooterAd() {
  const location = useLocation();
  return (
    <div data-testid="above-footer-ad" key={`footer-${location.pathname}`}>
      <AdUnit formatId={28} minHeight="90px" />
    </div>
  );
}

// Sticky Skyscraper
export function StickySkyscraperAd() {
  return (
    <>
      <style>{`
        @media (min-width: 1024px) {
          #tm-skyscraper {
            position: fixed;
            left: 0px;
            top: 90px;
            z-index: 99999999;
          }
        }
      `}</style>
      <div id="tm-skyscraper" className="hidden lg:block"></div>
    </>
  );
}

// Global Ad Container
export function GlobalAd() {
  return <div id="tm-global"></div>;
}
