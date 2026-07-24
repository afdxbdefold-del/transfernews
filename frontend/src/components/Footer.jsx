import { Link } from "react-router-dom";

export default function Footer() {
  return (
    <footer className="bg-[#1a1a1a] text-white py-8" data-testid="main-footer">
      <div className="max-w-[1000px] mx-auto px-4">
        {/* Logo */}
        <div className="mb-6">
          <Link to="/">
            <img src="/logo.svg" alt="TransferNews" className="h-5 brightness-0 invert" />
          </Link>
        </div>
        
        {/* Links Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-8">
          <div>
            <h4 className="text-xs font-bold uppercase text-gray-400 mb-3">News</h4>
            <ul className="space-y-2">
              <li><Link to="/news" className="text-sm text-gray-300 hover:text-white">Alle News</Link></li>
              <li><Link to="/geruechte" className="text-sm text-gray-300 hover:text-white">Gerüchte</Link></li>
              <li><Link to="/transfers" className="text-sm text-gray-300 hover:text-white">Transfers</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="text-xs font-bold uppercase text-gray-400 mb-3">Wettbewerbe</h4>
            <ul className="space-y-2">
              <li><Link to="/wettbewerb/bundesliga" className="text-sm text-gray-300 hover:text-white">Bundesliga</Link></li>
              <li><Link to="/wettbewerb/premier-league" className="text-sm text-gray-300 hover:text-white">Premier League</Link></li>
              <li><Link to="/wettbewerb/la-liga" className="text-sm text-gray-300 hover:text-white">La Liga</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="text-xs font-bold uppercase text-gray-400 mb-3">Über Uns</h4>
            <ul className="space-y-2">
              <li><Link to="/ueber-uns" className="text-sm text-gray-300 hover:text-white">Über TransferNews</Link></li>
              <li><Link to="/redaktion" className="text-sm text-gray-300 hover:text-white">Redaktion</Link></li>
              <li><Link to="/impressum" className="text-sm text-gray-300 hover:text-white">Impressum</Link></li>
              <li><Link to="/datenschutz" className="text-sm text-gray-300 hover:text-white">Datenschutz</Link></li>
            </ul>
          </div>
        </div>
        
        {/* Copyright */}
        <div className="border-t border-gray-800 pt-4">
          <p className="text-xs text-gray-500">&copy; {new Date().getFullYear()} transfernews.de</p>
        </div>
      </div>
    </footer>
  );
}
