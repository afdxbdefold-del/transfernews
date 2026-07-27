import { Link, useLocation } from "react-router-dom";
import { AboveFooterAd } from "./TheMoneytizerAds";

// Pages without ads
const NO_AD_PAGES = ['/impressum', '/datenschutz', '/ueber-uns', '/about'];

export default function Footer() {
  const location = useLocation();
  const showAds = !NO_AD_PAGES.some(p => location.pathname.startsWith(p));

  return (
    <>
      {/* Was ist transfernews.de - SEO/Programmatic Section */}
      <div className="bg-[#f5f5f5] py-6 px-4 border-t border-gray-200">
        <div className="max-w-[900px] mx-auto">
          <h2 className="text-lg font-bold text-gray-800 mb-3" style={{ fontFamily: "'Oswald', sans-serif" }}>
            Was ist transfernews.de?
          </h2>
          <p className="text-sm text-gray-600 leading-relaxed mb-3">
            <strong>transfernews.de</strong> ist Deutschlands führendes Nachrichtenportal für Fußball-Transfers, 
            Gerüchte und Wechsel-News. Wir berichten täglich über die neuesten Transfermeldungen aus der 
            Bundesliga, Premier League, La Liga, Serie A und allen großen europäischen Ligen.
          </p>
          <p className="text-sm text-gray-600 leading-relaxed mb-3">
            Unser erfahrenes Redaktionsteam analysiert Quellen aus aller Welt und liefert Ihnen verifizierte 
            Informationen zu Spielerwechseln, Vertragsverhandlungen, Ablösesummen und Marktwerten. Von 
            Top-Transfers der größten Stars bis hin zu aufstrebenden Talenten – wir halten Sie auf dem Laufenden.
          </p>
          <p className="text-sm text-gray-600 leading-relaxed">
            <strong>Unsere Themen:</strong> Transfer-News, Wechsel-Gerüchte, Vertragsauflösungen, ablösefreie 
            Spieler, Deadline-Day-Ticker, Marktwert-Updates, Spieler- und Vereinsprofile sowie exklusive 
            Hintergrundberichte aus dem Transfermarkt.
          </p>
        </div>
      </div>
      
      {/* Ad above footer */}
      {showAds && (
        <div className="bg-[#e8e8e8] py-3 flex justify-center">
          <AboveFooterAd />
        </div>
      )}
      
      <footer className="bg-neutral-800 text-white" data-testid="main-footer">
        <div className="py-8 px-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Brand */}
            <div>
              <h3 
                className="text-xl font-black text-white uppercase mb-3"
                style={{ fontFamily: "'Oswald', sans-serif" }}
              >
                TransferNews
              </h3>
              <p className="text-sm text-gray-400">
                Die schnellste Quelle für Fußball-Transfer-News, Gerüchte und offizielle Wechsel.
              </p>
            </div>
            
            {/* Quick Links */}
            <div>
              <h4 className="text-sm font-bold text-white uppercase mb-3 tracking-wider">Links</h4>
              <ul className="space-y-2">
                <li><Link to="/" className="text-sm text-gray-400 hover:text-white transition-colors">Startseite</Link></li>
                <li><Link to="/news" className="text-sm text-gray-400 hover:text-white transition-colors">Alle News</Link></li>
                <li><Link to="/geruechte" className="text-sm text-gray-400 hover:text-white transition-colors">Gerüchte</Link></li>
                <li><Link to="/transfers" className="text-sm text-gray-400 hover:text-white transition-colors">Transfers</Link></li>
              </ul>
            </div>
            
            {/* Legal */}
            <div>
              <h4 className="text-sm font-bold text-white uppercase mb-3 tracking-wider">Rechtliches</h4>
              <ul className="space-y-2">
                <li><Link to="/impressum" className="text-sm text-gray-400 hover:text-white transition-colors">Impressum</Link></li>
                <li><Link to="/datenschutz" className="text-sm text-gray-400 hover:text-white transition-colors">Datenschutz</Link></li>
                <li><Link to="/ueber-uns" className="text-sm text-gray-400 hover:text-white transition-colors">Über uns</Link></li>
              </ul>
            </div>
          </div>
          
          <div className="mt-8 pt-6 border-t border-gray-700 flex flex-col md:flex-row justify-between items-center">
            <p className="text-xs text-gray-500">
              © {new Date().getFullYear()} transfernews.de — Alle Rechte vorbehalten
            </p>
            <p className="text-xs text-gray-500 mt-2 md:mt-0">
              Spielerbilder: Wikimedia Commons (CC BY-SA) | Artikelbilder: Unsplash, Pexels
            </p>
          </div>
        </div>
      </footer>
    </>
  );
}
