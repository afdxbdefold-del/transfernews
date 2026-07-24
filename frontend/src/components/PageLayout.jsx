/**
 * PageLayout - Globales Layout für alle Seiten
 * 
 * Struktur wie transfermarkt.de:
 * - Gesamter Content in 1000px zentrierter Box
 * - Links und rechts Platz für Sticky Ads
 * - Header, Nav, Content, Footer alle innerhalb der Box
 */
export default function PageLayout({ children }) {
  return (
    <div className="min-h-screen bg-[#c5c5c5] dark:bg-[#1a1a1a]" data-testid="page-layout">
      {/* Sticky Ad - Links (ganz außen) */}
      <div 
        className="fixed left-0 top-0 bottom-0 hidden xl:block z-40"
        style={{ width: '160px' }}
      >
        <div className="sticky top-[100px] p-2">
          <div 
            className="ad-slot-sticky bg-gray-200 dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded"
            style={{ width: '160px', height: '600px' }}
            data-testid="left-sticky-ad"
          >
            <div className="flex items-center justify-center h-full text-[10px] text-gray-400 uppercase">
              Anzeige
            </div>
          </div>
        </div>
      </div>

      {/* Sticky Ad - Rechts (ganz außen) */}
      <div 
        className="fixed right-0 top-0 bottom-0 hidden xl:block z-40"
        style={{ width: '160px' }}
      >
        <div className="sticky top-[100px] p-2">
          <div 
            className="ad-slot-sticky bg-gray-200 dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded"
            style={{ width: '160px', height: '600px' }}
            data-testid="right-sticky-ad"
          >
            <div className="flex items-center justify-center h-full text-[10px] text-gray-400 uppercase">
              Anzeige
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Box - 1000px zentriert */}
      <div className="w-full max-w-[1000px] mx-auto min-h-screen bg-[#e8e8e8] dark:bg-gray-950 shadow-lg">
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
