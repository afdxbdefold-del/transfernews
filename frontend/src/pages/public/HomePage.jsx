import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { HeroCard, NewsCardHorizontal, NewsTickerEntry } from "@/components/NewsCard";
import { AdSlot, SidebarAd } from "@/components/AdSlot";
import { useEffect, useState } from "react";
import { getPublishedArticles, getConfirmedTransfers, getRumours } from "@/api";
import { Link } from "react-router-dom";
import { CaretRight } from "@phosphor-icons/react";

export default function HomePage() {
  const [articles, setArticles] = useState([]);
  const [transfers, setTransfers] = useState([]);
  const [rumours, setRumours] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [newsRes, transfersRes, rumoursRes] = await Promise.all([
          getPublishedArticles({ limit: 20 }),
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

  const heroArticle = articles[0];
  const feedArticles = articles.slice(1, 10);
  const tickerArticles = articles.slice(0, 8);

  return (
    <div className="min-h-screen flex flex-col bg-white" data-testid="homepage">
      <Header />
      
      <main className="flex-1">
        {/* Hero Section */}
        {heroArticle && (
          <div className="max-w-[1280px] mx-auto">
            <HeroCard article={heroArticle} isLive={heroArticle.is_breaking} />
          </div>
        )}
        
        {/* Ad below hero */}
        <div className="max-w-[1280px] mx-auto px-4 py-3">
          <AdSlot slotKey="below_header" minHeight="90px" />
        </div>
        
        {/* Main Content */}
        <div className="max-w-[1280px] mx-auto">
          {/* Desktop: 2 columns (Feed + Ticker) */}
          <div className="lg:flex">
            {/* News Feed */}
            <div className="flex-1">
              {feedArticles.map((article, idx) => (
                <div key={article.id}>
                  <NewsCardHorizontal article={article} showVideo={idx === 1} />
                  {idx === 2 && (
                    <div className="p-3">
                      <AdSlot slotKey="homepage_feed_banner_1" minHeight="90px" />
                    </div>
                  )}
                  {idx === 5 && (
                    <div className="p-3">
                      <AdSlot slotKey="homepage_feed_banner_2" minHeight="90px" />
                    </div>
                  )}
                </div>
              ))}
            </div>
            
            {/* Sidebar Ticker - Desktop only */}
            <div className="hidden lg:block w-[340px] border-l border-gray-100">
              {/* Newsticker Header */}
              <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
                <Link to="/news" className="flex items-center gap-1 group">
                  <span className="text-sm font-bold uppercase">Newsticker</span>
                  <CaretRight size={14} weight="bold" className="text-gray-400" />
                </Link>
              </div>
              
              {/* Ticker List */}
              <div className="px-4">
                {tickerArticles.map((article) => (
                  <NewsTickerEntry key={article.id} article={article} />
                ))}
              </div>
              
              {/* All News Button */}
              <div className="p-4">
                <Link 
                  to="/news" 
                  className="block w-full bg-black text-white text-center text-sm font-bold uppercase py-3"
                >
                  ALLE NEWS ANZEIGEN
                </Link>
              </div>
              
              {/* Sidebar Ads */}
              <div className="p-4 space-y-4">
                <SidebarAd slotKey="sidebar_top" />
                <SidebarAd slotKey="sidebar_middle" />
              </div>
            </div>
          </div>
          
          {/* Mobile: Newsticker Section */}
          <div className="lg:hidden border-t border-gray-200 mt-4">
            <div className="flex items-center justify-between px-4 py-3 bg-gray-50">
              <Link to="/news" className="flex items-center gap-1">
                <span className="text-sm font-bold uppercase">Newsticker</span>
                <CaretRight size={14} weight="bold" className="text-gray-400" />
              </Link>
            </div>
            <div className="px-4">
              {tickerArticles.slice(0, 5).map((article) => (
                <NewsTickerEntry key={article.id} article={article} />
              ))}
            </div>
            <div className="p-4">
              <Link to="/news" className="block w-full bg-black text-white text-center text-sm font-bold uppercase py-3">
                ALLE NEWS ANZEIGEN
              </Link>
            </div>
          </div>
        </div>
        
        {/* Bottom Ad */}
        <div className="max-w-[1280px] mx-auto px-4 py-4">
          <AdSlot slotKey="footer_top" minHeight="90px" />
        </div>
      </main>

      <Footer />
    </div>
  );
}
