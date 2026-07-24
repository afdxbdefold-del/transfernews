import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { NewsCardHorizontal } from "@/components/NewsCard";
import { TrendingWidget } from "@/components/TrendingWidget";
import { useEffect, useState } from "react";
import { getPublishedArticles } from "@/api";
import { CaretRight, Newspaper, Fire, Trophy, Funnel } from "@phosphor-icons/react";
import { NewsCardSkeleton } from "@/components/EnhancedSkeleton";
import { Link } from "react-router-dom";
import { Helmet } from "react-helmet-async";

import { HotTransfers } from "@/components/HotTransfers";
import { WebsiteSchema } from "@/components/SchemaMarkup";

const FILTERS = [
  { id: 'all', label: 'Alle', icon: Newspaper },
  { id: 'rumour', label: 'Gerüchte', icon: Fire },
  { id: 'transfer', label: 'Transfers', icon: Trophy },
  { id: 'news', label: 'News', icon: Newspaper },
];

const LEAGUES = [
  { slug: 'bundesliga', name: 'Bundesliga', flag: '🇩🇪' },
  { slug: 'premier-league', name: 'Premier League', flag: '🏴󠁧󠁢󠁥󠁮󠁧󠁿' },
  { slug: 'la-liga', name: 'La Liga', flag: '🇪🇸' },
  { slug: 'serie-a', name: 'Serie A', flag: '🇮🇹' },
  { slug: 'ligue-1', name: 'Ligue 1', flag: '🇫🇷' },
];

