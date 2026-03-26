import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { NewsCard, NewsTickerEntry } from "@/components/NewsCard";
import { AdSlot, SidebarAd } from "@/components/AdSlot";
import { useEffect, useState } from "react";
import { getPublishedArticles } from "@/api";
import { CaretRight } from "@phosphor-icons/react";
import { Skeleton } from "@/components/ui/skeleton";
import { Link } from "react-router-dom";

export default function NewsListPage() {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const limit = 20;

  useEffect(() => {
    fetchArticles();
  }, []);

  const fetchArticles = async (loadMore = false) => {
    try {
      setLoading(true);
      const skip = loadMore ? articles.length : 0;
      const res = await getPublishedArticles({ skip, limit });
      
      if (loadMore) {
        setArticles([...articles, ...res.data]);
      } else {
        setArticles(res.data);
      }
      setHasMore(res.data.length === limit);
    } catch (e) {
      console.error("News list error:", e);
    } finally {
      setLoading(false);
    }
  };

  const loadMore = () => {
    setPage(page + 1);
    fetchArticles(true);
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#f5f5f5]" data-testid="news-list-page">
      <Header />
      
      {/* Top Ad */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-[1200px] mx-auto px-3 py-2">
          <AdSlot slotKey="below_header" minHeight="90px" />
        </div>
      </div>

      <main className="flex-1">
        <div className="max-w-[1200px] mx-auto px-3 py-6">
          {/* Page Header */}
          <div className="bg-white p-4 mb-6">
            <div className="flex items-center gap-2">
              <h1 
                className="text-2xl md:text-3xl font-black uppercase"
                style={{ fontFamily: "'Oswald', sans-serif" }}
                data-testid="page-title"
              >
                Newsticker
              </h1>
              <CaretRight size={24} weight="bold" className="text-[#79B92A]" />
            </div>
            <p className="text-gray-500 text-sm mt-1">
              Alle aktuellen Transfer-News und Fußball-Meldungen
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Main Content */}
            <div className="lg:col-span-2">
              <div className="bg-white">
                {loading && articles.length === 0 ? (
                  <div className="divide-y divide-gray-100">
                    {[...Array(8)].map((_, i) => (
                      <div key={i} className="p-4">
                        <Skeleton className="h-5 w-3/4 mb-2" />
                        <Skeleton className="h-4 w-1/2" />
                      </div>
                    ))}
                  </div>
                ) : (
                  <>
                    {/* Newsticker Style List */}
                    <div className="divide-y divide-gray-100">
                      {articles.map((article, idx) => (
                        <div key={article.id}>
                          <NewsTickerEntry article={article} />
                          {/* Insert ad after every 6th article */}
                          {(idx + 1) % 6 === 0 && idx < articles.length - 1 && (
                            <div className="p-4 border-t border-gray-100">
                              <AdSlot slotKey={`listing_after_card_${idx + 1}`} minHeight="90px" />
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                    
                    {hasMore && (
                      <div className="p-4 border-t border-gray-100">
                        <button
                          onClick={loadMore}
                          disabled={loading}
                          className="w-full bg-[#79B92A] text-white py-3 font-black uppercase hover:bg-[#6aa325] transition-colors disabled:opacity-50"
                          style={{ fontFamily: "'Oswald', sans-serif" }}
                          data-testid="load-more-btn"
                        >
                          {loading ? "LÄDT..." : "MEHR NEWS LADEN"}
                        </button>
                      </div>
                    )}

                    {articles.length === 0 && !loading && (
                      <div className="text-center py-12">
                        <p className="text-gray-500">Noch keine News vorhanden</p>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>

            {/* Sidebar */}
            <aside className="space-y-6">
              <SidebarAd slotKey="sidebar_top" />
              
              {/* Quick Links */}
              <div className="bg-white">
                <div className="p-4 border-b border-gray-100">
                  <h3 
                    className="text-lg font-black uppercase"
                    style={{ fontFamily: "'Oswald', sans-serif" }}
                  >
                    Kategorien
                  </h3>
                </div>
                <nav className="divide-y divide-gray-100">
                  {[
                    { label: "Transfers", path: "/transfers" },
                    { label: "Gerüchte", path: "/geruechte" },
                    { label: "Bundesliga", path: "/wettbewerb/bundesliga" },
                    { label: "Premier League", path: "/wettbewerb/premier-league" },
                  ].map((item) => (
                    <Link
                      key={item.path}
                      to={item.path}
                      className="flex items-center justify-between p-3 hover:bg-gray-50 transition-colors group"
                    >
                      <span className="font-medium text-sm group-hover:text-[#79B92A] transition-colors">
                        {item.label}
                      </span>
                      <CaretRight size={16} className="text-gray-400 group-hover:text-[#79B92A]" />
                    </Link>
                  ))}
                </nav>
              </div>
              
              <SidebarAd slotKey="sidebar_middle" />
              <SidebarAd slotKey="sidebar_bottom" />
            </aside>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
