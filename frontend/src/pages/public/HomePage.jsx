import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { HeroCard, NewsCardHorizontal, NewsTickerEntry } from "@/components/NewsCard";
import { TrendingWidget } from "@/components/TrendingWidget";
import { HotTransfers } from "@/components/HotTransfers";
import { WebsiteSchema } from "@/components/SchemaMarkup";
import { useEffect, useState } from "react";
import { getPublishedArticles } from "@/api";
import { Link } from "react-router-dom";
import { CaretRight } from "@phosphor-icons/react";
import { Helmet } from "react-helmet-async";

export default function HomePage() {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const newsRes = await getPublishedArticles({ limit: 20 });
        setArticles(newsRes.data);
      } catch (e) {
        console.error("Homepage load error:", e);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const heroArticle = articles[0];
  const feedArticles = articles.slice(1, 12);
  const tickerArticles = articles.slice(0, 10);

  return (
    <div className="min-h-screen flex flex-col bg-white" data-testid="homepage">
      <Helmet>
        <title>TransferNews.de - Alle Fußball-Transfers & Gerüchte</title>
        <meta name="description" content="Die neuesten Fußball-Transfer-News, Gerüchte und offizielle Wechsel. Bundesliga, Premier League, La Liga und mehr." />
        <meta name="robots" content="index, follow, max-image-preview:large" />
        <link rel="canonical" href="https://transfernews.de" />
      </Helmet>
      
      {/* Schema.org WebSite JSON-LD */}
      <WebsiteSchema />
      
      <Header />
      
      {/* Hot Transfers Section */}
      <HotTransfers />
      
      <main className="flex-1">
        {/* Main Content - Desktop: Hero + Sidebar nebeneinander */}
        <div className="max-w-[1000px] mx-auto px-3">
          <div className="lg:grid lg:grid-cols-[1fr_280px] lg:gap-4">
            {/* Left Column: Hero + News Feed */}
            <div>
              {/* Hero Section */}
              {heroArticle && (
                <HeroCard article={heroArticle} isLive={heroArticle.is_breaking} />
              )}
              
              {/* News Feed */}
              {feedArticles.map((article, idx) => (
                <NewsCardHorizontal key={article.id} article={article} showVideo={idx === 1} />
              ))}
            </div>
            
            {/* Sidebar Ticker + Trending - Desktop only */}
            <div className="hidden lg:block border-l border-gray-100">
              {/* Trending Widget */}
              <TrendingWidget className="m-4" />
              
              {/* Newsticker */}
              <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
                <Link to="/news" className="flex items-center gap-1 group">
                  <span className="text-sm font-bold uppercase">Newsticker</span>
                  <CaretRight size={14} weight="bold" className="text-gray-400" />
                </Link>
              </div>
              
              <div className="px-4">
                {tickerArticles.map((article) => (
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
      </main>

      <Footer />
    </div>
  );
}
