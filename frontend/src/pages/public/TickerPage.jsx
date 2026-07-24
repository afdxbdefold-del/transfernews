import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { useEffect, useState, useRef } from "react";
import { getPublishedArticles } from "@/api";
import { Clock, Circle, CaretRight } from "@phosphor-icons/react";
import { Link } from "react-router-dom";
import { Helmet } from "react-helmet-async";

function formatTime(dateString) {
  if (!dateString) return "";
  const date = new Date(dateString);
  return date.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' });
}

function formatDate(dateString) {
  if (!dateString) return "";
  const date = new Date(dateString);
  const now = new Date();
  const isToday = date.toDateString() === now.toDateString();
  
  if (isToday) {
    return `Heute, ${formatTime(dateString)}`;
  }
  return date.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: '2-digit' }) + `, ${formatTime(dateString)}`;
}

function TickerRow({ article, isNew }) {
  const typeConfig = {
    rumour: { bg: "bg-amber-500", label: "Gerücht" },
    transfer: { bg: "bg-[#00a83f]", label: "Transfer" },
    news: { bg: "bg-[#1d4370]", label: "News" },
  };
  const type = typeConfig[article.article_type] || typeConfig.news;
  
  return (
    <Link 
      to={`/news/${article.slug}`}
      className="flex items-start gap-3 p-2 hover:bg-[#e8f4e8] border-b border-gray-200 last:border-0 group"
      data-testid={`ticker-${article.id}`}
    >
      {/* Time Column */}
      <div className="w-[70px] flex-shrink-0 text-right">
        <div className="text-[11px] font-semibold text-gray-700">{formatTime(article.published_at)}</div>
        {isNew && (
          <div className="text-[9px] font-bold text-red-600 mt-0.5">LIVE</div>
        )}
      </div>
      
      {/* Indicator */}
      <div className="flex-shrink-0 pt-1.5">
        <Circle 
          size={8} 
          weight="fill" 
          className={isNew ? "text-red-500 animate-pulse" : "text-gray-300"} 
        />
      </div>
      
      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-0.5">
          <span className={`text-[9px] font-bold text-white px-1.5 py-0.5 rounded-sm ${type.bg}`}>
            {type.label}
          </span>
          {article.is_breaking && (
            <span className="text-[9px] font-bold text-white px-1.5 py-0.5 rounded-sm bg-red-600">
              BREAKING
            </span>
          )}
        </div>
        <h3 className="text-[13px] font-semibold text-gray-900 group-hover:text-[#00a83f] line-clamp-2 leading-tight">
          {article.title}
        </h3>
        {article.excerpt && (
          <p className="text-[11px] text-gray-500 mt-0.5 line-clamp-1">{article.excerpt}</p>
        )}
      </div>
      
      <CaretRight size={14} className="text-gray-400 flex-shrink-0 mt-1" />
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
      setArticles(Array.isArray(res.data) ? res.data : []);
    } catch (e) {
      console.error("Ticker error:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchArticles();
    if (autoRefresh) {
      intervalRef.current = setInterval(fetchArticles, 30000);
    }
    return () => intervalRef.current && clearInterval(intervalRef.current);
  }, [autoRefresh]);

  const isNew = (publishedAt) => {
    if (!publishedAt) return false;
    return (new Date() - new Date(publishedAt)) / 3600000 < 1;
  };

  // Group articles by date
  const groupedArticles = articles.reduce((acc, article) => {
    const date = new Date(article.published_at);
    const key = date.toDateString();
    if (!acc[key]) acc[key] = [];
    acc[key].push(article);
    return acc;
  }, {});

  return (
    <div className="min-h-screen flex flex-col bg-[#e8e8e8]" data-testid="ticker-page">
      <Helmet>
        <title>News-Ticker - Live Updates | TransferNews.de</title>
        <meta name="description" content="Alle Transfer-News im Live-Ticker." />
        <link rel="canonical" href="https://transfernews.de/ticker" />
      </Helmet>
      
      <Header />
      
      <main className="flex-1 py-3">
        <div className="max-w-[1000px] mx-auto px-3">
          <div className="bg-white border border-gray-300 rounded-sm overflow-hidden">
            {/* Header */}
            <div className="bg-[#1d4370] px-3 py-2 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <h1 className="text-white text-[12px] font-bold uppercase">News-Ticker</h1>
                {autoRefresh && (
                  <span className="flex items-center gap-1 text-[10px] text-white/70">
                    <Circle size={6} weight="fill" className="text-red-500 animate-pulse" />
                    LIVE
                  </span>
                )}
              </div>
              <button
                onClick={() => setAutoRefresh(!autoRefresh)}
                className={`text-[10px] px-2 py-1 rounded ${
                  autoRefresh ? 'bg-red-500 text-white' : 'bg-white/20 text-white'
                }`}
              >
                {autoRefresh ? 'Auto-Update AN' : 'Auto-Update AUS'}
              </button>
            </div>
            
            {/* Ticker Content */}
            {loading ? (
              <div className="divide-y divide-gray-200">
                {[...Array(15)].map((_, i) => (
                  <div key={i} className="flex items-start gap-3 p-2 animate-pulse">
                    <div className="w-[70px] h-4 bg-gray-200 rounded" />
                    <div className="w-2 h-2 bg-gray-200 rounded-full mt-1" />
                    <div className="flex-1">
                      <div className="h-3 bg-gray-200 rounded w-20 mb-2" />
                      <div className="h-4 bg-gray-200 rounded w-full" />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              Object.entries(groupedArticles).map(([dateKey, dateArticles]) => (
                <div key={dateKey}>
                  {/* Date Header */}
                  <div className="bg-gray-100 px-3 py-1.5 border-b border-gray-200 sticky top-0">
                    <span className="text-[11px] font-bold text-gray-600">
                      {new Date(dateKey).toLocaleDateString('de-DE', { 
                        weekday: 'long', 
                        day: '2-digit', 
                        month: 'long',
                        year: 'numeric'
                      })}
                    </span>
                  </div>
                  {dateArticles.map((article) => (
                    <TickerRow key={article.id} article={article} isNew={isNew(article.published_at)} />
                  ))}
                </div>
              ))
            )}
          </div>
        </div>
      </main>
      
      <Footer />
    </div>
  );
}
