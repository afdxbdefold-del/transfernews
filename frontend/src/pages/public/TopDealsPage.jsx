import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { useEffect, useState } from "react";
import { getTopTransfers } from "@/api";
import { CaretRight, TrendUp } from "@phosphor-icons/react";
import { Link } from "react-router-dom";
import { Helmet } from "react-helmet-async";

function TopDealRow({ article, rank }) {
  const probability = article.transfer_probability || 0;
  
  return (
    <Link 
      to={`/news/${article.slug}`}
      className="flex items-center gap-3 p-2 hover:bg-[#e8f4e8] border-b border-gray-200 last:border-0 group"
      data-testid={`top-deal-${rank}`}
    >
      {/* Rank */}
      <div className={`w-7 h-7 flex-shrink-0 rounded flex items-center justify-center text-[12px] font-bold ${
        rank === 1 ? 'bg-yellow-400 text-yellow-900' :
        rank === 2 ? 'bg-gray-300 text-gray-700' :
        rank === 3 ? 'bg-amber-600 text-white' :
        'bg-gray-100 text-gray-600'
      }`}>
        {rank}
      </div>
      
      {/* Image */}
      <div className="w-[50px] h-[36px] flex-shrink-0 bg-gray-200 overflow-hidden rounded-sm">
        {article.image_url && (
          <img src={article.image_url} alt="" className="w-full h-full object-cover" />
        )}
      </div>
      
      {/* Content */}
      <div className="flex-1 min-w-0">
        <h3 className="text-[12px] font-semibold text-gray-900 group-hover:text-[#00a83f] line-clamp-1">
          {article.title}
        </h3>
        <div className="flex items-center gap-2 mt-0.5">
          <span className={`text-[9px] font-bold text-white px-1.5 py-0.5 rounded-sm ${
            article.article_type === 'transfer' ? 'bg-[#00a83f]' : 'bg-amber-500'
          }`}>
            {article.article_type === 'transfer' ? 'Bestätigt' : 'Gerücht'}
          </span>
        </div>
      </div>
      
      {/* Probability */}
      <div className="w-[80px] flex-shrink-0">
        <div className="flex items-center gap-1">
          <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
            <div 
              className={`h-full rounded-full ${probability >= 70 ? 'bg-[#00a83f]' : probability >= 40 ? 'bg-amber-500' : 'bg-red-500'}`}
              style={{ width: `${probability}%` }}
            />
          </div>
          <span className="text-[11px] font-bold text-gray-700 w-8 text-right">{probability}%</span>
        </div>
      </div>
      
      <CaretRight size={14} className="text-gray-400 flex-shrink-0" />
    </Link>
  );
}

export default function TopDealsPage() {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetch = async () => {
      try {
        const res = await getTopTransfers(30);
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
    <div className="min-h-screen flex flex-col bg-[#e8e8e8]" data-testid="top-deals-page">
      <Helmet>
        <title>Top-Transfers | TransferNews.de</title>
        <meta name="description" content="Die Transfer-Gerüchte mit der höchsten Wahrscheinlichkeit." />
        <link rel="canonical" href="https://transfernews.de/top-deals" />
      </Helmet>
      
      <Header />
      
      <main className="flex-1 py-3">
        <div className="max-w-[1000px] mx-auto px-3">
          <div className="bg-white border border-gray-300 rounded-sm overflow-hidden">
            <div className="bg-[#1d4370] px-3 py-2 flex items-center gap-2">
              <TrendUp size={16} className="text-white" />
              <h1 className="text-white text-[12px] font-bold uppercase">Top-Transfers nach Wahrscheinlichkeit</h1>
            </div>
            
            {/* Legend */}
            <div className="bg-gray-50 px-3 py-2 border-b border-gray-200 flex items-center gap-4 text-[10px]">
              <span className="text-gray-500">Legende:</span>
              <span className="flex items-center gap-1"><span className="w-3 h-2 bg-[#00a83f] rounded-sm"></span> Hoch (&gt;70%)</span>
              <span className="flex items-center gap-1"><span className="w-3 h-2 bg-amber-500 rounded-sm"></span> Mittel (40-70%)</span>
              <span className="flex items-center gap-1"><span className="w-3 h-2 bg-red-500 rounded-sm"></span> Niedrig (&lt;40%)</span>
            </div>
            
            {loading ? (
              <div className="divide-y divide-gray-200">
                {[...Array(10)].map((_, i) => (
                  <div key={i} className="flex items-center gap-3 p-2 animate-pulse">
                    <div className="w-7 h-7 bg-gray-200 rounded" />
                    <div className="w-[50px] h-[36px] bg-gray-200 rounded-sm" />
                    <div className="flex-1">
                      <div className="h-4 bg-gray-200 rounded w-3/4 mb-1" />
                      <div className="h-3 bg-gray-200 rounded w-16" />
                    </div>
                    <div className="w-[80px] h-2 bg-gray-200 rounded-full" />
                  </div>
                ))}
              </div>
            ) : articles.length > 0 ? (
              <div>
                {articles.map((article, idx) => (
                  <TopDealRow key={article.id} article={article} rank={idx + 1} />
                ))}
              </div>
            ) : (
              <div className="p-8 text-center text-gray-500 text-[13px]">
                Keine Top-Transfers mit Wahrscheinlichkeitsangabe vorhanden.
                <Link to="/" className="block mt-2 text-[#00a83f] hover:underline">
                  Alle News ansehen
                </Link>
              </div>
            )}
          </div>
        </div>
      </main>
      
      <Footer />
    </div>
  );
}
