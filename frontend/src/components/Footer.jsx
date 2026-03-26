import { Link } from "react-router-dom";
import { FacebookLogo, InstagramLogo, XLogo, YoutubeLogo } from "@phosphor-icons/react";

export default function Footer() {
  return (
    <footer className="bg-[#1a1a1a] text-white" data-testid="main-footer">
      {/* Main Footer Content */}
      <div className="max-w-[1200px] mx-auto px-3 py-10">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          {/* Brand Column */}
          <div className="col-span-2 md:col-span-1">
            <Link to="/" className="inline-block mb-4">
              <span 
                className="text-2xl font-black tracking-tight uppercase"
                style={{ fontFamily: "'Oswald', sans-serif" }}
              >
                <span className="text-white">TRANSFER</span>
                <span className="text-[#79B92A]">NEWS</span>
              </span>
            </Link>
            <p className="text-sm text-white/60 leading-relaxed mb-6">
              Die schnellste Quelle für Fußball-Transfer-News, Gerüchte und offizielle Wechsel in Deutschland.
            </p>
            
            {/* Social Icons */}
            <div className="flex items-center gap-3">
              <a 
                href="https://facebook.com" 
                target="_blank" 
                rel="noopener noreferrer"
                className="w-10 h-10 bg-white/10 flex items-center justify-center hover:bg-[#79B92A] transition-colors"
              >
                <FacebookLogo size={20} weight="fill" />
              </a>
              <a 
                href="https://instagram.com" 
                target="_blank" 
                rel="noopener noreferrer"
                className="w-10 h-10 bg-white/10 flex items-center justify-center hover:bg-[#79B92A] transition-colors"
              >
                <InstagramLogo size={20} weight="fill" />
              </a>
              <a 
                href="https://x.com" 
                target="_blank" 
                rel="noopener noreferrer"
                className="w-10 h-10 bg-white/10 flex items-center justify-center hover:bg-[#79B92A] transition-colors"
              >
                <XLogo size={20} weight="fill" />
              </a>
              <a 
                href="https://youtube.com" 
                target="_blank" 
                rel="noopener noreferrer"
                className="w-10 h-10 bg-white/10 flex items-center justify-center hover:bg-[#79B92A] transition-colors"
              >
                <YoutubeLogo size={20} weight="fill" />
              </a>
            </div>
          </div>

          {/* News Links */}
          <div>
            <h4 
              className="text-sm font-black uppercase mb-4 text-[#79B92A]"
              style={{ fontFamily: "'Oswald', sans-serif" }}
            >
              News
            </h4>
            <ul className="space-y-2">
              <li>
                <Link to="/news" className="text-sm text-white/60 hover:text-white transition-colors">
                  Alle News
                </Link>
              </li>
              <li>
                <Link to="/geruechte" className="text-sm text-white/60 hover:text-white transition-colors">
                  Gerüchte
                </Link>
              </li>
              <li>
                <Link to="/transfers" className="text-sm text-white/60 hover:text-white transition-colors">
                  Bestätigte Transfers
                </Link>
              </li>
            </ul>
          </div>

          {/* Competitions Links */}
          <div>
            <h4 
              className="text-sm font-black uppercase mb-4 text-[#79B92A]"
              style={{ fontFamily: "'Oswald', sans-serif" }}
            >
              Wettbewerbe
            </h4>
            <ul className="space-y-2">
              <li>
                <Link to="/wettbewerb/bundesliga" className="text-sm text-white/60 hover:text-white transition-colors">
                  Bundesliga
                </Link>
              </li>
              <li>
                <Link to="/wettbewerb/premier-league" className="text-sm text-white/60 hover:text-white transition-colors">
                  Premier League
                </Link>
              </li>
              <li>
                <Link to="/wettbewerb/la-liga" className="text-sm text-white/60 hover:text-white transition-colors">
                  La Liga
                </Link>
              </li>
              <li>
                <Link to="/wettbewerb/serie-a" className="text-sm text-white/60 hover:text-white transition-colors">
                  Serie A
                </Link>
              </li>
              <li>
                <Link to="/wettbewerb/champions-league" className="text-sm text-white/60 hover:text-white transition-colors">
                  Champions League
                </Link>
              </li>
            </ul>
          </div>

          {/* Legal Links */}
          <div>
            <h4 
              className="text-sm font-black uppercase mb-4 text-[#79B92A]"
              style={{ fontFamily: "'Oswald', sans-serif" }}
            >
              Rechtliches
            </h4>
            <ul className="space-y-2">
              <li>
                <Link to="/impressum" className="text-sm text-white/60 hover:text-white transition-colors">
                  Impressum
                </Link>
              </li>
              <li>
                <Link to="/datenschutz" className="text-sm text-white/60 hover:text-white transition-colors">
                  Datenschutz
                </Link>
              </li>
              <li>
                <Link to="/agb" className="text-sm text-white/60 hover:text-white transition-colors">
                  AGB
                </Link>
              </li>
              <li>
                <Link to="/kontakt" className="text-sm text-white/60 hover:text-white transition-colors">
                  Kontakt
                </Link>
              </li>
              <li>
                <Link to="/werbung" className="text-sm text-white/60 hover:text-white transition-colors">
                  Werbung
                </Link>
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* Bottom Bar */}
      <div className="border-t border-white/10">
        <div className="max-w-[1200px] mx-auto px-3 py-4">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <p className="text-xs text-white/40 text-center md:text-left">
              &copy; {new Date().getFullYear()} transfernews.de - Alle Rechte vorbehalten
            </p>
            <div className="flex items-center gap-4">
              <Link to="/impressum" className="text-xs text-white/40 hover:text-white transition-colors">
                Impressum
              </Link>
              <span className="text-white/20">|</span>
              <Link to="/datenschutz" className="text-xs text-white/40 hover:text-white transition-colors">
                Datenschutz
              </Link>
              <span className="text-white/20">|</span>
              <Link to="/kontakt" className="text-xs text-white/40 hover:text-white transition-colors">
                Kontakt
              </Link>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
