import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { AdSlot, SidebarAd } from "@/components/AdSlot";
import { NewsCard } from "@/components/NewsCard";
import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getCompetitionBySlug, getArticlesByCompetition, getClubs } from "@/api";
import { Trophy, MapPin, ArrowLeft, Buildings } from "@phosphor-icons/react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";

export default function CompetitionPage() {
  const { slug } = useParams();
  const [competition, setCompetition] = useState(null);
  const [articles, setArticles] = useState([]);
  const [clubs, setClubs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const compRes = await getCompetitionBySlug(slug);
        setCompetition(compRes.data);

        const [articlesRes, clubsRes] = await Promise.all([
          getArticlesByCompetition(compRes.data.id, { limit: 10 }),
          getClubs({ competition_id: compRes.data.id, limit: 50 }),
        ]);

        setArticles(articlesRes.data);
        setClubs(clubsRes.data);
      } catch (e) {
        console.error("Competition load error:", e);
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
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  if (!competition) {
    return (
      <div className="min-h-screen flex flex-col bg-gray-50">
        <Header />
        <main className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <h1 className="text-2xl font-bold mb-4">Wettbewerb nicht gefunden</h1>
            <Link to="/" className="text-[#00a651] hover:underline">
              Zur Startseite
            </Link>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-gray-50" data-testid="competition-page">
      <Header />

      {/* Top Ad */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-2">
          <AdSlot slotKey="competition_above_header" minHeight="90px" />
        </div>
      </div>

      <main className="flex-1">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Breadcrumb */}
          <div className="mb-6">
            <Link to="/" className="text-sm text-gray-500 hover:text-[#00a651] flex items-center">
              <ArrowLeft size={14} className="mr-1" />
              Zurück
            </Link>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Main Content */}
            <div className="lg:col-span-2">
              {/* Competition Header */}
              <div className="bg-white border border-gray-200 mb-6">
                <div className="bg-gradient-to-r from-[#053f2c] to-[#00a651] p-6">
                  <div className="flex items-center gap-6">
                    <div className="w-24 h-24 bg-white rounded-lg flex items-center justify-center p-2">
                      {competition.logo ? (
                        <img src={competition.logo} alt={competition.name} className="w-full h-full object-contain" />
                      ) : (
                        <Trophy size={48} className="text-yellow-500" />
                      )}
                    </div>
                    <div className="text-white">
                      <h1 className="font-['Oswald'] text-3xl font-bold uppercase" data-testid="competition-name">
                        {competition.name}
                      </h1>
                      {competition.country && (
                        <div className="flex items-center mt-2 text-white/80">
                          <MapPin size={16} className="mr-1" />
                          {competition.country}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Ad below header */}
              <AdSlot slotKey="competition_below_header" minHeight="90px" className="mb-6" />

              {/* Tabs */}
              <Tabs defaultValue="news" className="bg-white border border-gray-200">
                <TabsList className="w-full justify-start border-b rounded-none bg-gray-50 p-0">
                  <TabsTrigger value="news" className="rounded-none border-b-2 border-transparent data-[state=active]:border-[#00a651]">
                    News ({articles.length})
                  </TabsTrigger>
                  <TabsTrigger value="clubs" className="rounded-none border-b-2 border-transparent data-[state=active]:border-[#00a651]">
                    Vereine ({clubs.length})
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

                <TabsContent value="clubs" className="p-4">
                  {clubs.length > 0 ? (
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                      {clubs.map((club) => (
                        <Link
                          key={club.id}
                          to={`/verein/${club.slug}`}
                          className="flex items-center gap-3 p-3 border border-gray-200 hover:border-[#00a651] transition-colors"
                        >
                          <div className="w-12 h-12 bg-gray-100 rounded flex items-center justify-center">
                            {club.logo ? (
                              <img src={club.logo} alt={club.name} className="w-10 h-10 object-contain" />
                            ) : (
                              <Buildings size={24} className="text-gray-400" />
                            )}
                          </div>
                          <span className="font-medium text-sm">{club.name}</span>
                        </Link>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-500 py-8 text-center">Keine Vereine vorhanden</p>
                  )}
                </TabsContent>
              </Tabs>

              {/* Ad between modules */}
              <AdSlot slotKey="competition_between_modules" minHeight="90px" className="mt-6" />
            </div>

            {/* Sidebar */}
            <aside className="space-y-6">
              <SidebarAd slotKey="sidebar_top" />
              <SidebarAd slotKey="sidebar_middle" />
              <SidebarAd slotKey="sidebar_bottom" />
            </aside>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
