import Header from "@/components/Header";
import Footer from "@/components/Footer";
import BreakingNewsTicker from "@/components/BreakingNewsTicker";
import { NewsCard, NewsCardCompact } from "@/components/NewsCard";
import { AdSlot, SidebarAd } from "@/components/AdSlot";
import { useEffect, useState } from "react";
import { getPublishedArticles, getConfirmedTransfers, getRumours } from "@/api";
import { Link } from "react-router-dom";
import { ArrowRight, TrendUp, Newspaper, Handshake } from "@phosphor-icons/react";
import { Badge } from "@/components/ui/badge";

export default function HomePage() {
  const [latestNews, setLatestNews] = useState([]);
  const [featuredNews, setFeaturedNews] = useState([]);
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
        
        const allNews = newsRes.data;
        setFeaturedNews(allNews.slice(0, 3));
        setLatestNews(allNews.slice(3, 15));
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

  return (
    <div className="min-h-screen flex flex-col bg-gray-50" data-testid="homepage">
      <Header />
      <BreakingNewsTicker />
      
      {/* Top Banner Ad */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-2">
          <AdSlot slotKey="below_header" minHeight="90px" />
        </div>
      </div>

      <main className="flex-1">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Main Content */}
            <div className="lg:col-span-2 space-y-8">
              {/* Featured News */}
              {featuredNews.length > 0 && (
                <section data-testid="featured-news">
                  <div className="flex items-center justify-between mb-6">
                    <h2 className="font-['Oswald'] text-2xl font-bold uppercase flex items-center">
                      <Newspaper size={24} className="mr-2 text-[#79B92A]" />
                      Top-News
                    </h2>
                    <Link to="/news" className="text-[#79B92A] text-sm font-medium hover:underline flex items-center">
                      Alle News <ArrowRight size={16} className="ml-1" />
                    </Link>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {featuredNews[0] && (
                      <div className="md:col-span-2">
                        <NewsCard article={featuredNews[0]} featured />
                      </div>
                    )}
                    {featuredNews.slice(1, 3).map((article) => (
                      <NewsCard key={article.id} article={article} />
                    ))}
                  </div>
                </section>
              )}

              {/* Feed Ad */}
              <AdSlot slotKey="homepage_feed_banner_1" minHeight="90px" />

              {/* Latest News */}
              <section data-testid="latest-news">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="font-['Oswald'] text-xl font-bold uppercase">
                    Aktuelle Meldungen
                  </h2>
                </div>
                <div className="space-y-3">
                  {latestNews.slice(0, 5).map((article) => (
                    <NewsCard key={article.id} article={article} />
                  ))}
                </div>
              </section>

              {/* Mid Feed Ad */}
              <AdSlot slotKey="homepage_feed_banner_2" minHeight="90px" />

              {/* More News */}
              <section>
                <div className="space-y-3">
                  {latestNews.slice(5, 10).map((article) => (
                    <NewsCard key={article.id} article={article} />
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

              {/* Latest Transfers Box */}
              <div className="bg-white border border-gray-200 p-4" data-testid="transfers-widget">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-['Oswald'] text-lg font-bold uppercase flex items-center">
                    <Handshake size={20} className="mr-2 text-[#79B92A]" />
                    Transfers
                  </h3>
                  <Link to="/transfers" className="text-[#79B92A] text-xs hover:underline">
                    Alle
                  </Link>
                </div>
                {transfers.length > 0 ? (
                  <div className="space-y-3">
                    {transfers.map((transfer) => (
                      <div key={transfer.id} className="text-sm border-b border-gray-100 pb-3 last:border-0">
                        <div className="flex items-center gap-2 mb-1">
                          <Badge className={transfer.status === "official" ? "badge-official" : "badge-confirmed"}>
                            {transfer.status === "official" ? "Offiziell" : "Bestätigt"}
                          </Badge>
                        </div>
                        <p className="font-medium">Transfer #{transfer.id.slice(0, 8)}</p>
                        {transfer.fee_amount && (
                          <p className="text-xs text-gray-500">
                            {transfer.fee_amount.toLocaleString("de-DE")} {transfer.fee_currency}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500">Keine Transfers</p>
                )}
              </div>

              {/* Sidebar Middle Ad */}
              <SidebarAd slotKey="sidebar_middle" />

              {/* Rumours Box */}
              <div className="bg-white border border-gray-200 p-4" data-testid="rumours-widget">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-['Oswald'] text-lg font-bold uppercase flex items-center">
                    <TrendUp size={20} className="mr-2 text-yellow-600" />
                    Gerüchte
                  </h3>
                  <Link to="/geruechte" className="text-[#79B92A] text-xs hover:underline">
                    Alle
                  </Link>
                </div>
                {rumours.length > 0 ? (
                  <div className="space-y-3">
                    {rumours.map((rumour) => (
                      <div key={rumour.id} className="text-sm border-b border-gray-100 pb-3 last:border-0">
                        <Badge className="badge-rumour mb-1">Gerücht</Badge>
                        <p className="font-medium">Gerücht #{rumour.id.slice(0, 8)}</p>
                        <div className="flex items-center gap-1 mt-1">
                          <div className="h-1.5 flex-1 bg-gray-200 rounded">
                            <div
                              className="h-full bg-yellow-500 rounded"
                              style={{ width: `${rumour.confidence_score}%` }}
                            />
                          </div>
                          <span className="text-xs text-gray-500">{rumour.confidence_score}%</span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500">Keine Gerüchte</p>
                )}
              </div>

              {/* Sidebar Bottom Ad */}
              <SidebarAd slotKey="sidebar_bottom" />
            </aside>
          </div>
        </div>
      </main>

      {/* Footer Ads */}
      <div className="bg-white border-t">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <AdSlot slotKey="footer_top" minHeight="90px" />
        </div>
      </div>

      <Footer />
    </div>
  );
}
