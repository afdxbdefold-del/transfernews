import { Link } from "react-router-dom";
import { useEffect } from "react";

export default function Footer() {
  useEffect(() => {
    const container = document.getElementById('141912-28');
    if (container && !container.hasChildNodes()) {
      const script1 = document.createElement('script');
      script1.src = '//ads.themoneytizer.com/s/gen.js?type=28';
      script1.async = true;
      const script2 = document.createElement('script');
      script2.src = '//ads.themoneytizer.com/s/requestform.js?siteId=141912&formatId=28';
      script2.async = true;
      container.appendChild(script1);
      container.appendChild(script2);
    }
  }, []);

  return (
    <>
      {/* Ad above footer */}
      <div className="bg-[#e8e8e8] py-3 flex justify-center">
        <div id="141912-28"></div>
      </div>
      
      <footer className="bg-neutral-800 text-white" data-testid="main-footer">
      {/* Main Footer Content */}
      <div className="py-4 border-b border-white/10 px-3">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <h4 className="text-[11px] font-bold uppercase text-white/60 mb-2">News</h4>
            <ul className="space-y-1">
              <li><Link to="/" className="text-[12px] text-white/80 hover:text-white">Alle News</Link></li>
              <li><Link to="/ticker" className="text-[12px] text-white/80 hover:text-white">News-Ticker</Link></li>
              <li><Link to="/geruechte" className="text-[12px] text-white/80 hover:text-white">Gerüchte</Link></li>
              <li><Link to="/top-deals" className="text-[12px] text-white/80 hover:text-white">Top-Transfers</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="text-[11px] font-bold uppercase text-white/60 mb-2">Wettbewerbe</h4>
            <ul className="space-y-1">
              <li><Link to="/wettbewerb/bundesliga" className="text-[12px] text-white/80 hover:text-white">Bundesliga</Link></li>
              <li><Link to="/wettbewerb/premier-league" className="text-[12px] text-white/80 hover:text-white">Premier League</Link></li>
              <li><Link to="/wettbewerb/la-liga" className="text-[12px] text-white/80 hover:text-white">La Liga</Link></li>
              <li><Link to="/wettbewerb/serie-a" className="text-[12px] text-white/80 hover:text-white">Serie A</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="text-[11px] font-bold uppercase text-white/60 mb-2">Transfers</h4>
            <ul className="space-y-1">
              <li><Link to="/abloesefrei" className="text-[12px] text-white/80 hover:text-white">Ablösefreie Spieler</Link></li>
              <li><Link to="/deadline-day" className="text-[12px] text-white/80 hover:text-white">Deadline Day</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="text-[11px] font-bold uppercase text-white/60 mb-2">Über Uns</h4>
            <ul className="space-y-1">
              <li><Link to="/ueber-uns" className="text-[12px] text-white/80 hover:text-white">Über TransferNews</Link></li>
              <li><Link to="/impressum" className="text-[12px] text-white/80 hover:text-white">Impressum</Link></li>
              <li><Link to="/datenschutz" className="text-[12px] text-white/80 hover:text-white">Datenschutz</Link></li>
            </ul>
          </div>
        </div>
      </div>
      
      {/* Bottom Bar */}
      <div className="py-3 px-3 flex flex-col md:flex-row items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="font-bold text-[12px] text-white">transfernews</span>
          <span className="text-[10px] text-white/50">© {new Date().getFullYear()}</span>
        </div>
        
        <div className="flex items-center gap-4 text-[10px] text-white/50">
          <Link to="/impressum" className="hover:text-white">Impressum</Link>
          <Link to="/datenschutz" className="hover:text-white">Datenschutz</Link>
          <span>Alle Rechte vorbehalten</span>
        </div>
      </div>
    </footer>
    </>
  );
}
