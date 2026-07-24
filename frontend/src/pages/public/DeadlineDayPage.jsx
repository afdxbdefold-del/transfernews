import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { useEffect, useState, useRef } from "react";
import { getPublishedArticles, getBreakingArticles } from "@/api";
import { Clock, Circle, CaretRight, Calendar } from "@phosphor-icons/react";
import { Link } from "react-router-dom";
import { Helmet } from "react-helmet-async";

const getNextDeadline = () => {
  const now = new Date();
  const year = now.getFullYear();
  const summerDeadline = new Date(year, 7, 31, 23, 59, 59);
  const winterDeadline = new Date(year, 0, 31, 23, 59, 59);
  const nextWinterDeadline = new Date(year + 1, 0, 31, 23, 59, 59);
  
  if (now < winterDeadline) return { date: winterDeadline, name: "Winter-Transferfenster", season: "winter" };
  if (now < summerDeadline) return { date: summerDeadline, name: "Sommer-Transferfenster", season: "summer" };
  return { date: nextWinterDeadline, name: "Winter-Transferfenster", season: "winter" };
};

function CountdownBox({ value, label }) {
  return (
    <div className="bg-[#1d4370] text-white px-3 py-2 rounded text-center min-w-[60px]">
      <div className="text-2xl md:text-3xl font-bold">{String(value).padStart(2, '0')}</div>
      <div className="text-[10px] uppercase text-white/70">{label}</div>
    </div>
  );
}

