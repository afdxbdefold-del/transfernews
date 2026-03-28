import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { AdSlot, SidebarAd } from "@/components/AdSlot";
import { NewsCard } from "@/components/NewsCard";
import { TrendingWidget } from "@/components/TrendingWidget";
import { SportsTeamSchema } from "@/components/SchemaMarkup";
import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getClubBySlug, getArticlesByClub, getTransfers } from "@/api";
import { Badge } from "@/components/ui/badge";
import { Buildings, MapPin, ArrowLeft } from "@phosphor-icons/react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { Helmet } from "react-helmet-async";

export default function ClubPage() {
  const { slug } = useParams();
  const [club, setClub] = useState(null);
  const [articles, setArticles] = useState([]);
  const [transfers, setTransfers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const clubRes = await getClubBySlug(slug);
        setClub(clubRes.data);

        const [articlesRes, transfersRes] = await Promise.all([
          getArticlesByClub(clubRes.data.id, { limit: 10 }),
          getTransfers({ club_id: clubRes.data.id, limit: 20 }),
        ]);

        setArticles(articlesRes.data);
        setTransfers(transfersRes.data);
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

  if (!club) {
    return (
      <div className="min-h-screen flex flex-col bg-gray-50">
        <Header />
        <main className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <h1 className="text-2xl font-bold mb-4">Verein nicht gefunden</h1>
            <Link to="/" className="text-[#79B92A] hover:underline">
              Zur Startseite
            </Link>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  // Schema.org SportsTeam data
  const teamData = {
    name: club.name,
    url: `https://transfernews.de/verein/${slug}`,
    location: club.country,
    logo: club.logo
  };

  return (
    <div className="min-h-screen flex flex-col bg-gray-50" data-testid="club-page">
      <Helmet>
        <title>{`${club.name} - Transfer-News & Gerüchte | TransferNews.de`}</title>
        <meta name="description" content={`Alle Transfer-News, Gerüchte, Zugänge und Abgänge von ${club.name}. Aktuelle Transfermarkt-Informationen.`} />
        <meta name="robots" content="index, follow, max-image-preview:large" />
        <link rel="canonical" href={`https://transfernews.de/verein/${slug}`} />
        
        {/* OpenGraph */}
        <meta property="og:title" content={`${club.name} - Transfer-News & Gerüchte`} />
        <meta property="og:description" content={`Alle Transfer-News von ${club.name}`} />
        <meta property="og:type" content="website" />
        <meta property="og:url" content={`https://transfernews.de/verein/${slug}`} />
        {club.logo && <meta property="og:image" content={club.logo} />}
        
        {/* Twitter */}
        <meta name="twitter:card" content="summary" />
        <meta name="twitter:title" content={`${club.name} - TransferNews.de`} />
      </Helmet>
      
      {/* Schema.org SportsTeam JSON-LD */}
      <SportsTeamSchema team={teamData} />
      
      <Header />

      {/* Top Ad */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-2">
          <AdSlot slotKey="club_above_header" minHeight="90px" />
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
              {/* Club Profile Card */}
              <div className="bg-white border border-gray-200 mb-6">
                <div className="bg-gradient-to-r from-[#3d5c1f] to-[#79B92A] p-6">
                  <div className="flex items-center gap-6">
                    <div className="w-24 h-24 bg-white rounded-lg flex items-center justify-center p-2">
                      {club.logo ? (
                        <img src={club.logo} alt={club.name} className="w-full h-full object-contain" />
                      ) : (
                        <Buildings size={48} className="text-gray-400" />
                      )}
                    </div>
                    <div className="text-white">
                      <h1 className="font-['Oswald'] text-3xl font-bold uppercase" data-testid="club-name">
                        {club.name}
                      </h1>
                      {club.country && (
                        <div className="flex items-center mt-2 text-white/80">
                          <MapPin size={16} className="mr-1" />
                          {club.country}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Ad below header */}
              <AdSlot slotKey="club_below_header" minHeight="90px" className="mb-6" />

              {/* Tabs */}
              <Tabs defaultValue="news" className="bg-white border border-gray-200">
                <TabsList className="w-full justify-start border-b rounded-none bg-gray-50 p-0">
                  <TabsTrigger value="news" className="rounded-none border-b-2 border-transparent data-[state=active]:border-[#79B92A]">
                    News ({articles.length})
                  </TabsTrigger>
                  <TabsTrigger value="transfers" className="rounded-none border-b-2 border-transparent data-[state=active]:border-[#79B92A]">
                    Transfers ({transfers.length})
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
                            <th>Richtung</th>
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
                              <td>
                                <Badge className={t.to_club_id === club.id ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}>
                                  {t.to_club_id === club.id ? "Zugang" : "Abgang"}
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
              </Tabs>

              {/* Ad between news blocks */}
              <AdSlot slotKey="club_between_news_blocks" minHeight="90px" className="mt-6" />
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
