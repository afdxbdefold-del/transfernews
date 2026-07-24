import Header from "@/components/Header";
import Footer from "@/components/Footer";
import PageLayout from "@/components/PageLayout";
import { useEffect, useState } from "react";
import { getPublishedArticles, getAllTrending } from "@/api";
import { Link } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import { CaretRight, TrendUp, Clock, Fire } from "@phosphor-icons/react";

const FILTERS = [
  { id: 'all', label: 'Alle News' },
  { id: 'rumour', label: 'Gerüchte' },
  { id: 'transfer', label: 'Transfers' },
  { id: 'news', label: 'News' },
];

const LEAGUES = [
  { slug: 'bundesliga', name: 'Bundesliga', flag: '🇩🇪' },
  { slug: 'premier-league', name: 'Premier League', flag: '🏴󠁧󠁢󠁥󠁮󠁧󠁿' },
  { slug: 'la-liga', name: 'La Liga', flag: '🇪🇸' },
  { slug: 'serie-a', name: 'Serie A', flag: '🇮🇹' },
  { slug: 'ligue-1', name: 'Ligue 1', flag: '🇫🇷' },
];

function formatDate(dateString) {
  if (!dateString) return "";
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  
  if (diffMins < 60) return `${diffMins} Min.`;
  if (diffHours < 24) return `${diffHours} Std.`;
  return date.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit' });
}

function NewsRow({ article, showImage = true }) {
  const isNew = () => {
    if (!article.published_at) return false;
    const diffHours = (new Date() - new Date(article.published_at)) / 3600000;
    return diffHours < 2;
  };
  
  const typeLabel = {
    rumour: { text: 'Gerücht', color: 'bg-amber-500' },
    transfer: { text: 'Transfer', color: 'bg-[#00a83f]' },
    news: { text: 'News', color: 'bg-[#1d4370]' },
  };
  const type = typeLabel[article.article_type] || typeLabel.news;
  
  // Use hero_image or image_url as fallback
  const imageUrl = article.hero_image || article.image_url;
  
  return (
    <Link 
      to={`/news/${article.slug}`}
      className="flex items-start gap-3 p-2 hover:bg-[#e8f4e8] border-b border-gray-200 last:border-0 group"
      data-testid={`news-row-${article.id}`}
    >
      {showImage && (
        <div className="w-[70px] h-[50px] flex-shrink-0 bg-gray-200 overflow-hidden rounded-sm">
          {imageUrl ? (
            <img 
              src={imageUrl} 
              alt="" 
              className="w-full h-full object-cover"
              referrerPolicy="no-referrer"
              loading="lazy"
            />
          ) : (
            <div className="w-full h-full bg-gray-300" />
          )}
        </div>
      )}
      
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-0.5">
          <span className={`text-[9px] font-bold text-white px-1.5 py-0.5 rounded-sm ${type.color}`}>
            {type.text}
          </span>
          {article.is_breaking && (
            <span className="text-[9px] font-bold text-white px-1.5 py-0.5 rounded-sm bg-red-600">
              BREAKING
            </span>
          )}
          {isNew() && (
            <span className="text-[9px] font-bold text-red-600">NEU</span>
          )}
          <span className="text-[10px] text-gray-500 flex items-center gap-0.5">
            <Clock size={10} />
            {formatDate(article.published_at)}
          </span>
        </div>
        
        <h3 className="text-[13px] font-semibold text-gray-900 group-hover:text-[#00a83f] line-clamp-2 leading-tight">
          {article.title}
        </h3>
        
        {article.transfer_probability > 0 && (
          <div className="flex items-center gap-1 mt-1">
            <div className="w-16 h-1.5 bg-gray-200 rounded-full overflow-hidden">
              <div 
                className="h-full bg-[#00a83f] rounded-full"
                style={{ width: `${article.transfer_probability}%` }}
              />
            </div>
            <span className="text-[10px] font-bold text-[#00a83f]">{article.transfer_probability}%</span>
          </div>
        )}
      </div>
      
      <CaretRight size={14} className="text-gray-400 flex-shrink-0 mt-2" />
    </Link>
  );
}

function BoxHeader({ title, link, linkText = "mehr" }) {
  return (
    <div className="bg-[#1d4370] px-3 py-2 flex items-center justify-between">
      <h2 className="text-white text-[11px] font-bold uppercase">{title}</h2>
      {link && (
        <Link to={link} className="text-white/70 hover:text-white text-[10px] flex items-center gap-1">
          {linkText} <CaretRight size={10} />
        </Link>
      )}
    </div>
  );
}

