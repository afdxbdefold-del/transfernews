import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { useEffect, useState } from "react";
import { getTopTransfers } from "@/api";
import { Trophy, TrendUp, CurrencyEur, ArrowRight } from "@phosphor-icons/react";
import { Link } from "react-router-dom";
import { Helmet } from "react-helmet-async";

function formatFee(amount) {
  if (!amount) return "Unbekannt";
  if (amount >= 1000000) {
    return `${(amount / 1000000).toFixed(1)} Mio. €`;
  }
  return `${(amount / 1000).toFixed(0)} Tsd. €`;
}

function TopDealCard({ article, rank }) {
  const probability = article.transfer_probability || 0;
  
  return (
    <Link 
      to={`/news/${article.slug}`}
      className="block bg-white dark:bg-gray-900 rounded-lg shadow-sm overflow-hidden hover:shadow-md transition-shadow group"
      data-testid={`top-deal-${rank}`}
    >
      <div className="relative">
        {/* Image */}
        <div className="aspect-[16/9] bg-gray-200 dark:bg-gray-800 overflow-hidden">
          {article.image_url ? (
            <img 
              src={article.image_url} 
              alt={article.title} 
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <Trophy size={48} className="text-gray-400" />
            </div>
          )}
        </div>
        
        {/* Rank Badge */}
        <div className={`absolute top-3 left-3 w-10 h-10 rounded-full flex items-center justify-center font-black text-lg ${
          rank === 1 ? 'bg-yellow-400 text-yellow-900' :
          rank === 2 ? 'bg-gray-300 text-gray-700' :
          rank === 3 ? 'bg-amber-600 text-white' :
          'bg-black/70 text-white'
        }`} style={{ fontFamily: "'Oswald', sans-serif" }}>
          {rank}
        </div>
        
        {/* Probability Badge */}
        {probability > 0 && (
          <div className="absolute top-3 right-3 bg-[#79B92A] text-white px-3 py-1 rounded-full font-bold text-sm flex items-center gap-1">
            <TrendUp size={14} weight="bold" />
            {probability}%
          </div>
        )}
      </div>
      
      <div className="p-4">
        {/* Type Badge */}
        <div className="flex items-center gap-2 mb-2">
          <span className={`text-[10px] font-bold text-white px-2 py-0.5 rounded ${
            article.article_type === 'transfer' ? 'bg-emerald-500' :
            article.article_type === 'rumour' ? 'bg-amber-500' : 'bg-blue-500'
          }`}>
            {article.article_type === 'transfer' ? 'BESTÄTIGT' :
             article.article_type === 'rumour' ? 'GERÜCHT' : 'NEWS'}
          </span>
          {article.fee_amount && (
            <span className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1">
              <CurrencyEur size={12} />
              {formatFee(article.fee_amount)}
            </span>
          )}
        </div>
        
        {/* Title */}
        <h3 
          className="font-bold text-lg text-gray-900 dark:text-white group-hover:text-[#79B92A] transition-colors line-clamp-2"
          style={{ fontFamily: "'Oswald', sans-serif" }}
        >
          {article.title}
        </h3>
        
        {/* Excerpt */}
        {article.excerpt && (
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-2 line-clamp-2">
            {article.excerpt}
          </p>
        )}
        
        {/* Probability Bar */}
        {probability > 0 && (
          <div className="mt-3">
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="text-gray-500 dark:text-gray-400">Wahrscheinlichkeit</span>
              <span className="font-bold text-[#79B92A]">{probability}%</span>
            </div>
            <div className="h-2 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-[#79B92A] to-[#9ED65A] rounded-full transition-all duration-500"
                style={{ width: `${probability}%` }}
              />
            </div>
          </div>
        )}
      </div>
    </Link>
  );
}

export default function TopDealsPage() {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTopDeals = async () => {
      try {
        const res = await getTopTransfers(30);
        setArticles(res.data?.articles || []);
      } catch (e) {
        console.error("Top deals fetch error:", e);
      } finally {
        setLoading(false);
      }
    };
    
    fetchTopDeals();
  }, []);

  return (
    <div className="min-h-screen flex flex-col bg-gray-100 dark:bg-gray-950" data-testid="top-deals-page">
      <Helmet>
        <title>Top-Deals - Die heißesten Transfers | TransferNews.de</title>
        <meta name="description" content="Die Top-Transfers der Saison mit den höchsten Wahrscheinlichkeiten. Aktuelle Transfer-Gerüchte und bestätigte Mega-Deals." />
        <meta name="robots" content="index, follow" />
        <link rel="canonical" href="https://transfernews.de/top-deals" />
      </Helmet>
      
      <Header />
      
      <main className="flex-1">
        <div className="max-w-[1000px] mx-auto px-3 py-4">
          {/* Header */}
          <div className="bg-gradient-to-r from-[#79B92A] to-[#5a8a1f] text-white rounded-lg p-6 mb-6">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 bg-white/20 rounded-full flex items-center justify-center">
                <Trophy size={32} weight="fill" />
              </div>
              <div>
                <h1 
                  className="text-3xl md:text-4xl font-black uppercase"
                  style={{ fontFamily: "'Oswald', sans-serif" }}
                  data-testid="page-title"
                >
                  Top-Deals
                </h1>
                <p className="text-white/80 mt-1">Die heißesten Transfers mit höchster Wahrscheinlichkeit</p>
              </div>
            </div>
          </div>
          
          {/* Content Grid */}
          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[...Array(9)].map((_, i) => (
                <div key={i} className="bg-white dark:bg-gray-900 rounded-lg overflow-hidden animate-pulse">
                  <div className="aspect-[16/9] bg-gray-200 dark:bg-gray-800" />
                  <div className="p-4">
                    <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-20 mb-3" />
                    <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-full mb-2" />
                    <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4" />
                  </div>
                </div>
              ))}
            </div>
          ) : articles.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {articles.map((article, index) => (
                <TopDealCard key={article.id} article={article} rank={index + 1} />
              ))}
            </div>
          ) : (
            <div className="bg-white dark:bg-gray-900 rounded-lg p-12 text-center">
              <Trophy size={64} className="mx-auto text-gray-300 dark:text-gray-600 mb-4" />
              <h2 className="text-xl font-bold text-gray-700 dark:text-gray-300 mb-2">Keine Top-Deals vorhanden</h2>
              <p className="text-gray-500 dark:text-gray-400 mb-4">Aktuell sind keine Transfers mit hoher Wahrscheinlichkeit verfügbar.</p>
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