export default function HomePage() {
  const [articles, setArticles] = useState([]);
  const [filteredArticles, setFilteredArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeFilter, setActiveFilter] = useState('all');
  const [hasMore, setHasMore] = useState(true);
  const limit = 30;

  useEffect(() => {
    fetchArticles();
  }, []);

  useEffect(() => {
    if (activeFilter === 'all') {
      setFilteredArticles(articles);
    } else {
      setFilteredArticles(articles.filter(a => a.article_type === activeFilter));
    }
  }, [activeFilter, articles]);

  const fetchArticles = async (loadMore = false) => {
    try {
      setLoading(true);
      const skip = loadMore ? articles.length : 0;
      const res = await getPublishedArticles({ skip, limit });
      const data = Array.isArray(res.data) ? res.data : [];
      
      if (loadMore) {
        setArticles([...articles, ...data]);
      } else {
        setArticles(data);
      }
      setHasMore(data.length === limit);
    } catch (e) {
      console.error("News list error:", e);
    } finally {
      setLoading(false);
    }
  };

  const loadMore = () => {
    fetchArticles(true);
  };

  return (
    <div className="min-h-screen flex flex-col bg-gray-50 dark:bg-gray-950" data-testid="homepage">
      <Helmet>
        <title>TransferNews.de - Alle Fußball-Transfers & Gerüchte</title>
        <meta name="description" content="Die neuesten Fußball-Transfer-News, Gerüchte und offizielle Wechsel. Bundesliga, Premier League, La Liga und mehr." />
        <meta name="robots" content="index, follow, max-image-preview:large" />
        <link rel="canonical" href="https://transfernews.de" />
      </Helmet>
      
      <WebsiteSchema />
      
      <Header />
      
      {/* Hot Transfers Section */}
      <HotTransfers />

      <main className="flex-1">
        <div className="max-w-[1000px] mx-auto px-3 py-4">
          {/* Page Header with Filter Tabs */}
          <div className="bg-white dark:bg-gray-900 rounded-lg shadow-sm mb-4">
            <div className="p-4 border-b border-gray-100 dark:border-gray-800">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Newspaper size={28} weight="fill" className="text-[#79B92A]" />
                  <h1 
                    className="text-2xl md:text-3xl font-black uppercase text-gray-900 dark:text-white"
                    style={{ fontFamily: "'Oswald', sans-serif" }}
                    data-testid="page-title"
                  >
                    Transfer-News
                  </h1>
                </div>
              </div>
            </div>
            
            {/* Filter Tabs */}
            <div className="flex items-center gap-1 p-2 overflow-x-auto hide-scrollbar">
              {FILTERS.map((filter) => {
                const Icon = filter.icon;
                const isActive = activeFilter === filter.id;
                
                return (
                  <button
                    key={filter.id}
                    onClick={() => setActiveFilter(filter.id)}
                    className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-bold transition-all whitespace-nowrap ${
                      isActive 
                        ? 'bg-[#79B92A] text-white' 
                        : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
                    }`}
                    data-testid={`filter-${filter.id}`}
                  >
                    <Icon size={16} weight={isActive ? "fill" : "regular"} />
                    {filter.label}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-[1fr_280px] gap-4">
            {/* Main Content */}
            <div>
              <div className="bg-white dark:bg-gray-900 rounded-lg shadow-sm overflow-hidden">
                {loading && articles.length === 0 ? (
                  <div>
                    {[...Array(8)].map((_, i) => (
                      <NewsCardSkeleton key={i} />
                    ))}
                  </div>
                ) : (
                  <>
                    {/* News Cards with Images */}
                    <div>
                      {filteredArticles.map((article) => (
                        <NewsCardHorizontal key={article.id} article={article} />
                      ))}
                    </div>
                    
                    {hasMore && filteredArticles.length > 0 && (
                      <div className="p-4 border-t border-gray-100 dark:border-gray-800">
                        <button
                          onClick={loadMore}
                          disabled={loading}
                          className="w-full bg-[#79B92A] text-white py-3 font-black uppercase hover:bg-[#6aa325] transition-colors disabled:opacity-50 rounded-lg"
                          style={{ fontFamily: "'Oswald', sans-serif" }}
                          data-testid="load-more-btn"
                        >
                          {loading ? "LÄDT..." : "MEHR NEWS LADEN"}
                        </button>
                      </div>
                    )}

                    {filteredArticles.length === 0 && !loading && (
                      <div className="text-center py-12">
                        <Funnel size={48} className="mx-auto text-gray-300 dark:text-gray-600 mb-4" />
                        <p className="text-gray-500 dark:text-gray-400">Keine Artikel in dieser Kategorie</p>
                        <button 
                          onClick={() => setActiveFilter('all')}
                          className="mt-3 text-[#79B92A] font-bold hover:underline"
                        >
                          Alle anzeigen
                        </button>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>

            {/* Sidebar */}
            <aside className="space-y-4">
              {/* Trending Widget */}
              <TrendingWidget />
              
              {/* Liga Quick Links */}
              <div className="bg-white dark:bg-gray-900 rounded-lg shadow-sm overflow-hidden">
                <div className="p-3 border-b border-gray-100 dark:border-gray-800">
                  <h3 
                    className="text-sm font-black uppercase text-gray-900 dark:text-white flex items-center gap-2"
                    style={{ fontFamily: "'Oswald', sans-serif" }}
                  >
                    <Trophy size={16} weight="fill" className="text-[#79B92A]" />
                    Ligen
                  </h3>
                </div>
                <nav>
                  {LEAGUES.map((league) => (
                    <Link
                      key={league.slug}
                      to={`/wettbewerb/${league.slug}`}
                      className="flex items-center justify-between p-3 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors group border-b border-gray-50 dark:border-gray-800 last:border-0"
                    >
                      <div className="flex items-center gap-2">
                        <span className="text-lg">{league.flag}</span>
                        <span className="font-medium text-sm text-gray-700 dark:text-gray-300 group-hover:text-[#79B92A] transition-colors">
                          {league.name}
                        </span>
                      </div>
                      <CaretRight size={14} className="text-gray-400 group-hover:text-[#79B92A]" />
                    </Link>
                  ))}
                </nav>
              </div>
              
              {/* Categories */}
              <div className="bg-white dark:bg-gray-900 rounded-lg shadow-sm overflow-hidden">
                <div className="p-3 border-b border-gray-100 dark:border-gray-800">
                  <h3 
                    className="text-sm font-black uppercase text-gray-900 dark:text-white"
                    style={{ fontFamily: "'Oswald', sans-serif" }}
                  >
                    Kategorien
                  </h3>
                </div>
                <nav>
                  {[
                    { label: "Alle Transfers", path: "/" },
                    { label: "Gerüchte", path: "/geruechte" },
                    { label: "Redaktion", path: "/redaktion" },
                  ].map((item) => (
                    <Link
                      key={item.path}
                      to={item.path}
                      className="flex items-center justify-between p-3 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors group border-b border-gray-50 dark:border-gray-800 last:border-0"
                    >
                      <span className="font-medium text-sm text-gray-700 dark:text-gray-300 group-hover:text-[#79B92A] transition-colors">
                        {item.label}
                      </span>
                      <CaretRight size={14} className="text-gray-400 group-hover:text-[#79B92A]" />
                    </Link>
                  ))}
                </nav>
              </div>
            </aside>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
