import { useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';

// Pages without ads
const NO_AD_PAGES = ['/impressum', '/datenschutz', '/ueber-uns', '/about'];

// TheMonetizer Ad Loader
export function useTheMoneytizerAds() {
  const location = useLocation();
  const loadedRef = useRef(false);
  
  useEffect(() => {
    // Skip ads on legal pages
    if (NO_AD_PAGES.some(p => location.pathname.startsWith(p))) {
      return;
    }
    
    // Small delay to ensure DOM is ready
    const timer = setTimeout(() => {
      loadAllAds();
    }, 100);
    
    return () => clearTimeout(timer);
  }, [location.pathname]);
}

// Load a single ad
function loadAd(containerId, formatId) {
  const container = document.getElementById(containerId);
  if (!container) return;
  
  // Clear existing scripts to reload
  container.innerHTML = '';
  
  const script1 = document.createElement('script');
  script1.src = `//ads.themoneytizer.com/s/gen.js?type=${formatId}`;
  script1.async = true;
  
  const script2 = document.createElement('script');
  script2.src = `//ads.themoneytizer.com/s/requestform.js?siteId=141912&formatId=${formatId}`;
  script2.async = true;
  
  container.appendChild(script1);
  container.appendChild(script2);
}

// Load all ads
export function loadAllAds() {
  // Format 1: Megabanner
  loadAd('141912-1', 1);
  
  // Format 2: MREC 300x250
  loadAd('141912-2', 2);
  
  // Format 3: Sidebar 300x600
  loadAd('141912-3', 3);
  
  // Format 4: Skyscraper sticky
  loadAd('141912-4', 4);
  
  // Format 6: Global
  loadAd('141912-6', 6);
  
  // Format 19: MREC 2
  loadAd('141912-19', 19);
  
  // Format 28: Above footer
  loadAd('141912-28', 28);
  
  // Format 31: Billboard
  loadAd('141912-31', 31);
}

// Ad Container Components
export function MegabannerAd() {
  return <div id="141912-1" className="flex justify-center"></div>;
}

export function BillboardAd() {
  return <div id="141912-31" style={{textAlign: 'center'}}></div>;
}

export function SidebarAd300x600() {
  return <div id="141912-3"></div>;
}

export function MrecAd() {
  return <div id="141912-2"></div>;
}

export function MrecAd2() {
  return <div id="141912-19"></div>;
}

export function AboveFooterAd() {
  return <div id="141912-28"></div>;
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
