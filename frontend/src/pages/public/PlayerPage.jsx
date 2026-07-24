import Header from "@/components/Header";
import Footer from "@/components/Footer";
import PageLayout from "@/components/PageLayout";
import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getPlayerBySlug, getArticlesByPlayer, getPlayerTransfers } from "@/api";
import { User, MapPin, Calendar, CaretRight, TrendUp, ArrowRight, Buildings, Swap } from "@phosphor-icons/react";
import { Helmet } from "react-helmet-async";

function BoxHeader({ title, icon: Icon }) {
  return (
    <div className="bg-[#79B92A] px-3 py-2 flex items-center gap-2">
      {Icon && <Icon size={14} className="text-white" />}
      <h2 className="text-white text-[11px] font-bold uppercase">{title}</h2>
    </div>
  );
}

function formatMarketValue(value) {
  if (!value) return "-";
  if (value >= 1000000) return `${(value / 1000000).toFixed(1)} Mio. €`;
  if (value >= 1000) return `${(value / 1000).toFixed(0)} Tsd. €`;
  return `${value} €`;
}

function formatDate(dateString) {
  if (!dateString) return "-";
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' });
  } catch {
    return dateString;
  }
}

function calculateAge(birthdate) {
  if (!birthdate) return null;
  try {
    const birth = new Date(birthdate);
    const today = new Date();
    let age = today.getFullYear() - birth.getFullYear();
    const m = today.getMonth() - birth.getMonth();
    if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) age--;
    return age;
  } catch {
    return null;
  }
}

function NewsRow({ article }) {
  const typeConfig = {
    rumour: { bg: "bg-amber-500", label: "Gerücht" },
    transfer: { bg: "bg-[#00a83f]", label: "Transfer" },
    news: { bg: "bg-[#79B92A]", label: "News" },
  };
  const type = typeConfig[article.article_type] || typeConfig.news;
  
  return (
    <Link 
      to={`/news/${article.slug}`}
      className="flex items-center gap-3 px-3 py-2 hover:bg-[#e8f4e8] border-b border-gray-200 last:border-0 group"
    >
      <div className="w-[50px] h-[36px] flex-shrink-0 bg-gray-200 overflow-hidden rounded-sm">
        {article.image_url && <img src={article.image_url} alt="" className="w-full h-full object-cover" />}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1 mb-0.5">
          <span className={`text-[9px] font-bold text-white px-1 py-0.5 rounded-sm ${type.bg}`}>{type.label}</span>
        </div>
        <h3 className="text-[12px] font-medium text-gray-900 group-hover:text-[#00a83f] line-clamp-1">{article.title}</h3>
      </div>
      <CaretRight size={12} className="text-gray-400" />
    </Link>
  );
}

function TransferRow({ transfer }) {
  return (
    <div className="flex items-center gap-3 px-3 py-2.5 border-b border-gray-200 last:border-0 text-[12px]">
      <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center flex-shrink-0">
        <Swap size={14} className="text-gray-500" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 text-gray-700">
          <span className="font-medium truncate">{transfer.from_club || 'Unbekannt'}</span>
          <ArrowRight size={12} className="text-[#79B92A] flex-shrink-0" />
          <span className="font-medium truncate">{transfer.to_club || 'Unbekannt'}</span>
        </div>
        <div className="text-[10px] text-gray-500 mt-0.5">{transfer.year || transfer.season || '-'}</div>
      </div>
      <div className="text-right flex-shrink-0">
        <div className="font-bold text-gray-900">
          {transfer.fee || (transfer.fee_amount ? formatMarketValue(transfer.fee_amount) : 'ablösefrei')}
        </div>
        <div className="text-[9px] text-gray-500">{transfer.transfer_type || 'Fest'}</div>
      </div>
    </div>
  );
}

