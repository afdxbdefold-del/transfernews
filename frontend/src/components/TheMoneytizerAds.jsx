import { useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';

// Pages without ads
const NO_AD_PAGES = ['/impressum', '/datenschutz', '/ueber-uns', '/about'];

// Hook to check if we should show ads
export function useShouldShowAds() {
  const location = useLocation();
  return !NO_AD_PAGES.some(p => location.pathname.startsWith(p));
}

// Load ad into a container with error handling
function loadAdIntoContainer(container, formatId) {
  if (!container) return;
  
  // Clear previous content
  container.innerHTML = '';
  
  try {
    // Create and append scripts with error handling
    const script1 = document.createElement('script');
    script1.src = `//ads.themoneytizer.com/s/gen.js?type=${formatId}`;
    script1.async = true;
    script1.onerror = () => console.log(`Ad script gen.js type=${formatId} failed to load`);
    
    const script2 = document.createElement('script');
    script2.src = `//ads.themoneytizer.com/s/requestform.js?siteId=141912&formatId=${formatId}`;
    script2.async = true;
    script2.onerror = () => console.log(`Ad script requestform.js formatId=${formatId} failed to load`);
    
    container.appendChild(script1);
    container.appendChild(script2);
  } catch (e) {
    console.log('Ad loading error:', e);
  }
}

// Hook for individual ad loading - loads on mount
function useAdLoader(formatId) {
  const location = useLocation();
  const containerRef = useRef(null);
  
  useEffect(() => {
    const shouldLoad = !NO_AD_PAGES.some(p => location.pathname.startsWith(p));
    if (!shouldLoad) return;
    
    const container = containerRef.current;
    if (!container) return;
    
    // Small delay to ensure DOM is ready
    const timer = setTimeout(() => {
      loadAdIntoContainer(container, formatId);
    }, 100);
    
    return () => {
      clearTimeout(timer);
      // Cleanup on unmount
      if (container) {
        try {
          container.innerHTML = '';
        } catch (e) {
          // Ignore cleanup errors
        }
      }
    };
  }, [formatId, location.pathname]);
  
  return containerRef;
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
      const skyscraper = document.getElementById('141912-4');
      if (skyscraper && skyscraper.childElementCount === 0) {
        loadAdIntoContainer(skyscraper, 4);
      }
      
      // Global (Format 6)
      const global = document.getElementById('141912-6');
      if (global && global.childElementCount === 0) {
        loadAdIntoContainer(global, 6);
      }
    };
    
    const timer = setTimeout(loadGlobalAds, 200);
    return () => clearTimeout(timer);
  }, [location.pathname]);
}

// Ad Container Components - key attribute should be passed from parent for remounting
export function MegabannerAd() {
  const containerRef = useAdLoader(1);
  return <div ref={containerRef} className="flex justify-center min-h-[90px]"></div>;
}

export function BillboardAd() {
  const containerRef = useAdLoader(31);
  return <div ref={containerRef} style={{textAlign: 'center', minHeight: '250px'}}></div>;
}

export function SidebarAd300x600() {
  const containerRef = useAdLoader(3);
  return <div ref={containerRef} className="min-h-[600px]"></div>;
}

export function MrecAd() {
  const containerRef = useAdLoader(2);
  return <div ref={containerRef} className="min-h-[250px]"></div>;
}

export function MrecAd2() {
  const containerRef = useAdLoader(19);
  return <div ref={containerRef} className="min-h-[250px]"></div>;
}

export function AboveFooterAd() {
  const containerRef = useAdLoader(28);
  return <div ref={containerRef} className="min-h-[90px]"></div>;
}

export function StickySkyscraperAd() {
  return (
    <>
      <style>{`
        @media (min-width: 1024px) {
          #sas_26324 {
            position: fixed;
            right: 0px;
            top: 90px;
            z-index: 99999999;
          }
        }
      `}</style>
      <div id="141912-4" className="hidden lg:block"></div>
    </>
  );
}

export function GlobalAd() {
  return <div id="141912-6"></div>;
}
