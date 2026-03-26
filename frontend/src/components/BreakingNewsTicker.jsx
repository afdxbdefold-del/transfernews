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
    <div className="bg-[#fee2e2] border-b border-red-200" data-testid="breaking-ticker">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center h-10 overflow-hidden">
          <div className="flex items-center flex-shrink-0 bg-red-600 text-white px-3 py-1 mr-4 text-xs font-bold uppercase">
            <Lightning size={14} weight="fill" className="mr-1 animate-pulse" />
            BREAKING
          </div>
          <div className="ticker-wrap flex-1">
            <div className="ticker">
              {[...breakingNews, ...breakingNews].map((news, idx) => (
                <Link
                  key={idx}
                  to={`/news/${news.slug}`}
                  className="inline-block text-red-800 text-sm font-medium hover:text-red-600 mr-12"
                >
                  {news.title}
                </Link>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
