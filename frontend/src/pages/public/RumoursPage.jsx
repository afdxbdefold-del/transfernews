import Header from "@/components/Header";
import Footer from "@/components/Footer";
import PageLayout from "@/components/PageLayout";
import StandardSidebar from "@/components/StandardSidebar";
import { NewsCardHorizontal } from "@/components/NewsCard";
import { useEffect, useState } from "react";
import { getPublishedArticles } from "@/api";
import { TrendUp, Fire } from "@phosphor-icons/react";
import { Skeleton } from "@/components/ui/skeleton";
import { Helmet } from "react-helmet-async";

export default function RumoursPage() {
  const [rumours, setRumours] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const res = await getPublishedArticles({ limit: 50 });
        let articles = Array.isArray(res.data) ? res.data : res.data?.articles || [];
        const rumourArticles = articles.filter(
          a => a.article_type === 'rumour' || a.article_type === 'gerücht'
        );
        setRumours(rumourArticles);
      } catch (e) {
        console.error("Rumours load error:", e);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  return (
    <PageLayout>
      <Helmet>
        <title>Transfer-Gerüchte - TransferNews</title>
        <meta name="description" content="Die heißesten Transfer-Gerüchte und Spekulationen vom Transfermarkt." />
      </Helmet>
      
      <Header />

      <main className="flex-1 py-3 px-3" data-testid="rumours-page">
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_300px] gap-3">
          {/* Main Content */}
          <div>
            <div className="bg-white border border-gray-300 rounded-sm overflow-hidden">
              <div className="bg-[#79B92A] px-3 py-2.5 flex items-center gap-2">
                <Fire size={18} className="text-white" weight="fill" />
                <h1 className="text-white text-[13px] font-bold uppercase">Transfer-Gerüchte</h1>
                <span className="text-white/70 text-[11px] ml-auto">{rumours.length} Gerüchte</span>
              </div>

              {loading ? (
                <div className="divide-y divide-gray-200">
                  {[...Array(5)].map((_, i) => (
                    <div key={i} className="p-3">
                      <Skeleton className="h-5 w-3/4 mb-2" />
                      <Skeleton className="h-4 w-1/2" />
                    </div>
                  ))}
                </div>
              ) : rumours.length > 0 ? (
                <div className="divide-y divide-gray-200">
                  {rumours.map((article) => (
                    <NewsCardHorizontal key={article.id} article={article} />
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <TrendUp size={48} className="mx-auto text-gray-300 mb-4" />
                  <p className="text-gray-500 text-[13px]">Noch keine Gerüchte vorhanden</p>
                </div>
              )}
            </div>
          </div>

          {/* Sidebar */}
          <StandardSidebar />
        </div>
      </main>

      <Footer />
    </PageLayout>
  );
}
