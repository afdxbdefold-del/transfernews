import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { NewsCard } from "@/components/NewsCard";
import { AdSlot, SidebarAd } from "@/components/AdSlot";
import { useEffect, useState } from "react";
import { getPublishedArticles } from "@/api";
import { Newspaper } from "@phosphor-icons/react";
import { Skeleton } from "@/components/ui/skeleton";

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
    <div className="min-h-screen flex flex-col bg-gray-50" data-testid="news-list-page">
      <Header />
      
      {/* Top Ad */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-2">
          <AdSlot slotKey="below_header" minHeight="90px" />
        </div>
      </div>

      <main className="flex-1">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Page Title */}
          <div className="mb-8">
            <h1 className="font-['Oswald'] text-4xl font-bold uppercase flex items-center" data-testid="page-title">
              <Newspaper size={36} className="mr-3 text-[#00a651]" />
              Transfer-News
            </h1>
            <p className="text-gray-500 mt-2">
              Alle aktuellen Nachrichten aus der Welt des Fußball-Transfermarkts
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Main Content */}
            <div className="lg:col-span-2">
              {loading && articles.length === 0 ? (
                <div className="space-y-4">
                  {[...Array(5)].map((_, i) => (
                    <div key={i} className="bg-white border p-4">
                      <Skeleton className="h-6 w-3/4 mb-3" />
                      <Skeleton className="h-4 w-full mb-2" />
                      <Skeleton className="h-4 w-1/2" />
                    </div>
                  ))}
                </div>
              ) : (
                <div className="space-y-4">
                  {articles.map((article, idx) => (
                    <div key={article.id}>
                      <NewsCard article={article} featured={idx === 0} />
                      {/* Insert ad after every 4th article */}
                      {(idx + 1) % 4 === 0 && idx < articles.length - 1 && (
                        <div className="my-4">
                          <AdSlot slotKey={`listing_after_card_${idx + 1}`} minHeight="90px" />
                        </div>
                      )}
                    </div>
                  ))}
                  
                  {hasMore && (
                    <div className="text-center py-8">
                      <button
                        onClick={loadMore}
                        disabled={loading}
                        className="bg-[#00a651] text-white px-8 py-3 font-bold uppercase hover:bg-[#008c45] transition-colors disabled:opacity-50"
                        data-testid="load-more-btn"
                      >
                        {loading ? "Lädt..." : "Mehr laden"}
                      </button>
                    </div>
                  )}

                  {articles.length === 0 && !loading && (
                    <div className="text-center py-12 bg-white border">
                      <Newspaper size={48} className="mx-auto text-gray-300 mb-4" />
                      <p className="text-gray-500">Noch keine News vorhanden</p>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Sidebar */}
            <aside className="space-y-6">
              <SidebarAd slotKey="sidebar_top" />
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
