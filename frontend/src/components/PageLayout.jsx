import { GlobalAd, MegabannerAd, StickySkyscraperAd, useShouldShowAds } from './TheMoneytizerAds';

export default function PageLayout({ children }) {
  const showAds = useShouldShowAds();
  

  return (
    <div className="min-h-screen bg-[#f2f2f2] dark:bg-[#1a1a1a] relative" data-testid="page-layout">
      {/* Megabanner über Header */}
      {showAds && (
        <div className="py-2 bg-[#f2f2f2]" data-testid="top-banner-container">
          <div className="w-full max-w-[1000px] mx-auto">
            <MegabannerAd />
          </div>
        </div>
      )}

      {/* Main Content Box - 1000px zentriert */}
      <div className="w-full max-w-[1000px] mx-auto min-h-screen bg-[#e8e8e8] dark:bg-gray-950">
        {children}
      </div>
      {showAds && <>
        <div className="w-[120px] mx-auto"><StickySkyscraperAd /></div>
        <GlobalAd />
      </>}
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
