import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { AdSlot, SidebarAd } from "@/components/AdSlot";
import { NewsCard } from "@/components/NewsCard";
import { TrendingWidget } from "@/components/TrendingWidget";
import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getPlayerBySlug, getArticlesByPlayer, getTransfers, getRumours } from "@/api";
import { Badge } from "@/components/ui/badge";
import { User, MapPin, Calendar, ArrowLeft } from "@phosphor-icons/react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { Helmet } from "react-helmet-async";

export default function PlayerPage() {
  const { slug } = useParams();
  const [player, setPlayer] = useState(null);
  const [articles, setArticles] = useState([]);
  const [transfers, setTransfers] = useState([]);
  const [rumours, setRumours] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const playerRes = await getPlayerBySlug(slug);
        setPlayer(playerRes.data);

        const [articlesRes, transfersRes, rumoursRes] = await Promise.all([
          getArticlesByPlayer(playerRes.data.id, { limit: 10 }),
          getTransfers({ player_id: playerRes.data.id, limit: 10 }),
          getRumours({ player_id: playerRes.data.id, limit: 10 }),
        ]);

        setArticles(articlesRes.data);
        setTransfers(transfersRes.data);
        setRumours(rumoursRes.data);
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
      <div className="min-h-screen flex flex-col bg-gray-50">
        <Header />
        <main className="flex-1">
          <div className="max-w-7xl mx-auto px-4 py-8">
            <Skeleton className="h-48 w-full mb-4" />
            <Skeleton className="h-8 w-1/2 mb-4" />
            <Skeleton className="h-4 w-1/3" />
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  if (!player) {
    return (
      <div className="min-h-screen flex flex-col bg-gray-50">
        <Header />
        <main className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <h1 className="text-2xl font-bold mb-4">Spieler nicht gefunden</h1>
            <Link to="/" className="text-[#79B92A] hover:underline">
              Zur Startseite
            </Link>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  // Schema.org Person markup
  const schemaData = {
    "@context": "https://schema.org",
    "@type": "Person",
    "name": player.name,
    "url": `https://transfernews.de/spieler/${slug}`,
    ...(player.country && { "nationality": player.country }),
    ...(player.birthdate && { "birthDate": player.birthdate }),
    ...(player.image && { "image": player.image }),
    ...(player.position && { "jobTitle": player.position })
  };

  return (
    <div className="min-h-screen flex flex-col bg-gray-50" data-testid="player-page">
      <Helmet>
        <title>{player.name} - Transfer-News & Gerüchte | TransferNews.de</title>
        <meta name="description" content={`Alle Transfer-News, Gerüchte und Wechsel zu ${player.name}. Aktuelle Informationen und Hintergründe.`} />
        <meta name="robots" content="index, follow, max-image-preview:large" />
        <link rel="canonical" href={`https://transfernews.de/spieler/${slug}`} />
        
        {/* OpenGraph */}
        <meta property="og:title" content={`${player.name} - Transfer-News & Gerüchte`} />
        <meta property="og:description" content={`Alle Transfer-News und Gerüchte zu ${player.name}`} />
        <meta property="og:type" content="profile" />
        <meta property="og:url" content={`https://transfernews.de/spieler/${slug}`} />
        {player.image && <meta property="og:image" content={player.image} />}
        
        {/* Twitter */}
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content={`${player.name} - TransferNews.de`} />
        
        {/* Schema.org */}
        <script type="application/ld+json">{JSON.stringify(schemaData)}</script>
      </Helmet>
      
      <Header />

      {/* Top Ad */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-2">
          <AdSlot slotKey="player_above_profile" minHeight="90px" />
        </div>
      </div>

      <main className="flex-1">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Breadcrumb */}
          <div className="mb-6">
            <Link to="/" className="text-sm text-gray-500 hover:text-[#79B92A] flex items-center">
              <ArrowLeft size={14} className="mr-1" />
              Zurück
            </Link>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Main Content */}
            <div className="lg:col-span-2">
              {/* Player Profile Card */}
              <div className="bg-white border border-gray-200 mb-6">
                <div className="bg-gradient-to-r from-[#3d5c1f] to-[#79B92A] p-6">
                  <div className="flex items-center gap-6">
                    <div className="w-24 h-24 bg-white/20 rounded-full flex items-center justify-center">
                      {player.image ? (
                        <img src={player.image} alt={player.name} className="w-full h-full rounded-full object-cover" />
                      ) : (
                        <User size={48} className="text-white/70" />
                      )}
                    </div>
                    <div className="text-white">
                      <h1 className="font-['Oswald'] text-3xl font-bold uppercase" data-testid="player-name">
                        {player.name}
                      </h1>
                      {player.position && (
                        <Badge className="mt-2 bg-white/20 text-white">{player.position}</Badge>
                      )}
                    </div>
                  </div>
                </div>

                <div className="p-6">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {player.country && (
                      <div className="flex items-center text-sm">
                        <MapPin size={16} className="mr-2 text-[#79B92A]" />
                        <span>{player.country}</span>
                      </div>
                    )}
                    {player.birthdate && (
                      <div className="flex items-center text-sm">
                        <Calendar size={16} className="mr-2 text-[#79B92A]" />
                        <span>{player.birthdate}</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Ad below profile */}
              <AdSlot slotKey="player_below_profile" minHeight="90px" className="mb-6" />

              {/* Tabs */}
              <Tabs defaultValue="news" className="bg-white border border-gray-200">
                <TabsList className="w-full justify-start border-b rounded-none bg-gray-50 p-0">
                  <TabsTrigger value="news" className="rounded-none border-b-2 border-transparent data-[state=active]:border-[#79B92A]">
                    News ({articles.length})
                  </TabsTrigger>
                  <TabsTrigger value="transfers" className="rounded-none border-b-2 border-transparent data-[state=active]:border-[#79B92A]">
                    Transfers ({transfers.length})
                  </TabsTrigger>
                  <TabsTrigger value="rumours" className="rounded-none border-b-2 border-transparent data-[state=active]:border-[#79B92A]">
                    Gerüchte ({rumours.length})
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="news" className="p-4">
                  {articles.length > 0 ? (
                    <div className="space-y-4">
                      {articles.map((article) => (
                        <NewsCard key={article.id} article={article} />
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-500 py-8 text-center">Keine News vorhanden</p>
                  )}
                </TabsContent>

                <TabsContent value="transfers" className="p-4">
                  {transfers.length > 0 ? (
                    <div className="overflow-x-auto">
                      <table className="transfer-table w-full">
                        <thead>
                          <tr>
                            <th>Status</th>
                            <th>Typ</th>
                            <th>Ablöse</th>
                            <th>Saison</th>
                          </tr>
                        </thead>
                        <tbody>
                          {transfers.map((t) => (
                            <tr key={t.id}>
                              <td>
                                <Badge className={t.status === "official" ? "badge-official" : "badge-confirmed"}>
                                  {t.status === "official" ? "Offiziell" : t.status}
                                </Badge>
                              </td>
                              <td>{t.transfer_type}</td>
                              <td>
                                {t.fee_amount
                                  ? `${t.fee_amount.toLocaleString("de-DE")} ${t.fee_currency}`
                                  : "-"}
                              </td>
                              <td>{t.season || "-"}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <p className="text-gray-500 py-8 text-center">Keine Transfers vorhanden</p>
                  )}
                </TabsContent>

                <TabsContent value="rumours" className="p-4">
                  {rumours.length > 0 ? (
                    <div className="space-y-4">
                      {rumours.map((r) => (
                        <div key={r.id} className="border-b pb-4">
                          <div className="flex items-center gap-2 mb-2">
                            <Badge className="badge-rumour">Gerücht</Badge>
                            <Badge className={r.status === "active" ? "bg-yellow-100 text-yellow-800" : "bg-gray-100"}>
                              {r.status}
                            </Badge>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-sm text-gray-500">Wahrscheinlichkeit:</span>
                            <div className="h-2 w-24 bg-gray-200 rounded">
                              <div
                                className="h-full bg-yellow-500 rounded"
                                style={{ width: `${r.confidence_score}%` }}
                              />
                            </div>
                            <span className="text-sm font-medium">{r.confidence_score}%</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-500 py-8 text-center">Keine Gerüchte vorhanden</p>
                  )}
                </TabsContent>
              </Tabs>

              {/* Ad between news blocks */}
              <AdSlot slotKey="player_between_news_blocks" minHeight="90px" className="mt-6" />
            </div>

            {/* Sidebar */}
            <aside className="space-y-6">
              <TrendingWidget />
              <SidebarAd slotKey="sidebar_top" />
              <SidebarAd slotKey="sidebar_middle" />
            </aside>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
