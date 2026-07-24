import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getClubBySlug, getArticlesByClub, getTransfers, getPlayers } from "@/api";
import { Buildings, MapPin, CaretRight, ArrowRight, ArrowLeft, User, Trophy, TrendUp, TrendDown, Equals } from "@phosphor-icons/react";
import { Helmet } from "react-helmet-async";

function BoxHeader({ title, icon: Icon, action }) {
  return (
    <div className="bg-[#1d4370] px-3 py-2 flex items-center justify-between">
      <div className="flex items-center gap-2">
        {Icon && <Icon size={14} className="text-white" />}
        <h2 className="text-white text-[11px] font-bold uppercase">{title}</h2>
      </div>
      {action && action}
    </div>
  );
}

function formatMarketValue(value) {
  if (!value) return "-";
  if (value >= 1000000) return `${(value / 1000000).toFixed(1)} Mio. €`;
  if (value >= 1000) return `${(value / 1000).toFixed(0)} Tsd. €`;
  return `${value} €`;
}

function NewsRow({ article }) {
  const typeConfig = {
    rumour: { bg: "bg-amber-500", label: "Gerücht" },
    transfer: { bg: "bg-[#00a83f]", label: "Transfer" },
    news: { bg: "bg-[#1d4370]", label: "News" },
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

function TransferRow({ transfer, clubId }) {
  const isIncoming = transfer.to_club_id === clubId;
  const playerName = transfer.player_name || 'Unbekannt';
  const otherClub = isIncoming ? (transfer.from_club_name || 'Unbekannt') : (transfer.to_club_name || 'Unbekannt');
  
  return (
    <div className="flex items-center gap-2 px-3 py-2 border-b border-gray-200 last:border-0 hover:bg-gray-50">
      <div className={`w-6 h-6 rounded flex items-center justify-center flex-shrink-0 ${isIncoming ? 'bg-green-100' : 'bg-red-100'}`}>
        {isIncoming ? <ArrowRight size={14} className="text-green-600" /> : <ArrowLeft size={14} className="text-red-600" />}
      </div>
      <div className="w-8 h-8 bg-gray-200 rounded-full flex-shrink-0 overflow-hidden">
        {transfer.player_image ? (
          <img src={transfer.player_image} alt="" className="w-full h-full object-cover" />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <User size={14} className="text-gray-400" />
          </div>
        )}
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-[12px] font-medium text-gray-900 truncate">{playerName}</div>
        <div className="text-[10px] text-gray-500 truncate">
          {isIncoming ? 'von ' : 'zu '}{otherClub}
        </div>
      </div>
      <div className="text-right flex-shrink-0">
        <div className="text-[11px] font-bold text-gray-900">
          {transfer.fee_amount ? formatMarketValue(transfer.fee_amount) : 'ablösefrei'}
        </div>
        <div className="text-[9px] text-gray-500">{transfer.season || '-'}</div>
      </div>
    </div>
  );
}

function PlayerRow({ player, position }) {
  return (
    <Link 
      to={`/spieler/${player.slug}`}
      className="flex items-center gap-2 px-3 py-2 border-b border-gray-200 last:border-0 hover:bg-[#e8f4e8] group"
    >
      <div className="w-5 text-center text-[10px] text-gray-500">{position}</div>
      <div className="w-8 h-8 bg-gray-200 rounded-full flex-shrink-0 overflow-hidden">
        {player.image ? (
          <img src={player.image} alt="" className="w-full h-full object-cover" />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <User size={14} className="text-gray-400" />
          </div>
        )}
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-[12px] font-medium text-gray-900 group-hover:text-[#00a83f] truncate">{player.name}</div>
        <div className="text-[10px] text-gray-500">{player.position || '-'}</div>
      </div>
      <div className="text-[11px] font-semibold text-[#00a83f]">
        {player.market_value ? formatMarketValue(player.market_value) : '-'}
      </div>
      <CaretRight size={12} className="text-gray-400" />
    </Link>
  );
}

export default function ClubPage() {
  const { slug } = useParams();
  const [club, setClub] = useState(null);
  const [articles, setArticles] = useState([]);
  const [transfers, setTransfers] = useState([]);
  const [players, setPlayers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const clubRes = await getClubBySlug(slug);
        setClub(clubRes.data);

        const [articlesRes, transfersRes, playersRes] = await Promise.all([
          getArticlesByClub(clubRes.data.id, { limit: 10 }),
          getTransfers({ club_id: clubRes.data.id, limit: 30 }),
          getPlayers({ current_club_id: clubRes.data.id, limit: 50 }),
        ]);

        setArticles(articlesRes.data || []);
        setTransfers(transfersRes.data || []);
        setPlayers(playersRes.data || []);
      } catch (e) {
        console.error("Club load error:", e);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [slug]);

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col bg-[#e8e8e8]">
        <Header />
        <main className="flex-1 py-3">
          <div className="max-w-[1000px] mx-auto px-3">
            <div className="bg-white border border-gray-300 rounded-sm animate-pulse">
              <div className="h-[100px] bg-gray-200" />
              <div className="p-4 space-y-3">
                <div className="h-6 bg-gray-200 rounded w-1/3" />
                <div className="h-4 bg-gray-200 rounded w-1/4" />
              </div>
            </div>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  if (!club) {
    return (
      <div className="min-h-screen flex flex-col bg-[#e8e8e8]">
        <Header />
        <main className="flex-1 flex items-center justify-center">
          <div className="text-center bg-white p-8 rounded-sm border border-gray-300">
            <Buildings size={48} className="mx-auto text-gray-400 mb-4" />
            <h1 className="text-lg font-bold mb-2">Verein nicht gefunden</h1>
            <Link to="/" className="text-[#00a83f] hover:underline text-[13px]">Zur Startseite</Link>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  // Calculate transfer balance
  const incomingTransfers = transfers.filter(t => t.to_club_id === club.id);
  const outgoingTransfers = transfers.filter(t => t.from_club_id === club.id);
  const totalIncoming = incomingTransfers.reduce((sum, t) => sum + (t.fee_amount || 0), 0);
  const totalOutgoing = outgoingTransfers.reduce((sum, t) => sum + (t.fee_amount || 0), 0);
  const balance = totalOutgoing - totalIncoming;

  // Calculate squad value
  const squadValue = players.reduce((sum, p) => sum + (p.market_value || 0), 0);

  return (
    <div className="min-h-screen flex flex-col bg-[#e8e8e8]" data-testid="club-page">
      <Helmet>
        <title>{`${club.name} - Transfers, Kader & News | TransferNews.de`}</title>
        <meta name="description" content={`${club.name} - Alle Infos: Kader, Transfers, Zugänge, Abgänge und aktuelle News.`} />
        <link rel="canonical" href={`https://transfernews.de/verein/${slug}`} />
      </Helmet>
      
      <Header />
      
      <main className="flex-1 py-3">
        <div className="max-w-[1000px] mx-auto px-3">
          {/* Breadcrumb */}
          <div className="mb-2 text-[11px] text-gray-500">
            <Link to="/" className="hover:text-[#00a83f]">Startseite</Link>
            <span className="mx-1">›</span>
            {club.competition_name && (
              <>
                <Link to={`/wettbewerb/${club.competition_slug}`} className="hover:text-[#00a83f]">{club.competition_name}</Link>
                <span className="mx-1">›</span>
              </>
            )}
            <span className="text-gray-700">{club.name}</span>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-[1fr_300px] gap-3">
            {/* Main Content */}
            <div className="space-y-3">
              {/* Club Header Card */}
              <div className="bg-white border border-gray-300 rounded-sm overflow-hidden">
                <div className="bg-[#1d4370] p-4">
                  <div className="flex items-center gap-4">
                    {/* Club Logo */}
                    <div className="w-[80px] h-[80px] bg-white rounded p-2 flex-shrink-0">
                      {club.logo ? (
                        <img src={club.logo} alt={club.name} className="w-full h-full object-contain" />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center">
                          <Buildings size={40} className="text-gray-400" />
                        </div>
                      )}
                    </div>
                    
                    {/* Club Info */}
                    <div className="flex-1 text-white">
                      <h1 className="text-2xl font-bold mb-1" data-testid="club-name">{club.name}</h1>
                      <div className="flex flex-wrap gap-x-4 gap-y-1 text-[12px] text-white/80">
                        {club.country && (
                          <span className="flex items-center gap-1">
                            <MapPin size={12} />
                            {club.country}
                          </span>
                        )}
                        {club.competition_name && (
                          <span className="flex items-center gap-1">
                            <Trophy size={12} />
                            {club.competition_name}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
                
                {/* Stats Bar */}
                <div className="grid grid-cols-4 divide-x divide-gray-200 border-t border-gray-200">
                  {[
                    { label: 'Kadergröße', value: players.length.toString() },
                    { label: 'Kaderwert', value: squadValue > 0 ? formatMarketValue(squadValue) : '-' },
                    { label: 'Zugänge', value: incomingTransfers.length.toString(), color: 'text-green-600' },
                    { label: 'Abgänge', value: outgoingTransfers.length.toString(), color: 'text-red-600' },
                  ].map((stat, i) => (
                    <div key={i} className="p-3 text-center">
                      <div className="text-[10px] text-gray-500 uppercase">{stat.label}</div>
                      <div className={`text-[14px] font-bold mt-0.5 ${stat.color || 'text-gray-900'}`}>{stat.value}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Tabs Navigation */}
              <div className="bg-white border border-gray-300 rounded-sm overflow-hidden">
                <div className="flex border-b border-gray-200 bg-gray-50">
                  {[
                    { id: 'overview', label: 'Übersicht' },
                    { id: 'squad', label: 'Kader' },
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
                  {activeTab === 'overview' && (
                    <div className="divide-y divide-gray-200">
                      {/* Transfer Balance */}
                      <div className="p-4">
                        <h3 className="font-bold text-[13px] mb-3 text-gray-900">Transfer-Bilanz</h3>
                        <div className="grid grid-cols-3 gap-3 text-center">
                          <div className="bg-green-50 rounded p-3">
                            <div className="text-[10px] text-green-700 uppercase mb-1">Einnahmen</div>
                            <div className="text-lg font-bold text-green-600">{formatMarketValue(totalOutgoing)}</div>
                          </div>
                          <div className="bg-red-50 rounded p-3">
                            <div className="text-[10px] text-red-700 uppercase mb-1">Ausgaben</div>
                            <div className="text-lg font-bold text-red-600">{formatMarketValue(totalIncoming)}</div>
                          </div>
                          <div className={`rounded p-3 ${balance >= 0 ? 'bg-green-50' : 'bg-red-50'}`}>
                            <div className="text-[10px] text-gray-600 uppercase mb-1">Bilanz</div>
                            <div className={`text-lg font-bold flex items-center justify-center gap-1 ${balance >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                              {balance >= 0 ? <TrendUp size={18} /> : <TrendDown size={18} />}
                              {balance >= 0 ? '+' : ''}{formatMarketValue(Math.abs(balance))}
                            </div>
                          </div>
                        </div>
                      </div>
                      
                      {/* Recent Transfers Preview */}
                      {transfers.length > 0 && (
                        <div>
                          <div className="bg-gray-50 px-3 py-2 flex items-center justify-between">
                            <span className="text-[10px] text-gray-500 uppercase font-bold">Letzte Transfers</span>
                            <button 
                              onClick={() => setActiveTab('transfers')}
                              className="text-[10px] text-[#00a83f] hover:underline"
                            >
                              Alle anzeigen
                            </button>
                          </div>
                          {transfers.slice(0, 5).map((t) => (
                            <TransferRow key={t.id} transfer={t} clubId={club.id} />
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                  
                  {activeTab === 'squad' && (
                    <div>
                      {players.length > 0 ? (
                        <>
                          <div className="bg-gray-50 px-3 py-2 border-b border-gray-200 flex items-center justify-between">
                            <span className="text-[10px] text-gray-500 uppercase font-bold">Kader ({players.length} Spieler)</span>
                            <span className="text-[10px] text-gray-500">Kaderwert: <strong className="text-[#00a83f]">{formatMarketValue(squadValue)}</strong></span>
                          </div>
                          {players.map((player, idx) => (
                            <PlayerRow key={player.id} player={player} position={idx + 1} />
                          ))}
                        </>
                      ) : (
                        <div className="p-8 text-center text-gray-500 text-[13px]">
                          Keine Spieler im Kader
                        </div>
                      )}
                    </div>
                  )}
                  
                  {activeTab === 'transfers' && (
                    <div>
                      {transfers.length > 0 ? (
                        <>
                          {/* Incoming */}
                          {incomingTransfers.length > 0 && (
                            <>
                              <div className="bg-green-50 px-3 py-2 border-b border-green-200 flex items-center gap-2">
                                <ArrowRight size={14} className="text-green-600" />
                                <span className="text-[10px] text-green-700 uppercase font-bold">Zugänge ({incomingTransfers.length})</span>
                              </div>
                              {incomingTransfers.map((t) => (
                                <TransferRow key={t.id} transfer={t} clubId={club.id} />
                              ))}
                            </>
                          )}
                          
                          {/* Outgoing */}
                          {outgoingTransfers.length > 0 && (
                            <>
                              <div className="bg-red-50 px-3 py-2 border-b border-red-200 flex items-center gap-2">
                                <ArrowLeft size={14} className="text-red-600" />
                                <span className="text-[10px] text-red-700 uppercase font-bold">Abgänge ({outgoingTransfers.length})</span>
                              </div>
                              {outgoingTransfers.map((t) => (
                                <TransferRow key={t.id} transfer={t} clubId={club.id} />
                              ))}
                            </>
                          )}
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
              {/* Squad Value */}
              <div className="bg-white border border-gray-300 rounded-sm overflow-hidden">
                <BoxHeader title="Kaderwert" icon={TrendUp} />
                <div className="p-4 text-center">
                  <div className="text-3xl font-bold text-[#00a83f] mb-1">
                    {squadValue > 0 ? formatMarketValue(squadValue) : '-'}
                  </div>
                  <div className="text-[10px] text-gray-500">{players.length} Spieler</div>
                </div>
              </div>
              
              {/* Top Players */}
              {players.length > 0 && (
                <div className="bg-white border border-gray-300 rounded-sm overflow-hidden">
                  <BoxHeader title="Wertvollste Spieler" />
                  {players
                    .filter(p => p.market_value)
                    .sort((a, b) => (b.market_value || 0) - (a.market_value || 0))
                    .slice(0, 5)
                    .map((player, idx) => (
                      <PlayerRow key={player.id} player={player} position={idx + 1} />
                    ))
                  }
                  {players.filter(p => p.market_value).length === 0 && (
                    <div className="p-3 text-center text-[11px] text-gray-500">
                      Keine Marktwerte verfügbar
                    </div>
                  )}
                </div>
              )}
              
              {/* Latest News */}
              {articles.length > 0 && (
                <div className="bg-white border border-gray-300 rounded-sm overflow-hidden">
                  <BoxHeader title="Aktuelle News" />
                  {articles.slice(0, 3).map((article) => (
                    <NewsRow key={article.id} article={article} />
                  ))}
                </div>
              )}
            </aside>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
