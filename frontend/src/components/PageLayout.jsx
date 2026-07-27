import { useLocation } from 'react-router-dom';
import { useTheMoneytizerAds, StickySkyscraperAd, GlobalAd, MegabannerAd, BillboardAd } from './TheMoneytizerAds';

// Pages without ads
const NO_AD_PAGES = ['/impressum', '/datenschutz', '/ueber-uns', '/about'];

export default function PageLayout({ children }) {
  const location = useLocation();
  const showAds = !NO_AD_PAGES.some(p => location.pathname.startsWith(p));
  
  // Load global ads
  useTheMoneytizerAds();

  return (
    <div className="min-h-screen bg-[#f2f2f2] dark:bg-[#1a1a1a] relative" data-testid="page-layout">
      {/* TheMonetizer Global Ads */}
      {showAds && (
        <>
          <StickySkyscraperAd />
          <GlobalAd />
        </>
      )}

      {/* Megabanner über Header */}
      {showAds && (
        <div className="hidden lg:block py-2 bg-[#f2f2f2]" data-testid="top-banner-container">
          <div className="w-full max-w-[1000px] mx-auto">
            <MegabannerAd />
          </div>
        </div>
      )}

      {/* Main Content Box - 1000px zentriert */}
      <div className="w-full max-w-[1000px] mx-auto min-h-screen bg-[#e8e8e8] dark:bg-gray-950">
        {/* Billboard unter dem Header-Bereich, innerhalb der Content-Box */}
        {showAds && (
          <div className="hidden lg:block bg-[#d9d9d9] py-2" data-testid="billboard-container">
            <div className="flex justify-center">
              <BillboardAd />
            </div>
          </div>
        )}
        {children}
      </div>
    </div>
  );
}

export function ContentWrapper({ children, className = "" }) {
  return (
    <div className={`px-3 py-3 ${className}`}>
      {children}
    </div>
  );
}
