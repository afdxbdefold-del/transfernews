import { useEffect } from 'react';

/**
 * PageLayout - Globales Layout für alle Seiten
 * 
 * Struktur wie transfermarkt.de:
 * - Gesamter Content in 1000px zentrierter Box
 * - Rechts TheMonetizer Sticky Ad
 * - Header, Nav, Content, Footer alle innerhalb der Box
 */
export default function PageLayout({ children }) {
  useEffect(() => {
    // Load TheMonetizer scripts
    const script1 = document.createElement('script');
    script1.src = '//ads.themoneytizer.com/s/gen.js?type=4';
    script1.async = true;
    
    const script2 = document.createElement('script');
    script2.src = '//ads.themoneytizer.com/s/requestform.js?siteId=141912&formatId=4';
    script2.async = true;
    
    const container = document.getElementById('141912-4');
    if (container && !container.hasChildNodes()) {
      container.appendChild(script1);
      container.appendChild(script2);
    }
    
    return () => {
      // Cleanup if needed
    };
  }, []);

  return (
    <div className="min-h-screen bg-[#f2f2f2] dark:bg-[#1a1a1a] relative" data-testid="page-layout">
      {/* TheMonetizer Sticky Skyscraper Rechts */}
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

      {/* Main Content Box - 1000px zentriert */}
      <div className="w-full max-w-[1000px] mx-auto min-h-screen bg-[#e8e8e8] dark:bg-gray-950">
        {children}
      </div>
    </div>
  );
}

/**
 * ContentWrapper - Wrapper für den Hauptinhalt innerhalb des Layouts
 * Verwendet für konsistentes Padding
 */
export function ContentWrapper({ children, className = "" }) {
  return (
    <div className={`px-3 py-3 ${className}`}>
      {children}
    </div>
  );
}
