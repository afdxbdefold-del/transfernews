import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { useEffect, useState } from "react";
import { getFreeTransfers } from "@/api";
import { UserCircle, Calendar, ArrowRight, Buildings } from "@phosphor-icons/react";
import { Link } from "react-router-dom";
import { Helmet } from "react-helmet-async";

function FreeAgentCard({ article }) {
  // Extract player info from article
  const playerName = article.player_name || article.title?.split(' ')[0] || 'Unbekannt';
  const contractUntil = article.contract_until || '2025';
  
  return (
    <Link 
      to={`/news/${article.slug}`}
      className="block bg-white dark:bg-gray-900 rounded-lg shadow-sm overflow-hidden hover:shadow-md transition-shadow group"
      data-testid={`free-agent-${article.id}`}
    >
      <div className="flex">
        {/* Player Image */}
        <div className="w-24 h-24 md:w-32 md:h-32 flex-shrink-0 bg-gray-200 dark:bg-gray-800 overflow-hidden">
          {article.image_url ? (
            <img 
              src={article.image_url} 
              alt={article.title} 
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <UserCircle size={48} className="text-gray-400" />
            </div>
          )}
        </div>
        
        <div className="flex-1 p-3 md:p-4 min-w-0">
          {/* Status Badge */}
          <div className="flex items-center gap-2 mb-2">
            <span className="text-[10px] font-bold text-white px-2 py-0.5 rounded bg-purple-600">
              ABLÖSEFREI
            </span>
            {article.article_type === 'transfer' && (
              <span className="text-[10px] font-bold text-white px-2 py-0.5 rounded bg-emerald-500">
                BESTÄTIGT
              </span>
            )}
            {article.article_type === 'rumour' && (
              <span className="text-[10px] font-bold text-white px-2 py-0.5 rounded bg-amber-500">
                GERÜCHT
              </span>
            )}
          </div>
          
          {/* Title */}
          <h3 
            className="font-bold text-gray-900 dark:text-white group-hover:text-[#79B92A] transition-colors line-clamp-2"
            style={{ fontFamily: "'Oswald', sans-serif" }}
          >
            {article.title}
          </h3>
          
          {/* Meta Info */}
          <div className="flex items-center gap-3 mt-2 text-xs text-gray-500 dark:text-gray-400">
            {contractUntil && (
              <span className="flex items-center gap-1">
                <Calendar size={12} />
                Vertrag bis {contractUntil}
              </span>
            )}
          </div>
          
          {/* Probability if available */}
          {article.transfer_probability > 0 && (
            <div className="mt-2 flex items-center gap-2">
              <div className="flex-1 h-1.5 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-[#79B92A] rounded-full"
                  style={{ width: `${article.transfer_probability}%` }}
                />
              </div>
              <span className="text-xs font-bold text-[#79B92A]">{article.transfer_probability}%</span>
            </div>
          )}
        </div>
      </div>
    </Link>
  );
}

export default function FreeAgentsPage() {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchFreeAgents = async () => {
      try {
        const res = await getFreeTransfers();
        setArticles(res.data?.articles || []);
      } catch (e) {
        console.error("Free agents fetch error:", e);
      } finally {
        setLoading(false);
      }
    };
    
    fetchFreeAgents();
  }, []);

  return (
    <div className="min-h-screen flex flex-col bg-gray-100 dark:bg-gray-950" data-testid="free-agents-page">
      <Helmet>
        <title>Ablösefrei - Vertragslose Spieler | TransferNews.de</title>
        <meta name="description" content="Alle ablösefreien Spieler und auslaufende Verträge. Top-Stars ohne Ablöse: Wer wechselt wohin?" />
        <meta name="robots" content="index, follow" />
        <link rel="canonical" href="https://transfernews.de/abloesefrei" />
      </Helmet>
      
      <Header />
      
      <main className="flex-1">
        <div className="max-w-[1000px] mx-auto px-3 py-4">
          {/* Header */}
          <div className="bg-gradient-to-r from-purple-600 to-purple-800 text-white rounded-lg p-6 mb-6">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 bg-white/20 rounded-full flex items-center justify-center">
                <UserCircle size={32} weight="fill" />
              </div>
              <div>
                <h1 
                  className="text-3xl md:text-4xl font-black uppercase"
                  style={{ fontFamily: "'Oswald', sans-serif" }}
                  data-testid="page-title"
                >
                  Ablösefrei
                </h1>
                <p className="text-white/80 mt-1">Spieler mit auslaufenden Verträgen & ablösefreie Transfers</p>
              </div>
            </div>
          </div>
          
          {/* Info Box */}
          <div className="bg-purple-50 dark:bg-purple-950/30 border border-purple-200 dark:border-purple-800 rounded-lg p-4 mb-6">
            <div className="flex items-start gap-3">
              <Buildings size={24} className="text-purple-600 flex-shrink-0 mt-0.5" />
              <div>
                <h2 className="font-bold text-purple-900 dark:text-purple-100">Ablösefreie Transfers</h2>
                <p className="text-sm text-purple-700 dark:text-purple-300 mt-1">
                  Spieler, deren Vertrag ausläuft oder bereits ausgelaufen ist, können ablösefrei wechseln. 
                  Dies ermöglicht spektakuläre Transfers ohne Ablösesumme.
                </p>
              </div>
            </div>
          </div>
          
          {/* Content */}
          {loading ? (
            <div className="space-y-3">
              {[...Array(8)].map((_, i) => (
                <div key={i} className="bg-white dark:bg-gray-900 rounded-lg overflow-hidden animate-pulse">
                  <div className="flex">
                    <div className="w-24 h-24 md:w-32 md:h-32 bg-gray-200 dark:bg-gray-800" />
                    <div className="flex-1 p-4">
                      <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-24 mb-3" />
                      <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2" />
                      <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : articles.length > 0 ? (
            <div className="space-y-3">
              {articles.map((article) => (
                <FreeAgentCard key={article.id} article={article} />
              ))}
            </div>
          ) : (
            <div className="bg-white dark:bg-gray-900 rounded-lg p-12 text-center">
              <UserCircle size={64} className="mx-auto text-gray-300 dark:text-gray-600 mb-4" />
              <h2 className="text-xl font-bold text-gray-700 dark:text-gray-300 mb-2">Keine ablösefreien Spieler</h2>
              <p className="text-gray-500 dark:text-gray-400 mb-4">Aktuell sind keine Artikel über ablösefreie Transfers vorhanden.</p>
              <Link 
                to="/"
                className="inline-flex items-center gap-2 text-[#79B92A] font-bold hover:underline"
              >
                Alle News ansehen <ArrowRight size={16} />
              </Link>
            </div>
          )}
        </div>
      </main>
      
      <Footer />
    </div>
  );
}
