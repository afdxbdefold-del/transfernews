import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { useEffect, useState, useRef } from "react";
import { getPublishedArticles, getBreakingArticles } from "@/api";
import { Clock, Lightning, Siren, Bell, Fire, Trophy, ArrowRight, Calendar } from "@phosphor-icons/react";
import { Link } from "react-router-dom";
import { Helmet } from "react-helmet-async";

// Transfer window deadlines (adjust year dynamically)
const getNextDeadline = () => {
  const now = new Date();
  const year = now.getFullYear();
  
  // Summer window: typically ends August 31
  const summerDeadline = new Date(year, 7, 31, 23, 59, 59); // Aug 31, 23:59
  // Winter window: typically ends January 31
  const winterDeadline = new Date(year, 0, 31, 23, 59, 59); // Jan 31, 23:59
  const nextWinterDeadline = new Date(year + 1, 0, 31, 23, 59, 59);
  
  // Find the next upcoming deadline
  if (now < winterDeadline) {
    return { date: winterDeadline, name: "Winter-Transferfenster", season: "winter" };
  } else if (now < summerDeadline) {
    return { date: summerDeadline, name: "Sommer-Transferfenster", season: "summer" };
  } else {
    return { date: nextWinterDeadline, name: "Winter-Transferfenster", season: "winter" };
  }
};

function CountdownUnit({ value, label }) {
  return (
    <div className="flex flex-col items-center">
      <div className="bg-black text-white text-3xl md:text-5xl font-black w-16 md:w-24 h-16 md:h-24 flex items-center justify-center rounded-lg shadow-lg"
           style={{ fontFamily: "'Oswald', sans-serif" }}>
        {String(value).padStart(2, '0')}
      </div>
      <span className="text-xs md:text-sm text-gray-600 dark:text-gray-400 mt-2 uppercase font-bold tracking-wider">
        {label}
      </span>
    </div>
  );
}

function BreakingCard({ article }) {
  return (
    <Link 
      to={`/news/${article.slug}`}
      className="block bg-red-600 text-white p-4 rounded-lg hover:bg-red-700 transition-colors group animate-pulse-slow"
      data-testid={`breaking-${article.id}`}
    >
      <div className="flex items-start gap-3">
        <Lightning size={24} weight="fill" className="flex-shrink-0 mt-1" />
        <div className="flex-1 min-w-0">
          <span className="text-xs font-bold bg-white/20 px-2 py-0.5 rounded">BREAKING</span>
          <h3 className="font-bold text-lg mt-2 line-clamp-2" style={{ fontFamily: "'Oswald', sans-serif" }}>
            {article.title}
          </h3>
          {article.excerpt && (
            <p className="text-sm text-white/80 mt-1 line-clamp-1">{article.excerpt}</p>
          )}
        </div>
      </div>
    </Link>
  );
}

function DeadlineNewsCard({ article, isHot }) {
  const typeConfig = {
    rumour: { bg: "bg-amber-500", label: "GERÜCHT" },
    transfer: { bg: "bg-emerald-500", label: "TRANSFER" },
    news: { bg: "bg-blue-500", label: "NEWS" },
  };
  const type = typeConfig[article.article_type] || typeConfig.news;
  
  return (
    <Link 
      to={`/news/${article.slug}`}
      className={`block bg-white dark:bg-gray-900 rounded-lg overflow-hidden hover:shadow-lg transition-shadow group ${isHot ? 'ring-2 ring-red-500' : ''}`}
      data-testid={`deadline-news-${article.id}`}
    >
      <div className="flex">
        {/* Image */}
        <div className="w-24 h-24 md:w-32 md:h-32 flex-shrink-0 bg-gray-200 dark:bg-gray-800 overflow-hidden relative">
          {article.image_url ? (
            <img src={article.image_url} alt="" className="w-full h-full object-cover" />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <Trophy size={32} className="text-gray-400" />
            </div>
          )}
          {isHot && (
            <div className="absolute top-1 left-1 bg-red-500 text-white p-1 rounded">
              <Fire size={14} weight="fill" />
            </div>
          )}
        </div>
        
        <div className="flex-1 p-3 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-[10px] font-bold text-white px-2 py-0.5 rounded ${type.bg}`}>
              {type.label}
            </span>
            {article.is_breaking && (
              <span className="text-[10px] font-bold text-white px-2 py-0.5 rounded bg-red-500">
                BREAKING
              </span>
            )}
            <span className="text-xs text-gray-500">
              {new Date(article.published_at).toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })}
            </span>
          </div>
          
          <h3 className="font-bold text-gray-900 dark:text-white group-hover:text-[#79B92A] transition-colors line-clamp-2"
              style={{ fontFamily: "'Oswald', sans-serif" }}>
            {article.title}
          </h3>
          
          {article.transfer_probability > 0 && (
            <div className="mt-2 flex items-center gap-2">
              <div className="flex-1 h-1.5 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                <div className="h-full bg-[#79B92A] rounded-full" style={{ width: `${article.transfer_probability}%` }} />
              </div>
              <span className="text-xs font-bold text-[#79B92A]">{article.transfer_probability}%</span>
            </div>
          )}
        </div>
      </div>
    </Link>
  );
}

