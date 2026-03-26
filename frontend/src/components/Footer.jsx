import { Link } from "react-router-dom";

export default function Footer() {
  return (
    <footer className="bg-[#1a1a1a] text-white mt-auto" data-testid="main-footer">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand */}
          <div>
            <span className="text-xl font-extrabold tracking-tight block mb-4" style={{fontFamily: 'Inter, sans-serif'}}>
              <span className="text-white">transfer</span>
              <span className="text-[#79B92A]">news</span>
            </span>
            <p className="text-sm text-white/70">
              Die schnellste Quelle für Fußball-Transfer-News, Gerüchte und offizielle Wechsel.
            </p>
          </div>

          {/* News */}
          <div>
            <h4 className="font-bold text-sm mb-4 text-[#79B92A]">News</h4>
            <ul className="space-y-2 text-sm text-white/70">
              <li><Link to="/news" className="hover:text-white transition-colors">Alle News</Link></li>
              <li><Link to="/geruechte" className="hover:text-white transition-colors">Gerüchte</Link></li>
              <li><Link to="/transfers" className="hover:text-white transition-colors">Bestätigte Transfers</Link></li>
            </ul>
          </div>

          {/* Wettbewerbe */}
          <div>
            <h4 className="font-bold text-sm mb-4 text-[#79B92A]">Wettbewerbe</h4>
            <ul className="space-y-2 text-sm text-white/70">
              <li><Link to="/wettbewerb/bundesliga" className="hover:text-white transition-colors">Bundesliga</Link></li>
              <li><Link to="/wettbewerb/premier-league" className="hover:text-white transition-colors">Premier League</Link></li>
              <li><Link to="/wettbewerb/la-liga" className="hover:text-white transition-colors">La Liga</Link></li>
              <li><Link to="/wettbewerb/champions-league" className="hover:text-white transition-colors">Champions League</Link></li>
            </ul>
          </div>

          {/* Rechtliches */}
          <div>
            <h4 className="font-bold text-sm mb-4 text-[#79B92A]">Rechtliches</h4>
            <ul className="space-y-2 text-sm text-white/70">
              <li><Link to="/impressum" className="hover:text-white transition-colors">Impressum</Link></li>
              <li><Link to="/datenschutz" className="hover:text-white transition-colors">Datenschutz</Link></li>
              <li><Link to="/kontakt" className="hover:text-white transition-colors">Kontakt</Link></li>
            </ul>
          </div>
        </div>

        <div className="border-t border-white/10 mt-8 pt-8 text-center text-sm text-white/50">
          <p>&copy; {new Date().getFullYear()} transfernews.de - Alle Rechte vorbehalten</p>
        </div>
      </div>
    </footer>
  );
}