function NewsRow({ article, isHot }) {
  const typeConfig = {
    rumour: { bg: "bg-amber-500", label: "Gerücht" },
    transfer: { bg: "bg-[#00a83f]", label: "Transfer" },
    news: { bg: "bg-[#1d4370]", label: "News" },
  };
  const type = typeConfig[article.article_type] || typeConfig.news;
  
  return (
    <Link 
      to={`/news/${article.slug}`}
      className={`flex items-start gap-3 p-2 hover:bg-[#e8f4e8] border-b border-gray-200 last:border-0 group ${isHot ? 'bg-red-50' : ''}`}
    >
      <div className="w-[70px] h-[50px] flex-shrink-0 bg-gray-200 overflow-hidden rounded-sm">
        {article.image_url && <img src={article.image_url} alt="" className="w-full h-full object-cover" />}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-0.5">
          <span className={`text-[9px] font-bold text-white px-1.5 py-0.5 rounded-sm ${type.bg}`}>{type.label}</span>
          {article.is_breaking && <span className="text-[9px] font-bold text-white px-1.5 py-0.5 rounded-sm bg-red-600">BREAKING</span>}
          {isHot && <span className="text-[9px] font-bold text-red-600">HOT</span>}
          <span className="text-[10px] text-gray-500 flex items-center gap-0.5">
            <Clock size={10} />
            {new Date(article.published_at).toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>
        <h3 className="text-[13px] font-semibold text-gray-900 group-hover:text-[#00a83f] line-clamp-2 leading-tight">{article.title}</h3>
      </div>
      <CaretRight size={14} className="text-gray-400 flex-shrink-0 mt-2" />
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

  useEffect(() => {
    const updateCountdown = () => {
      const now = new Date();
      const diff = deadline.date - now;
      if (diff <= 0) {
        setCountdown({ days: 0, hours: 0, minutes: 0, seconds: 0 });
        setIsDeadlineDay(true);
        return;
      }
      setIsDeadlineDay(deadline.date.toDateString() === now.toDateString());
      setCountdown({
        days: Math.floor(diff / (1000 * 60 * 60 * 24)),
        hours: Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60)),
        minutes: Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60)),
        seconds: Math.floor((diff % (1000 * 60)) / 1000),
      });
    };
    updateCountdown();
    const timer = setInterval(updateCountdown, 1000);
    return () => clearInterval(timer);
  }, [deadline]);

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
        console.error("Error:", e);
      } finally {
        setLoading(false);
      }
    };
    fetchNews();
    if (isDeadlineDay) intervalRef.current = setInterval(fetchNews, 60000);
    return () => intervalRef.current && clearInterval(intervalRef.current);
  }, [isDeadlineDay]);

  return (
    <div className="min-h-screen flex flex-col bg-[#e8e8e8]" data-testid="deadline-day-page">
      <Helmet>
        <title>Deadline Day - Transfer-Countdown | TransferNews.de</title>
        <meta name="description" content={`Countdown zum ${deadline.name}. Alle Breaking News am Deadline Day.`} />
        <link rel="canonical" href="https://transfernews.de/deadline-day" />
      </Helmet>
      
      <Header />
      
      <main className="flex-1 py-3">
        <div className="max-w-[1000px] mx-auto px-3 space-y-3">
          {/* Countdown Box */}
          <div className={`border rounded-sm overflow-hidden ${isDeadlineDay ? 'border-red-500 bg-red-600' : 'border-gray-300 bg-[#1d4370]'}`}>
            <div className="p-4 text-center">
              <div className="flex items-center justify-center gap-2 mb-2">
                <Calendar size={18} className="text-white" />
                <span className="text-white text-[12px] font-bold uppercase">{deadline.name} {deadline.date.getFullYear()}</span>
                {isDeadlineDay && <span className="bg-white text-red-600 px-2 py-0.5 rounded text-[10px] font-bold animate-pulse">LIVE</span>}
              </div>
              <h1 className="text-white text-xl md:text-2xl font-bold mb-3">
                {isDeadlineDay ? 'DEADLINE DAY LÄUFT!' : 'Countdown zum Deadline Day'}
              </h1>
              <div className="flex justify-center gap-2 md:gap-4">
                <CountdownBox value={countdown.days} label="Tage" />
                <CountdownBox value={countdown.hours} label="Std" />
                <CountdownBox value={countdown.minutes} label="Min" />
                <CountdownBox value={countdown.seconds} label="Sek" />
              </div>
              <p className="text-white/70 text-[11px] mt-3">
                {deadline.date.toLocaleDateString('de-DE', { weekday: 'long', day: '2-digit', month: 'long', year: 'numeric' })}, 23:59 Uhr
              </p>
            </div>
          </div>
          
          {/* Breaking News */}
          {breakingNews.length > 0 && (
            <div className="bg-white border border-red-500 rounded-sm overflow-hidden">
              <div className="bg-red-600 px-3 py-2 flex items-center gap-2">
                <Circle size={8} weight="fill" className="text-white animate-pulse" />
                <span className="text-white text-[12px] font-bold uppercase">Breaking News</span>
              </div>
              <div>
                {breakingNews.map((article) => (
                  <NewsRow key={article.id} article={article} isHot={true} />
                ))}
              </div>
            </div>
          )}
          
          {/* All News */}
          <div className="bg-white border border-gray-300 rounded-sm overflow-hidden">
            <div className="bg-[#1d4370] px-3 py-2 flex items-center justify-between">
              <span className="text-white text-[12px] font-bold uppercase">Alle News</span>
              {isDeadlineDay && (
                <span className="text-[10px] text-white/70 flex items-center gap-1">
                  <Circle size={6} weight="fill" className="text-green-400 animate-pulse" />
                  Auto-Update
                </span>
              )}
            </div>
            {loading ? (
              <div className="divide-y divide-gray-200">
                {[...Array(10)].map((_, i) => (
                  <div key={i} className="flex items-start gap-3 p-2 animate-pulse">
                    <div className="w-[70px] h-[50px] bg-gray-200 rounded-sm" />
                    <div className="flex-1">
                      <div className="h-3 bg-gray-200 rounded w-20 mb-2" />
                      <div className="h-4 bg-gray-200 rounded w-full" />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div>
                {latestNews.map((article, idx) => (
                  <NewsRow key={article.id} article={article} isHot={idx < 3 && isDeadlineDay} />
                ))}
              </div>
            )}
          </div>
          
          {/* Info Box */}
          {!isDeadlineDay && (
            <div className="bg-white border border-gray-300 rounded-sm p-4">
              <h2 className="font-bold text-[13px] text-gray-900 mb-2">Was ist der Deadline Day?</h2>
              <p className="text-[12px] text-gray-600 leading-relaxed">
                Der Deadline Day markiert das Ende des Transferfensters. An diesem Tag müssen alle Transfers 
                bis Mitternacht abgeschlossen sein. Oft kommt es zu Last-Minute-Deals und überraschenden Wechseln.
              </p>
              <div className="mt-3 flex items-center gap-4 text-[11px] text-gray-500">
                <span className="flex items-center gap-1"><span className="w-2 h-2 bg-[#00a83f] rounded-full"></span> Sommer: 31. August</span>
                <span className="flex items-center gap-1"><span className="w-2 h-2 bg-blue-500 rounded-full"></span> Winter: 31. Januar</span>
              </div>
            </div>
          )}
        </div>
      </main>
      
      <Footer />
    </div>
  );
}
