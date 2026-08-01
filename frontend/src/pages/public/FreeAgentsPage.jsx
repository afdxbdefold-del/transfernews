import Header from "@/components/Header";
import Footer from "@/components/Footer";
import PageLayout from "@/components/PageLayout";
import StandardSidebar from "@/components/StandardSidebar";
import { useEffect, useState } from "react";
import { getFreeTransfers } from "@/api";
import { CaretRight, Calendar, UserCircle } from "@phosphor-icons/react";
import { Link } from "react-router-dom";
import { Helmet } from "react-helmet-async";

function FreeAgentRow({ article }) {
  // Use hero_image or image_url as fallback (API returns hero_image)
  const imageUrl = article.hero_image || article.image_url;
  
  return (
    <a href={`/news/${article.slug}`}
      className="flex items-center gap-3 p-2 hover:bg-[#e8f4e8] border-b border-gray-200 last:border-0 group"
      data-testid={`free-agent-${article.id}`}
    >
      {/* Image */}
      <div className="w-[50px] h-[50px] flex-shrink-0 bg-gray-200 overflow-hidden rounded-sm">
        {imageUrl ? (
          <img src={imageUrl} alt="" className="w-full h-full object-cover" referrerPolicy="no-referrer" />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <UserCircle size={24} className="text-gray-400" />
          </div>
        )}
      </div>
      
      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-0.5">
          <span className="text-[9px] font-bold text-white px-1.5 py-0.5 rounded-sm bg-purple-600">
            Ablösefrei
          </span>
          {article.article_type === 'transfer' && (
            <span className="text-[9px] font-bold text-white px-1.5 py-0.5 rounded-sm bg-[#00a83f]">
              Bestätigt
            </span>
          )}
          {article.article_type === 'rumour' && (
            <span className="text-[9px] font-bold text-white px-1.5 py-0.5 rounded-sm bg-amber-500">
              Gerücht
            </span>
          )}
        </div>
        <h3 className="text-[12px] font-semibold text-gray-900 group-hover:text-[#00a83f] line-clamp-1">
          {article.title}
        </h3>
        {article.contract_until && (
          <div className="flex items-center gap-1 mt-0.5 text-[10px] text-gray-500">
            <Calendar size={10} />
            Vertrag bis {article.contract_until}
          </div>
        )}
      </div>
      
      {/* Probability */}
      {article.transfer_probability > 0 && (
        <div className="w-[60px] flex-shrink-0 text-right">
          <span className="text-[12px] font-bold text-[#00a83f]">{article.transfer_probability}%</span>
        </div>
      )}
      
      <CaretRight size={14} className="text-gray-400 flex-shrink-0" />
    </a>
  );
}

export default function FreeAgentsPage() {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetch = async () => {
      try {
        const res = await getFreeTransfers();
        setArticles(res.data?.articles || []);
      } catch (e) {
        console.error("Error:", e);
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, []);

  return (
    <PageLayout>
      <Helmet>
        <title>Ablösefreie Spieler | TransferNews.de</title>
        <meta name="description" content="Alle ablösefreien Spieler und auslaufende Verträge." />
        <link rel="canonical" href="https://transfernews.de/abloesefrei" />
      </Helmet>
      
      <Header />
      
      <main className="flex-1 py-3 px-3" data-testid="free-agents-page">
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_300px] gap-3">
          {/* Main Content */}
          <div>
        <div className="bg-white border border-gray-300 rounded-sm overflow-hidden">
            <div className="bg-[#79B92A] px-3 py-2 flex items-center gap-2">
              <UserCircle size={16} className="text-white" />
              <h1 className="text-white text-[12px] font-bold uppercase">Ablösefreie Spieler & Verträge</h1>
            </div>
            
            {/* Info Box */}
            <div className="bg-purple-50 px-3 py-2 border-b border-purple-200 text-[11px] text-purple-800">
              Spieler, deren Vertrag ausläuft oder bereits ausgelaufen ist, können ablösefrei wechseln.
            </div>
            
            {loading ? (
              <div className="divide-y divide-gray-200">
                {[...Array(8)].map((_, i) => (
                  <div key={i} className="flex items-center gap-3 p-2 animate-pulse">
                    <div className="w-[50px] h-[50px] bg-gray-200 rounded-sm" />
                    <div className="flex-1">
                      <div className="h-3 bg-gray-200 rounded w-20 mb-2" />
                      <div className="h-4 bg-gray-200 rounded w-3/4" />
                    </div>
                  </div>
                ))}
              </div>
            ) : articles.length > 0 ? (
              <div>
                {articles.map((article) => (
                  <FreeAgentRow key={article.id} article={article} />
                ))}
              </div>
            ) : (
              <div className="p-8 text-center text-gray-500 text-[13px]">
                Keine Artikel über ablösefreie Spieler vorhanden.
                <Link to="/" className="block mt-2 text-[#00a83f] hover:underline">
                  Alle News ansehen
                </Link>
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
