import Header from "@/components/Header";
import Footer from "@/components/Footer";
import BreakingNewsTicker from "@/components/BreakingNewsTicker";
import { HeroTeaser, MediumTeaser, ListTeaser, NewsTickerEntry } from "@/components/NewsCard";
import { AdSlot, SidebarAd } from "@/components/AdSlot";
import { useEffect, useState } from "react";
import { getPublishedArticles, getConfirmedTransfers, getRumours } from "@/api";
import { Link } from "react-router-dom";
import { ArrowRight, TrendUp, Handshake, CaretRight } from "@phosphor-icons/react";

export default function HomePage() {
  const [articles, setArticles] = useState([]);
  const [transfers, setTransfers] = useState([]);
  const [rumours, setRumours] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [newsRes, transfersRes, rumoursRes] = await Promise.all([
          getPublishedArticles({ limit: 25 }),
          getConfirmedTransfers({ limit: 5 }),
          getRumours({ status: "active", limit: 5 }),
        ]);
        
        setArticles(newsRes.data);
        setTransfers(transfersRes.data);
        setRumours(rumoursRes.data);
      } catch (e) {
        console.error("Homepage load error:", e);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  // Split articles for different sections
  const heroArticle = articles[0];
  const midTeasers = articles.slice(1, 5);
  const listTeasers = articles.slice(5, 9);
  const newsTickerArticles = articles.slice(0, 12);
  const moreArticles = articles.slice(9, 20);

  return (
    <div className="min-h-screen flex flex-col bg-[#f5f5f5]" data-testid="homepage">
      <Header />
      <BreakingNewsTicker />
      
      {/* Top Banner Ad */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-[1200px] mx-auto px-3 py-2">
          <AdSlot slotKey="below_header" minHeight="90px" />
        </div>
      </div>

      <main className="flex-1">
        <div className="max-w-[1200px] mx-auto px-3 py-6">
          
          {/* Top Teaser Card Section - Sport1 Style */}
          <div className="bg-white mb-6" data-testid="top-teaser-section">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-0">
              
              {/* Main Content Area (Left 2/3) */}
              <div className="lg:col-span-2">
                {/* Hero + Mid Teasers Grid */}
                <div className="p-3 md:p-0">
                  {/* Hero Teaser */}
                  {heroArticle && (
                    <HeroTeaser article={heroArticle} />
                  )}
                  
                  {/* Mid Teasers - 2 Column Grid */}
                  <div className="grid grid-cols-2 gap-3 mt-3">
                    {midTeasers.map((article) => (
                      <MediumTeaser key={article.id} article={article} />
                    ))}
                  </div>
                  
                  {/* List Teasers */}
                  <div className="mt-4 border-t border-gray-100 pt-4">
                    {listTeasers.map((article) => (
                      <ListTeaser key={article.id} article={article} />
                    ))}
                  </div>
                </div>

                {/* Action Buttons - Sport1 Style */}
                <div className="flex gap-3 p-3 md:p-4 border-t border-gray-100">
                  <Link 
                    to="/transfers"
                    className="flex-1 bg-[#79B92A] text-white font-black uppercase text-center py-3 hover:bg-[#6aa325] transition-colors"
                    style={{ fontFamily: "'Oswald', sans-serif" }}
                    data-testid="action-btn-transfers"
                  >
                    Transfers
                  </Link>
                  <Link 
                    to="/geruechte"
                    className="flex-1 bg-[#79B92A] text-white font-black uppercase text-center py-3 hover:bg-[#6aa325] transition-colors"
                    style={{ fontFamily: "'Oswald', sans-serif" }}
                    data-testid="action-btn-geruechte"
                  >
                    Gerüchte
                  </Link>
                </div>
              </div>

              {/* Newsticker Sidebar (Right 1/3) - Desktop Only */}
              <div className="hidden lg:block border-l border-gray-100">
                {/* Newsticker Header */}
                <div className="flex items-center justify-between p-4 border-b border-gray-100">
                  <Link 
                    to="/news"
                    className="flex items-center gap-2 group"
                  >
                    <h2 
                      className="text-2xl font-black uppercase text-gray-900 group-hover:text-[#79B92A] transition-colors"
                      style={{ fontFamily: "'Oswald', sans-serif" }}
                    >
                      Newsticker
                    </h2>
                    <CaretRight size={20} weight="bold" className="text-gray-400 group-hover:text-[#79B92A] transition-colors" />
                  </Link>
                </div>

                {/* Newsticker Entries */}
                <div className="divide-y divide-gray-100">
                  {newsTickerArticles.map((article) => (
                    <NewsTickerEntry key={article.id} article={article} />
                  ))}
                </div>

                {/* All News Button */}
                <div className="p-4">
                  <Link 
                    to="/news"
                    className="block w-full bg-[#79B92A] text-white font-black uppercase text-center py-3 hover:bg-[#6aa325] transition-colors"
                    style={{ fontFamily: "'Oswald', sans-serif" }}
                  >
                    Alle News anzeigen
                  </Link>
                </div>
              </div>
            </div>
          </div>

          {/* Mobile Newsticker - Only on Mobile */}
          <div className="lg:hidden bg-white mb-6" data-testid="mobile-newsticker">
            <div className="flex items-center justify-between p-4 border-b border-gray-100">
              <Link to="/news" className="flex items-center gap-2 group">
                <h2 
                  className="text-xl font-black uppercase text-gray-900 group-hover:text-[#79B92A] transition-colors"
                  style={{ fontFamily: "'Oswald', sans-serif" }}
                >
                  Newsticker
                </h2>
                <CaretRight size={18} weight="bold" className="text-gray-400 group-hover:text-[#79B92A]" />
              </Link>
            </div>
            <div className="divide-y divide-gray-100 px-4">
              {newsTickerArticles.slice(0, 6).map((article) => (
                <NewsTickerEntry key={article.id} article={article} />
              ))}
            </div>
            <div className="p-4">
              <Link 
                to="/news"
                className="block w-full bg-[#79B92A] text-white font-black uppercase text-center py-3 hover:bg-[#6aa325] transition-colors"
                style={{ fontFamily: "'Oswald', sans-serif" }}
              >
                Alle News anzeigen
              </Link>
            </div>
          </div>

          {/* Ad Banner */}
          <div className="mb-6">
            <AdSlot slotKey="homepage_feed_banner_1" minHeight="90px" />
          </div>

          {/* Main Grid Layout - Content + Sidebar */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            
            {/* Main Content Column */}
            <div className="lg:col-span-2 space-y-6">
              
              {/* Transfer News Section */}
              <section className="bg-white" data-testid="transfers-section">
                <div className="flex items-center justify-between p-4 border-b border-gray-100">
                  <h2 
                    className="text-xl font-black uppercase flex items-center gap-2"
                    style={{ fontFamily: "'Oswald', sans-serif" }}
                  >
                    <Handshake size={24} className="text-[#79B92A]" weight="fill" />
                    Transfers
                  </h2>
                  <Link 
                    to="/transfers" 
                    className="text-[#79B92A] text-sm font-bold hover:underline flex items-center gap-1"
                  >
                    Alle <ArrowRight size={14} />
                  </Link>
                </div>
                
                {transfers.length > 0 ? (
                  <div className="divide-y divide-gray-100">
                    {transfers.map((transfer) => (
                      <div key={transfer.id} className="flex items-center gap-4 p-4 hover:bg-gray-50 transition-colors">
                        <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0">
                          <Handshake size={20} className="text-green-600" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span className={`text-[10px] font-bold px-1.5 py-0.5 ${
                              transfer.status === "official" 
                                ? "bg-blue-100 text-blue-700" 
                                : "bg-green-100 text-green-700"
                            }`}>
                              {transfer.status === "official" ? "OFFIZIELL" : "BESTÄTIGT"}
                            </span>
                          </div>
                          <p className="font-bold text-sm">Transfer #{transfer.id.slice(0, 8)}</p>
                          {transfer.fee_amount && (
                            <p className="text-xs text-gray-500 mt-0.5">
                              {transfer.fee_amount.toLocaleString("de-DE")} {transfer.fee_currency}
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="p-4 text-sm text-gray-500">Keine bestätigten Transfers</p>
                )}
              </section>

              {/* Mid Page Ad */}
              <AdSlot slotKey="homepage_feed_banner_2" minHeight="90px" />

              {/* More News Section */}
              <section className="bg-white" data-testid="more-news-section">
                <div className="flex items-center justify-between p-4 border-b border-gray-100">
                  <h2 
                    className="text-xl font-black uppercase"
                    style={{ fontFamily: "'Oswald', sans-serif" }}
                  >
                    Weitere News
                  </h2>
                </div>
                
                <div className="divide-y divide-gray-100">
                  {moreArticles.map((article) => (
                    <ListTeaser key={article.id} article={article} />
                  ))}
                </div>
              </section>

              {/* Bottom Feed Ad */}
              <AdSlot slotKey="homepage_feed_banner_3" minHeight="90px" />
            </div>

            {/* Sidebar */}
            <aside className="space-y-6">
              {/* Sidebar Top Ad */}
              <SidebarAd slotKey="sidebar_top" />

              {/* Rumours Widget */}
              <section className="bg-white" data-testid="rumours-widget">
                <div className="flex items-center justify-between p-4 border-b border-gray-100">
                  <h3 
                    className="text-lg font-black uppercase flex items-center gap-2"
                    style={{ fontFamily: "'Oswald', sans-serif" }}
                  >
                    <TrendUp size={20} className="text-yellow-600" weight="fill" />
                    Gerüchte
                  </h3>
                  <Link to="/geruechte" className="text-[#79B92A] text-xs font-bold hover:underline">
                    Alle
                  </Link>
                </div>
                
                {rumours.length > 0 ? (
                  <div className="divide-y divide-gray-100">
                    {rumours.map((rumour) => (
                      <div key={rumour.id} className="p-4 hover:bg-gray-50 transition-colors">
                        <span className="inline-block text-[10px] font-bold px-1.5 py-0.5 bg-yellow-100 text-yellow-700 mb-2">
                          GERÜCHT
                        </span>
                        <p className="font-bold text-sm">Gerücht #{rumour.id.slice(0, 8)}</p>
                        <div className="flex items-center gap-2 mt-2">
                          <div className="h-1.5 flex-1 bg-gray-200 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-yellow-500 rounded-full"
                              style={{ width: `${rumour.confidence_score}%` }}
                            />
                          </div>
                          <span className="text-xs text-gray-500 font-medium">{rumour.confidence_score}%</span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="p-4 text-sm text-gray-500">Keine Gerüchte</p>
                )}
              </section>

              {/* Sidebar Middle Ad */}
              <SidebarAd slotKey="sidebar_middle" />

              {/* Quick Links Widget */}
              <section className="bg-white" data-testid="quick-links-widget">
                <div className="p-4 border-b border-gray-100">
                  <h3 
                    className="text-lg font-black uppercase"
                    style={{ fontFamily: "'Oswald', sans-serif" }}
                  >
                    Wettbewerbe
                  </h3>
                </div>
                <nav className="divide-y divide-gray-100">
                  {[
                    { name: "Bundesliga", slug: "bundesliga" },
                    { name: "Premier League", slug: "premier-league" },
                    { name: "La Liga", slug: "la-liga" },
                    { name: "Serie A", slug: "serie-a" },
                    { name: "Champions League", slug: "champions-league" },
                  ].map((league) => (
                    <Link
                      key={league.slug}
                      to={`/wettbewerb/${league.slug}`}
                      className="flex items-center justify-between p-3 hover:bg-gray-50 transition-colors group"
                    >
                      <span className="font-medium text-sm group-hover:text-[#79B92A] transition-colors">
                        {league.name}
                      </span>
                      <CaretRight size={16} className="text-gray-400 group-hover:text-[#79B92A]" />
                    </Link>
                  ))}
                </nav>
              </section>

              {/* Sidebar Bottom Ad */}
              <SidebarAd slotKey="sidebar_bottom" />
            </aside>
          </div>
        </div>
      </main>

      {/* Footer Ad */}
      <div className="bg-white border-t border-gray-200">
        <div className="max-w-[1200px] mx-auto px-3 py-4">
          <AdSlot slotKey="footer_top" minHeight="90px" />
        </div>
      </div>

      <Footer />
    </div>
  );
}
