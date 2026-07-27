import { useEffect, useRef, useState } from 'react';
import { useLocation } from 'react-router-dom';

// Pages without ads
const NO_AD_PAGES = ['/impressum', '/datenschutz', '/ueber-uns', '/about'];

// Hook to check if we should show ads
export function useShouldShowAds() {
  const location = useLocation();
  return !NO_AD_PAGES.some(p => location.pathname.startsWith(p));
}

// Simple ad loader that triggers on pathname change
function AdContainer({ formatId, containerId, minHeight }) {
  const location = useLocation();
  const containerRef = useRef(null);
  const shouldShow = !NO_AD_PAGES.some(p => location.pathname.startsWith(p));
  const mountedRef = useRef(false);
  
  useEffect(() => {
    if (!shouldShow || !containerRef.current) return;
    
    const container = containerRef.current;
    
    // Clear old content
    container.innerHTML = '';
    
    // Load scripts after a delay
    const timer = setTimeout(() => {
      const script1 = document.createElement('script');
      script1.src = `//ads.themoneytizer.com/s/gen.js?type=${formatId}`;
      script1.async = true;
      
      const script2 = document.createElement('script');
      script2.src = `//ads.themoneytizer.com/s/requestform.js?siteId=141912&formatId=${formatId}`;
      script2.async = true;
      
      container.appendChild(script1);
      container.appendChild(script2);
    }, mountedRef.current ? 300 : 100);
    
    mountedRef.current = true;
    
    return () => clearTimeout(timer);
  }, [location.pathname, formatId, shouldShow]);
  
  if (!shouldShow) return null;
  
  return (
    <div 
      ref={containerRef}
      id={containerId}
      style={{ minHeight }}
    />
  );
}

// Hook for global ads
export function useTheMoneytizerAds() {
  const location = useLocation();
  const loadedRef = useRef(false);
  
  useEffect(() => {
    if (NO_AD_PAGES.some(p => location.pathname.startsWith(p))) return;
    if (loadedRef.current) return;
    
    const timer = setTimeout(() => {
      // Skyscraper
      const skyscraper = document.getElementById('141912-4');
      if (skyscraper && skyscraper.childElementCount === 0) {
        const s1 = document.createElement('script');
        s1.src = '//ads.themoneytizer.com/s/gen.js?type=4';
        s1.async = true;
        const s2 = document.createElement('script');
        s2.src = '//ads.themoneytizer.com/s/requestform.js?siteId=141912&formatId=4';
        s2.async = true;
        skyscraper.appendChild(s1);
        skyscraper.appendChild(s2);
      }
      
      // Global
      const global = document.getElementById('141912-6');
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
      
      loadedRef.current = true;
    }, 300);
    
    return () => clearTimeout(timer);
  }, [location.pathname]);
}

// Ad Components
export function MegabannerAd() {
  return (
    <div data-testid="megabanner-ad" className="flex justify-center">
      <AdContainer formatId={1} containerId="141912-1" minHeight="90px" />
    </div>
  );
}

export function BillboardAd() {
  return (
    <div data-testid="billboard-ad" style={{ textAlign: 'center' }}>
      <AdContainer formatId={31} containerId="141912-31" minHeight="250px" />
    </div>
  );
}

export function SidebarAd300x600() {
  return (
    <div data-testid="sidebar-ad">
      <AdContainer formatId={3} containerId="141912-3" minHeight="600px" />
    </div>
  );
}

export function MrecAd() {
  return (
    <div data-testid="mrec-ad">
      <AdContainer formatId={2} containerId="141912-2" minHeight="250px" />
    </div>
  );
}

export function MrecAd2() {
  return (
    <div data-testid="mrec-ad-2">
      <AdContainer formatId={19} containerId="141912-19" minHeight="250px" />
    </div>
  );
}

export function AboveFooterAd() {
  return (
    <div data-testid="above-footer-ad">
      <AdContainer formatId={28} containerId="141912-28" minHeight="90px" />
    </div>
  );
}

export function StickySkyscraperAd() {
  return (
    <>
      <style>{`
        @media (min-width: 1024px) {
          #141912-4 {
            position: fixed;
            left: 0px;
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