function TrendingItem({ item, rank }) {
  return (
    <Link 
      to={item.slug ? `/spieler/${item.slug}` : '#'}
      className="flex items-center gap-2 px-3 py-1.5 hover:bg-[#e8f4e8] border-b border-gray-100 last:border-0"
    >
      <span className="w-5 h-5 bg-gray-200 rounded-full flex items-center justify-center text-[10px] font-bold text-gray-600">
        {rank}
      </span>
      <span className="flex-1 text-[12px] text-gray-900 truncate">{item.name}</span>
      <span className="text-[10px] text-gray-500">{item.score || item.count}</span>
    </Link>
  );
}

export default function HomePage() {
  const [articles, setArticles] = useState([]);
  const [filteredArticles, setFilteredArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeFilter, setActiveFilter] = useState('all');
  const [trending, setTrending] = useState({ players: [], clubs: [] });
  const [hasMore, setHasMore] = useState(true);
  const limit = 30;

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (activeFilter === 'all') {
      setFilteredArticles(articles);
    } else {
      setFilteredArticles(articles.filter(a => a.article_type === activeFilter));
    }
  }, [activeFilter, articles]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [articlesRes, trendingRes] = await Promise.all([
        getPublishedArticles({ limit }),
        getAllTrending(24)
      ]);
      
      const data = Array.isArray(articlesRes.data) ? articlesRes.data : [];
      setArticles(data);
      setHasMore(data.length === limit);
      
      if (trendingRes.data) {
        setTrending({
          players: trendingRes.data.trending_players || [],
          clubs: trendingRes.data.trending_clubs || []
        });
      }
    } catch (e) {
      console.error("Fetch error:", e);
    } finally {
      setLoading(false);
    }
  };

  const loadMore = async () => {
    try {
      const res = await getPublishedArticles({ skip: articles.length, limit });
      const data = Array.isArray(res.data) ? res.data : [];
      setArticles([...articles, ...data]);
      setHasMore(data.length === limit);
    } catch (e) {
      console.error("Load more error:", e);
    }
  };

  return (
    <PageLayout>
      <Helmet>
        <title>TransferNews.de - Fußball-Transfers & Gerüchte</title>
        <meta name="description" content="Die neuesten Fußball-Transfer-News, Gerüchte und offizielle Wechsel. Bundesliga, Premier League, La Liga und mehr." />
        <link rel="canonical" href="https://transfernews.de" />
      </Helmet>
      
      <Header />
      
      <main className="flex-1 py-3 px-3" data-testid="homepage">
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_280px] gap-3">
          {/* Main Content */}
          <div className="space-y-3">
            {/* News Box */}
            <div className="bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm">
              {/* Filter Tabs - Modern Pill Style */}
              <div className="flex items-center gap-2 p-3 bg-gradient-to-r from-gray-50 to-white border-b border-gray-100">
                {FILTERS.map((filter) => (
                  <button
                    key={filter.id}
                    onClick={() => setActiveFilter(filter.id)}
                    className={`px-4 py-1.5 text-[11px] font-medium rounded-full transition-all duration-200 ${
                      activeFilter === filter.id 
                        ? 'bg-[#79B92A] text-white shadow-sm' 
                        : 'bg-white text-gray-600 hover:bg-gray-100 border border-gray-200'
                    }`}
                    data-testid={`filter-${filter.id}`}
                  >
                    {filter.label}
                  </button>
                ))}
              </div>
              
              {/* News List */}
              <div>
                {loading ? (
                  [...Array(10)].map((_, i) => (
                    <div key={i} className="flex items-start gap-3 p-2 border-b border-gray-200 animate-pulse">
                      <div className="w-[70px] h-[50px] bg-gray-200 rounded-sm" />
                      <div className="flex-1">
                        <div className="h-3 bg-gray-200 rounded w-20 mb-2" />
                        <div className="h-4 bg-gray-200 rounded w-full mb-1" />
                        <div className="h-4 bg-gray-200 rounded w-2/3" />
                      </div>
                    </div>
                  ))
                ) : filteredArticles.length > 0 ? (
                  filteredArticles.map((article) => (
                    <NewsRow key={article.id} article={article} />
                  ))
                ) : (
                  <div className="p-8 text-center text-gray-500 text-[13px]">
                    Keine Artikel in dieser Kategorie
                  </div>
                )}
              </div>
              
              {hasMore && !loading && filteredArticles.length > 0 && (
                <div className="p-3 border-t border-gray-100 bg-gradient-to-r from-gray-50 to-white">
                  <button
                    onClick={loadMore}
                    className="w-full py-2.5 text-[12px] font-semibold text-white bg-[#79B92A] hover:bg-[#6aa825] rounded-full transition-all duration-200 shadow-sm"
                    data-testid="load-more-btn"
                  >
                    Mehr News laden
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Sidebar */}
          <aside className="space-y-3">
            {/* Megasky Ad 300x600 (nur Desktop) */}
            <div className="hidden lg:flex bg-gray-200 border border-gray-300 rounded-sm items-center justify-center" style={{ width: '280px', height: '600px' }}>
              <span className="text-[10px] text-gray-400 uppercase">Anzeige</span>
            </div>
            
            {/* Trending Players */}
            <div className="bg-white border border-gray-300 rounded-sm overflow-hidden">
              <BoxHeader title="Trending Spieler" />
              <div>
                {trending.players.length > 0 ? (
                  trending.players.slice(0, 5).map((player, idx) => (
                    <TrendingItem key={player.id || idx} item={player} rank={idx + 1} />
                  ))
                ) : (
                  <div className="p-3 text-center text-gray-500 text-[12px]">
                    Keine Trending-Daten
                  </div>
                )}
              </div>
            </div>
            
            {/* Ad 300x250 unter Trending Spieler (nur Desktop) */}
            <div className="hidden lg:flex bg-gray-200 border border-gray-300 rounded-sm items-center justify-center" style={{ width: '280px', height: '250px' }}>
              <span className="text-[10px] text-gray-400 uppercase">Anzeige</span>
            </div>
            
            {/* Trending Clubs */}
            <div className="bg-white border border-gray-300 rounded-sm overflow-hidden">
              <BoxHeader title="Trending Vereine" />
              <div>
                {trending.clubs.length > 0 ? (
                  trending.clubs.slice(0, 5).map((club, idx) => (
                    <TrendingItem key={club.id || idx} item={club} rank={idx + 1} />
                  ))
                ) : (
                  <div className="p-3 text-center text-gray-500 text-[12px]">
                    Keine Trending-Daten
                  </div>
                )}
              </div>
            </div>
            
            {/* Leagues */}
            <div className="bg-white border border-gray-300 rounded-sm overflow-hidden">
              <BoxHeader title="Wettbewerbe" />
              <nav>
                {LEAGUES.map((league) => (
                  <Link
                    key={league.slug}
                    to={`/wettbewerb/${league.slug}`}
                    className="flex items-center justify-between px-3 py-2 hover:bg-[#e8f4e8] border-b border-gray-100 last:border-0 group"
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-base">{league.flag}</span>
                      <span className="text-[12px] text-gray-900 group-hover:text-[#00a83f]">
                        {league.name}
                      </span>
                    </div>
                    <CaretRight size={12} className="text-gray-400" />
                  </Link>
                ))}
              </nav>
            </div>
            
            {/* Quick Links */}
            <div className="bg-white border border-gray-300 rounded-sm overflow-hidden">
              <BoxHeader title="Schnellzugriff" />
              <nav>
                {[
                  { label: "Deadline Day", path: "/deadline-day", icon: Fire },
                  { label: "Top-Transfers", path: "/top-deals", icon: TrendUp },
                  { label: "Ablösefreie Spieler", path: "/abloesefrei" },
                  { label: "Redaktion", path: "/redaktion" },
                ].map((item) => (
                  <Link
                    key={item.path}
                    to={item.path}
                    className="flex items-center justify-between px-3 py-2 hover:bg-[#e8f4e8] border-b border-gray-100 last:border-0 group"
                  >
                    <span className="text-[12px] text-gray-900 group-hover:text-[#00a83f] flex items-center gap-2">
                      {item.icon && <item.icon size={14} className="text-gray-500" />}
                      {item.label}
                    </span>
                    <CaretRight size={12} className="text-gray-400" />
                  </Link>
                ))}
              </nav>
            </div>
            
            {/* Ad Slot (nur Desktop) */}
            <div className="hidden lg:flex bg-gray-200 border border-gray-300 rounded-sm items-center justify-center" style={{ height: '250px' }}>
              <span className="text-[10px] text-gray-400 uppercase">Anzeige</span>
            </div>
          </aside>
        </div>
      </main>

      <Footer />
    </PageLayout>
  );
}
