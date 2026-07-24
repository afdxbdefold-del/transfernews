import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { NewsCardHorizontal } from "@/components/NewsCard";
import { useEffect, useState } from "react";
import { getPublishedArticles } from "@/api";
import { TrendUp, Fire } from "@phosphor-icons/react";
import { Skeleton } from "@/components/ui/skeleton";
import { Link } from "react-router-dom";
import { Helmet } from "react-helmet-async";

export default function RumoursPage() {
  const [rumours, setRumours] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const res = await getPublishedArticles({ limit: 50 });
        console.log('Raw response:', res);
        console.log('res.data type:', typeof res.data);
        
        // Axios wraps in data - handle both cases
        let articles = [];
        if (Array.isArray(res.data)) {
          articles = res.data;
        } else if (Array.isArray(res)) {
          articles = res;
        } else if (res.data?.articles) {
          articles = res.data.articles;
        }
        
        console.log('Articles count:', articles.length);
        
        // Filter für Gerüchte
        const rumourArticles = articles.filter(
          a => a.article_type === 'rumour' || a.article_type === 'gerücht'
        );
        console.log('Rumours found:', rumourArticles.length);
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
    <div className="min-h-screen flex flex-col bg-gray-50" data-testid="rumours-page">
      <Helmet>
        <title>Transfer-Gerüchte - TransferNews</title>
        <meta name="description" content="Die heißesten Transfer-Gerüchte und Spekulationen vom Transfermarkt. Alle Wechsel-News zu Bayern, BVB, Real Madrid und mehr." />
      </Helmet>
      
      <Header />

      <main className="flex-1">
        <div className="max-w-[1000px] mx-auto px-4 py-6">
          {/* Page Header */}
          <div className="mb-6 border-b-4 border-amber-500 pb-4">
            <h1 className="text-3xl font-black uppercase flex items-center gap-3" style={{ fontFamily: "'Oswald', sans-serif" }} data-testid="page-title">
              <Fire size={32} weight="fill" className="text-amber-500" />
              Transfer-Gerüchte
            </h1>
            <p className="text-gray-500 mt-2">
              {rumours.length} aktuelle Gerüchte und Spekulationen vom Transfermarkt
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Main Content */}
            <div className="lg:col-span-2">
              {loading ? (
                <div className="space-y-3">
                  {[...Array(5)].map((_, i) => (
                    <div key={i} className="bg-white border p-4">
                      <Skeleton className="h-6 w-3/4 mb-3" />
                      <Skeleton className="h-4 w-1/2" />
                    </div>
                  ))}
                </div>
              ) : rumours.length > 0 ? (
                <div className="bg-white border border-gray-200">
                  {rumours.map((article) => (
                    <NewsCardHorizontal key={article.id} article={article} />
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 bg-white border">
                  <TrendUp size={48} className="mx-auto text-gray-300 mb-4" />
                  <p className="text-gray-500">Noch keine Gerüchte vorhanden</p>
                </div>
              )}
            </div>

            {/* Sidebar */}
            <aside className="space-y-6">
              {/* Hot Rumours Box */}
              <div className="bg-gradient-to-br from-amber-500 to-orange-500 rounded-lg p-4 text-white">
                <h3 className="font-bold uppercase text-sm mb-3 flex items-center gap-2">
                  <Fire size={18} weight="fill" />
                  Heißeste Gerüchte
                </h3>
                <div className="space-y-2">
                  {rumours.slice(0, 3).map((r, idx) => (
                    <Link 
                      key={r.id}
                      to={`/news/${r.slug}`}
                      className="block bg-white/10 rounded p-2 hover:bg-white/20 transition"
                    >
                      <span className="text-yellow-300 font-bold mr-2">#{idx + 1}</span>
                      <span className="text-sm">{r.player_name || r.title?.split(':')[0]}</span>
                    </Link>
                  ))}
                </div>
              </div>
              
              {/* Liga Filter */}
              <div className="bg-white border border-gray-200 p-4">
                <h3 className="font-bold uppercase text-sm mb-3">Nach Liga filtern</h3>
                <div className="space-y-2">
                  <Link to="/wettbewerb/bundesliga" className="flex items-center gap-2 hover:text-[#79B92A]">
                    <span>🇩🇪</span> Bundesliga
                  </Link>
                  <Link to="/wettbewerb/premier-league" className="flex items-center gap-2 hover:text-[#79B92A]">
                    <span>🏴󠁧󠁢󠁥󠁮󠁧󠁿</span> Premier League
                  </Link>
                  <Link to="/wettbewerb/la-liga" className="flex items-center gap-2 hover:text-[#79B92A]">
                    <span>🇪🇸</span> La Liga
                  </Link>
                  <Link to="/wettbewerb/serie-a" className="flex items-center gap-2 hover:text-[#79B92A]">
                    <span>🇮🇹</span> Serie A
                  </Link>
                </div>
              </div>
            </aside>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
