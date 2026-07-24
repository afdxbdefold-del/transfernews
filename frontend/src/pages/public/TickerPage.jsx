import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { useEffect, useState, useRef } from "react";
import { getPublishedArticles } from "@/api";
import { Lightning, Circle, Clock } from "@phosphor-icons/react";
import { Link } from "react-router-dom";
import { Helmet } from "react-helmet-async";

function formatTimeAgo(dateString) {
  if (!dateString) return "";
  const now = new Date();
  const date = new Date(dateString);
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);
  
  if (diffMins < 1) return "Gerade eben";
  if (diffMins < 60) return `vor ${diffMins} Min.`;
  if (diffHours < 24) return `vor ${diffHours} Std.`;
  if (diffDays < 7) return `vor ${diffDays} Tag${diffDays > 1 ? 'en' : ''}`;
  return date.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit' });
}

function TickerItem({ article, isNew }) {
  const typeColors = {
    rumour: { bg: "bg-amber-500", text: "GERÜCHT" },
    transfer: { bg: "bg-emerald-500", text: "TRANSFER" },
    news: { bg: "bg-blue-500", text: "NEWS" },
  };
  
  const type = typeColors[article.article_type] || typeColors.news;
  const isBreaking = article.is_breaking;
  
  return (
    <Link 
      to={`/news/${article.slug}`}
      className={`block border-l-4 ${isBreaking ? 'border-red-500 bg-red-50 dark:bg-red-950/30' : 'border-[#79B92A] bg-white dark:bg-gray-900'} p-4 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors group`}
      data-testid={`ticker-item-${article.id}`}
    >
      <div className="flex items-start gap-3">
        {/* Live Indicator */}
        <div className="flex-shrink-0 pt-1">
          {isBreaking ? (
            <Lightning size={20} weight="fill" className="text-red-500 animate-pulse" />
          ) : (
            <Circle size={10} weight="fill" className={`${isNew ? 'text-[#79B92A]' : 'text-gray-300 dark:text-gray-600'}`} />
          )}
        </div>
        
        <div className="flex-1 min-w-0">
          {/* Time and Type */}
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1">
              <Clock size={12} />
              {formatTimeAgo(article.published_at)}
            </span>
            <span className={`text-[10px] font-bold text-white px-2 py-0.5 rounded ${type.bg}`}>
              {type.text}
            </span>
            {isBreaking && (
              <span className="text-[10px] font-bold text-white px-2 py-0.5 rounded bg-red-500 animate-pulse">
                BREAKING
              </span>
            )}
          </div>
          
          {/* Title */}
          <h3 className="font-bold text-gray-900 dark:text-white group-hover:text-[#79B92A] transition-colors line-clamp-2"
              style={{ fontFamily: "'Oswald', sans-serif" }}>
            {article.title}
          </h3>
          
          {/* Subtitle/Excerpt */}
          {article.excerpt && (
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1 line-clamp-1">
              {article.excerpt}
            </p>
          )}
        </div>
        
        {/* Thumbnail */}
        {article.image_url && (
          <div className="flex-shrink-0 w-16 h-16 rounded overflow-hidden">
            <img 
              src={article.image_url} 
              alt="" 
              className="w-full h-full object-cover"
            />
          </div>
        )}
      </div>
    </Link>
  );
}

export default function TickerPage() {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const intervalRef = useRef(null);

  const fetchArticles = async () => {
    try {
      const res = await getPublishedArticles({ limit: 50 });
      const data = Array.isArray(res.data) ? res.data : [];
      setArticles(data);
    } catch (e) {
      console.error("Ticker fetch error:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchArticles();
    
    // Auto-refresh every 30 seconds
    if (autoRefresh) {
      intervalRef.current = setInterval(fetchArticles, 30000);
    }
    
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [autoRefresh]);

  const isNewArticle = (publishedAt) => {
    if (!publishedAt) return false;
    const now = new Date();
    const published = new Date(publishedAt);
    const diffHours = (now - published) / 3600000;
    return diffHours < 1;
  };

  return (
    <div className="min-h-screen flex flex-col bg-gray-100 dark:bg-gray-950" data-testid="ticker-page">
      <Helmet>
        <title>Transfer-Ticker - Live Updates | TransferNews.de</title>
        <meta name="description" content="Alle Fußball-Transfer-News im Live-Ticker. Aktuelle Gerüchte, bestätigte Wechsel und Breaking News in Echtzeit." />
        <meta name="robots" content="index, follow" />
        <link rel="canonical" href="https://transfernews.de/ticker" />
      </Helmet>
      
      <Header />
      
      <main className="flex-1">
        <div className="max-w-[1000px] mx-auto px-3 py-4">
          {/* Header */}
          <div className="bg-black text-white rounded-lg p-4 mb-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-red-500 rounded-full flex items-center justify-center animate-pulse">
                  <Lightning size={24} weight="fill" />
                </div>
                <div>
                  <h1 
                    className="text-2xl md:text-3xl font-black uppercase"
                    style={{ fontFamily: "'Oswald', sans-serif" }}
                    data-testid="page-title"
                  >
                    Transfer-Ticker
                  </h1>
                  <p className="text-sm text-gray-400">Live-Updates aus der Transfer-Welt</p>
                </div>
              </div>
              
              {/* Auto-Refresh Toggle */}
              <button
                onClick={() => setAutoRefresh(!autoRefresh)}
                className={`flex items-center gap-2 px-3 py-2 rounded-full text-sm font-medium transition-colors ${
                  autoRefresh 
                    ? 'bg-[#79B92A] text-white' 
                    : 'bg-gray-700 text-gray-300'
                }`}
                data-testid="auto-refresh-toggle"
              >
                <Circle size={8} weight="fill" className={autoRefresh ? 'animate-pulse' : ''} />
                {autoRefresh ? 'LIVE' : 'PAUSIERT'}
              </button>
            </div>
          </div>
          
          {/* Ticker Content */}
          <div className="bg-white dark:bg-gray-900 rounded-lg shadow-sm overflow-hidden">
            {loading ? (
              <div className="space-y-0">
                {[...Array(10)].map((_, i) => (
                  <div key={i} className="border-l-4 border-gray-200 p-4 animate-pulse">
                    <div className="flex items-start gap-3">
                      <div className="w-3 h-3 rounded-full bg-gray-200 dark:bg-gray-700" />
                      <div className="flex-1">
                        <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-24 mb-2" />
                        <div className="h-5 bg-gray-200 dark:bg-gray-700 rounded w-3/4" />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="divide-y divide-gray-100 dark:divide-gray-800">
                {articles.map((article) => (
                  <TickerItem 
                    key={article.id} 
                    article={article} 
                    isNew={isNewArticle(article.published_at)}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </main>
      
      <Footer />
    </div>
  );
}
