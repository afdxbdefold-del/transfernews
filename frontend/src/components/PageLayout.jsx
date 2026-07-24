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
    <div className="min-h-screen bg-[#f2f2f2] dark:bg-[#1a1a1a] relative" data-testid="page-layout">
      {/* Sticky Skyscraper Links */}
      <div className="hidden xl:block fixed left-0 top-[100px] z-40" style={{ width: '160px' }}>
        <div 
          className="bg-gray-200 dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded ml-2 flex items-center justify-center"
          style={{ width: '160px', height: '600px' }}
          data-testid="left-sticky-ad"
        >
          <span className="text-[10px] text-gray-400 uppercase">Anzeige</span>
        </div>
      </div>

      {/* Sticky Skyscraper Rechts */}
      <div className="hidden xl:block fixed right-0 top-[100px] z-40" style={{ width: '160px' }}>
        <div 
          className="bg-gray-200 dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded mr-2 flex items-center justify-center"
          style={{ width: '160px', height: '600px' }}
          data-testid="right-sticky-ad"
        >
          <span className="text-[10px] text-gray-400 uppercase">Anzeige</span>
        </div>
      </div>

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