export default function PlayerPage() {
  const { slug } = useParams();
  const [player, setPlayer] = useState(null);
  const [articles, setArticles] = useState([]);
  const [transfers, setTransfers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('profile');

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const playerRes = await getPlayerBySlug(slug);
        setPlayer(playerRes.data);

        const [articlesRes, transfersRes] = await Promise.all([
          getArticlesByPlayer(playerRes.data.id, { limit: 10 }),
          getPlayerTransfers(slug),
        ]);

        setArticles(articlesRes.data || []);
        setTransfers(transfersRes.data || []);
      } catch (e) {
        console.error("Player load error:", e);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [slug]);

  if (loading) {
    return (
      <PageLayout>
        <Header />
        <main className="flex-1 py-3 px-3">
          <div className="bg-white border border-gray-300 rounded-sm animate-pulse">
            <div className="h-[120px] bg-gray-200" />
            <div className="p-4 space-y-3">
              <div className="h-6 bg-gray-200 rounded w-1/3" />
              <div className="h-4 bg-gray-200 rounded w-1/4" />
            </div>
          </div>
        </main>
        <Footer />
      </PageLayout>
    );
  }

  if (!player) {
    return (
      <PageLayout>
        <Header />
        <main className="flex-1 flex items-center justify-center">
          <div className="text-center bg-white p-8 rounded-sm border border-gray-300">
            <User size={48} className="mx-auto text-gray-400 mb-4" />
            <h1 className="text-lg font-bold mb-2">Spieler nicht gefunden</h1>
            <Link to="/" className="text-[#00a83f] hover:underline text-[13px]">Zur Startseite</Link>
          </div>
        </main>
        <Footer />
      </PageLayout>
    );
  }

  const age = calculateAge(player.birthdate);
  const marketValue = player.market_value || null;

  return (
    <PageLayout>
      <Helmet>
        <title>{`${player.name} - Profil, News & Transfers | TransferNews.de`}</title>
        <meta name="description" content={`${player.name} - Alle Infos: Marktwert, Transfers, News und Gerüchte.`} />
        <link rel="canonical" href={`https://transfernews.de/spieler/${slug}`} />
      </Helmet>
      
      <Header />
      
      <main className="flex-1 py-3 px-3" data-testid="player-page">
        {/* Breadcrumb */}
        <div className="mb-2 text-[11px] text-gray-500">
            <Link to="/" className="hover:text-[#00a83f]">Startseite</Link>
            <span className="mx-1">›</span>
            <span className="text-gray-700">{player.name}</span>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-[1fr_300px] gap-3">
            {/* Main Content */}
            <div className="space-y-3">
              {/* Player Header Card */}
              <div className="bg-white border border-gray-300 rounded-sm overflow-hidden">
                <div className="bg-[#79B92A] p-4">
                  <div className="flex items-start gap-4">
                    {/* Player Image */}
                    <div className="w-[100px] h-[130px] bg-white rounded overflow-hidden flex-shrink-0">
                      {player.image ? (
                        <img 
                          src={player.image} 
                          alt={player.name} 
                          className="w-full h-full object-cover"
                          referrerPolicy="no-referrer"
                          crossOrigin="anonymous"
                          onError={(e) => {
                            e.target.style.display = 'none';
                            e.target.nextSibling.style.display = 'flex';
                          }}
                        />
                      ) : null}
                      <div className={`w-full h-full items-center justify-center bg-gray-100 ${player.image ? 'hidden' : 'flex'}`}>
                        <User size={48} className="text-gray-400" />
                      </div>
                    </div>
                    
                    {/* Player Info */}
                    <div className="flex-1 text-white">
                      <h1 className="text-2xl font-bold mb-1" data-testid="player-name">{player.name}</h1>
                      
                      <div className="flex flex-wrap gap-x-4 gap-y-1 text-[12px] text-white/80 mt-2">
                        {player.position && (
                          <span className="bg-white/20 px-2 py-0.5 rounded">{player.position}</span>
                        )}
                        {player.country && (
                          <span className="flex items-center gap-1">
                            <MapPin size={12} />
                            {player.country}
                          </span>
                        )}
                        {age && (
                          <span className="flex items-center gap-1">
                            <Calendar size={12} />
                            {age} Jahre
                          </span>
                        )}
                      </div>
                      
                      {player.current_club_name && (
                        <div className="mt-3 text-[12px] flex items-center gap-2">
                          <Buildings size={14} />
                          <span>Aktueller Verein: </span>
                          <Link 
                            to={`/verein/${player.current_club_slug}`}
                            className="font-bold hover:underline"
                          >
                            {player.current_club_name}
                          </Link>
                        </div>
                      )}
                    </div>
                    
                    {/* Market Value Box */}
                    <div className="bg-white rounded p-3 text-center min-w-[120px]">
                      <div className="text-[10px] text-gray-500 uppercase mb-1">Marktwert</div>
                      <div className="text-xl font-bold text-[#00a83f]">
                        {marketValue ? formatMarketValue(marketValue) : '-'}
                      </div>
                      {player.market_value_date && (
                        <div className="text-[9px] text-gray-400 mt-1">
                          Stand: {formatDate(player.market_value_date)}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
                
                {/* Stats Bar */}
                <div className="grid grid-cols-4 divide-x divide-gray-200 border-t border-gray-200">
                  {[
                    { label: 'Geburtsdatum', value: player.birthdate ? formatDate(player.birthdate) : '-' },
                    { label: 'Nationalität', value: player.country || '-' },
                    { label: 'Position', value: player.position || '-' },
                    { label: 'Vertrag bis', value: player.contract_until || '-' },
                  ].map((stat, i) => (
                    <div key={i} className="p-3 text-center">
                      <div className="text-[10px] text-gray-500 uppercase">{stat.label}</div>
                      <div className="text-[12px] font-semibold text-gray-900 mt-0.5">{stat.value}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Tabs Navigation */}
              <div className="bg-white border border-gray-300 rounded-sm overflow-hidden">
                <div className="flex border-b border-gray-200 bg-gray-50">
                  {[
                    { id: 'profile', label: 'Profil' },
                    { id: 'transfers', label: 'Transfers' },
                    { id: 'news', label: 'News' },
                  ].map((tab) => (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`px-4 py-2 text-[11px] font-semibold transition-colors ${
                        activeTab === tab.id 
                          ? 'text-[#00a83f] border-b-2 border-[#00a83f] bg-white -mb-[1px]' 
                          : 'text-gray-600 hover:text-gray-900'
                      }`}
                    >
                      {tab.label}
                    </button>
                  ))}
                </div>
                
                {/* Tab Content */}
                <div>
                  {activeTab === 'profile' && (
                    <div className="p-4">
                      <h3 className="font-bold text-[13px] mb-3 text-gray-900">Spielerdaten</h3>
                      <div className="grid grid-cols-2 gap-2 text-[12px]">
                        {[
                          { label: 'Vollständiger Name', value: player.name },
                          { label: 'Geburtsdatum', value: player.birthdate ? formatDate(player.birthdate) : '-' },
                          { label: 'Geburtsort', value: player.birthplace || '-' },
                          { label: 'Nationalität', value: player.country || '-' },
                          { label: 'Position', value: player.position || '-' },
                          { label: 'Fuß', value: player.foot || '-' },
                          { label: 'Größe', value: player.height ? `${player.height} cm` : '-' },
                          { label: 'Aktueller Verein', value: player.current_club_name || '-' },
                          { label: 'Vertrag bis', value: player.contract_until || '-' },
                          { label: 'Marktwert', value: marketValue ? formatMarketValue(marketValue) : '-' },
                        ].map((item, i) => (
                          <div key={i} className="flex border-b border-gray-100 py-1.5">
                            <span className="w-1/2 text-gray-500">{item.label}:</span>
                            <span className="w-1/2 font-medium text-gray-900">{item.value}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {activeTab === 'transfers' && (
                    <div>
                      {transfers.length > 0 ? (
                        <>
                          <div className="bg-gray-50 px-3 py-2 border-b border-gray-200 text-[10px] text-gray-500 uppercase font-bold">
                            Transfer-Historie
                          </div>
                          {transfers.map((t) => (
                            <TransferRow key={t.id} transfer={t} />
                          ))}
                        </>
                      ) : (
                        <div className="p-8 text-center text-gray-500 text-[13px]">
                          Keine Transfers vorhanden
                        </div>
                      )}
                    </div>
                  )}
                  
                  {activeTab === 'news' && (
                    <div>
                      {articles.length > 0 ? (
                        articles.map((article) => (
                          <NewsRow key={article.id} article={article} />
                        ))
                      ) : (
                        <div className="p-8 text-center text-gray-500 text-[13px]">
                          Keine News vorhanden
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Sidebar */}
            <aside className="space-y-3">
              {/* Market Value History */}
              <div className="bg-white border border-gray-300 rounded-sm overflow-hidden">
                <BoxHeader title="Marktwert-Entwicklung" icon={TrendUp} />
                <div className="p-4">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-[#00a83f] mb-1">
                      {marketValue ? formatMarketValue(marketValue) : '-'}
                    </div>
                    <div className="text-[10px] text-gray-500">Aktueller Marktwert</div>
                  </div>
                  {/* Placeholder for chart */}
                  <div className="mt-4 h-[100px] bg-gray-50 rounded flex items-center justify-center text-[11px] text-gray-400">
                    Marktwert-Verlauf
                  </div>
                </div>
              </div>
              
              {/* Latest News */}
              {articles.length > 0 && (
                <div className="bg-white border border-gray-300 rounded-sm overflow-hidden">
                  <BoxHeader title="Aktuelle News" />
                  {articles.slice(0, 3).map((article) => (
                    <NewsRow key={article.id} article={article} />
                  ))}
                </div>
              )}
              
              {/* Quick Links */}
              <div className="bg-white border border-gray-300 rounded-sm overflow-hidden">
                <BoxHeader title="Ähnliche Spieler" />
                <div className="p-3 text-[11px] text-gray-500 text-center">
                  Keine ähnlichen Spieler gefunden
                </div>
              </div>
            </aside>
          </div>
        </main>

        <Footer />
      </PageLayout>
  );
}