export default function DeadlineDayPage() {
  const [countdown, setCountdown] = useState({ days: 0, hours: 0, minutes: 0, seconds: 0 });
  const [deadline] = useState(getNextDeadline());
  const [breakingNews, setBreakingNews] = useState([]);
  const [latestNews, setLatestNews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isDeadlineDay, setIsDeadlineDay] = useState(false);
  const intervalRef = useRef(null);

  // Countdown calculation
  useEffect(() => {
    const updateCountdown = () => {
      const now = new Date();
      const diff = deadline.date - now;
      
      if (diff <= 0) {
        setCountdown({ days: 0, hours: 0, minutes: 0, seconds: 0 });
        setIsDeadlineDay(true);
        return;
      }
      
      // Check if it's deadline day (same day)
      const isToday = deadline.date.toDateString() === now.toDateString();
      setIsDeadlineDay(isToday);
      
      const days = Math.floor(diff / (1000 * 60 * 60 * 24));
      const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
      const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
      const seconds = Math.floor((diff % (1000 * 60)) / 1000);
      
      setCountdown({ days, hours, minutes, seconds });
    };
    
    updateCountdown();
    const timer = setInterval(updateCountdown, 1000);
    return () => clearInterval(timer);
  }, [deadline]);

  // Fetch news
  useEffect(() => {
    const fetchNews = async () => {
      try {
        const [breakingRes, latestRes] = await Promise.all([
          getBreakingArticles(5),
          getPublishedArticles({ limit: 20 })
        ]);
        
        setBreakingNews(breakingRes.data?.breaking_news || []);
        setLatestNews(Array.isArray(latestRes.data) ? latestRes.data : []);
      } catch (e) {
        console.error("Deadline news fetch error:", e);
      } finally {
        setLoading(false);
      }
    };
    
    fetchNews();
    
    // Auto-refresh every 60 seconds on deadline day
    if (isDeadlineDay) {
      intervalRef.current = setInterval(fetchNews, 60000);
    }
    
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [isDeadlineDay]);

  const formatDeadlineDate = () => {
    return deadline.date.toLocaleDateString('de-DE', {
      weekday: 'long',
      day: '2-digit',
      month: 'long',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className={`min-h-screen flex flex-col ${isDeadlineDay ? 'bg-red-950' : 'bg-gray-100 dark:bg-gray-950'}`} data-testid="deadline-day-page">
      <Helmet>
        <title>Deadline Day - Transfer-Countdown | TransferNews.de</title>
        <meta name="description" content={`Countdown zum ${deadline.name}. Alle Breaking News und Last-Minute-Transfers am Deadline Day.`} />
        <meta name="robots" content="index, follow" />
        <link rel="canonical" href="https://transfernews.de/deadline-day" />
      </Helmet>
      
      <Header />
      
      <main className="flex-1">
        <div className="max-w-[1000px] mx-auto px-3 py-4">
          {/* Hero Section */}
          <div className={`rounded-lg p-6 md:p-8 mb-6 text-center relative overflow-hidden ${
            isDeadlineDay 
              ? 'bg-gradient-to-r from-red-600 to-red-800' 
              : 'bg-gradient-to-r from-gray-900 to-black'
          }`}>
            {/* Background Pattern */}
            <div className="absolute inset-0 opacity-10">
              <div className="absolute inset-0" style={{
                backgroundImage: 'repeating-linear-gradient(45deg, transparent, transparent 10px, rgba(255,255,255,0.1) 10px, rgba(255,255,255,0.1) 20px)'
              }} />
            </div>
            
            <div className="relative z-10">
              {/* Status Badge */}
              {isDeadlineDay ? (
                <div className="inline-flex items-center gap-2 bg-white text-red-600 px-4 py-2 rounded-full font-bold text-sm mb-4 animate-bounce">
                  <Siren size={20} weight="fill" className="animate-pulse" />
                  DEADLINE DAY LÄUFT!
                  <Siren size={20} weight="fill" className="animate-pulse" />
                </div>
              ) : (
                <div className="inline-flex items-center gap-2 bg-[#79B92A] text-white px-4 py-2 rounded-full font-bold text-sm mb-4">
                  <Calendar size={18} weight="fill" />
                  {deadline.name} {deadline.date.getFullYear()}
                </div>
              )}
              
              {/* Title */}
              <h1 
                className="text-4xl md:text-6xl font-black text-white uppercase mb-2"
                style={{ fontFamily: "'Oswald', sans-serif" }}
                data-testid="page-title"
              >
                Deadline Day
              </h1>
              <p className="text-white/70 mb-6">
                {formatDeadlineDate()}
              </p>
              
              {/* Countdown */}
              <div className="flex justify-center gap-3 md:gap-6 mb-6">
                <CountdownUnit value={countdown.days} label="Tage" />
                <CountdownUnit value={countdown.hours} label="Std" />
                <CountdownUnit value={countdown.minutes} label="Min" />
                <CountdownUnit value={countdown.seconds} label="Sek" />
              </div>
              
              {/* Alert Section */}
              {isDeadlineDay && (
                <div className="bg-white/10 backdrop-blur rounded-lg p-4 max-w-md mx-auto">
                  <div className="flex items-center gap-3 text-white">
                    <Bell size={24} weight="fill" className="animate-bounce" />
                    <span className="font-bold">Auto-Refresh aktiv - News werden automatisch aktualisiert</span>
                  </div>
                </div>
              )}
            </div>
          </div>
          
          {/* Breaking News Section */}
          {breakingNews.length > 0 && (
            <div className="mb-6">
              <div className="flex items-center gap-2 mb-3">
                <Lightning size={24} weight="fill" className="text-red-500" />
                <h2 className="text-xl font-black uppercase text-gray-900 dark:text-white" 
                    style={{ fontFamily: "'Oswald', sans-serif" }}>
                  Breaking News
                </h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {breakingNews.map((article) => (
                  <BreakingCard key={article.id} article={article} />
                ))}
              </div>
            </div>
          )}
          
          {/* Latest News */}
          <div className="bg-white dark:bg-gray-900 rounded-lg shadow-sm overflow-hidden">
            <div className="p-4 border-b border-gray-100 dark:border-gray-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Clock size={20} weight="fill" className="text-[#79B92A]" />
                <h2 className="text-lg font-black uppercase text-gray-900 dark:text-white"
                    style={{ fontFamily: "'Oswald', sans-serif" }}>
                  Alle News
                </h2>
              </div>
              {isDeadlineDay && (
                <span className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1">
                  <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                  Live
                </span>
              )}
            </div>
            
            {loading ? (
              <div className="divide-y divide-gray-100 dark:divide-gray-800">
                {[...Array(8)].map((_, i) => (
                  <div key={i} className="flex p-3 animate-pulse">
                    <div className="w-24 h-24 bg-gray-200 dark:bg-gray-800 rounded" />
                    <div className="flex-1 p-3">
                      <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-24 mb-2" />
                      <div className="h-5 bg-gray-200 dark:bg-gray-700 rounded w-3/4" />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="divide-y divide-gray-100 dark:divide-gray-800">
                {latestNews.map((article, idx) => (
                  <DeadlineNewsCard 
                    key={article.id} 
                    article={article} 
                    isHot={idx < 3 && isDeadlineDay}
                  />
                ))}
              </div>
            )}
          </div>
          
          {/* Info Box */}
          {!isDeadlineDay && (
            <div className="mt-6 bg-gray-800 text-white rounded-lg p-6">
              <h3 className="font-bold text-lg mb-3 flex items-center gap-2">
                <Calendar size={20} weight="fill" />
                Was ist der Deadline Day?
              </h3>
              <p className="text-gray-300 text-sm leading-relaxed">
                Der Deadline Day markiert das Ende des Transferfensters. An diesem Tag müssen alle Transfers 
                bis Mitternacht abgeschlossen sein. Oft kommt es zu Last-Minute-Deals und überraschenden Wechseln. 
                Die Spannung steigt, wenn die Uhr tickt und Vereine versuchen, ihre Kader zu verstärken.
              </p>
              <div className="mt-4 flex items-center gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-[#79B92A] rounded-full" />
                  <span>Sommer: 31. August</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-blue-500 rounded-full" />
                  <span>Winter: 31. Januar</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
      
      <Footer />
      
      {/* Custom Animation Styles */}
      <style>{`
        @keyframes pulse-slow {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.85; }
        }
        .animate-pulse-slow {
          animation: pulse-slow 2s ease-in-out infinite;
        }
      `}</style>
    </div>
  );
}
