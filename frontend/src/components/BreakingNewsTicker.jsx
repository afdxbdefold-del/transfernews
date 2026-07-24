import { Link } from "react-router-dom";
import { Lightning } from "@phosphor-icons/react";
import { useEffect, useState } from "react";
import { getBreakingNews } from "@/api";

export default function BreakingNewsTicker() {
  const [breakingNews, setBreakingNews] = useState([]);

  useEffect(() => {
    const fetchBreaking = async () => {
      try {
        const res = await getBreakingNews({ limit: 10 });
        setBreakingNews(res.data);
      } catch (e) {
        console.error("Breaking news error:", e);
      }
    };
    fetchBreaking();
    // Refresh every 60 seconds
    const interval = setInterval(fetchBreaking, 60000);
    return () => clearInterval(interval);
  }, []);

  if (breakingNews.length === 0) {
    return null;
  }

  return (
    <div className="bg-red-600" data-testid="breaking-ticker">
      <div className="max-w-[1000px] mx-auto px-3">
        <div className="flex items-center h-10 overflow-hidden">
          {/* Breaking Label */}
          <div className="flex items-center flex-shrink-0 bg-white text-red-600 px-3 py-1 mr-4">
            <Lightning size={14} weight="fill" className="mr-1" />
            <span 
              className="text-xs font-black uppercase"
              style={{ fontFamily: "'Oswald', sans-serif" }}
            >
              BREAKING
            </span>
          </div>
          
          {/* Ticker Content */}
          <div className="ticker-wrap flex-1">
            <div className="ticker">
              {[...breakingNews, ...breakingNews].map((news, idx) => (
                <Link
                  key={idx}
                  to={`/news/${news.slug}`}
                  className="inline-block text-white text-sm font-medium hover:text-white/80 transition-colors mr-16"
                >
                  <span className="mr-2">+++</span>
                  {news.title}
                  <span className="ml-2">+++</span>
                </Link>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
