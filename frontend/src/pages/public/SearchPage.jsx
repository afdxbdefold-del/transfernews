import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { AdSlot, SidebarAd } from "@/components/AdSlot";
import { NewsCard } from "@/components/NewsCard";
import { useEffect, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { search } from "@/api";
import { MagnifyingGlass, User, Buildings, Trophy, Newspaper } from "@phosphor-icons/react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";

export default function SearchPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [query, setQuery] = useState(searchParams.get("q") || "");
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const q = searchParams.get("q");
    if (q) {
      setQuery(q);
      performSearch(q);
    }
  }, [searchParams]);

  const performSearch = async (q) => {
    if (!q || q.length < 2) return;
    
    try {
      setLoading(true);
      const res = await search(q, 20);
      setResults(res.data);
    } catch (e) {
      console.error("Search error:", e);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      setSearchParams({ q: query.trim() });
    }
  };

  const totalResults = results
    ? results.players.length + results.clubs.length + results.competitions.length + results.articles.length
    : 0;

  return (
    <div className="min-h-screen flex flex-col bg-gray-50" data-testid="search-page">
      <Header />

      {/* Top Ad */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-2">
          <AdSlot slotKey="search_results_top" minHeight="90px" />
        </div>
      </div>

      <main className="flex-1">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Search Form */}
          <div className="mb-8">
            <h1 className="font-['Oswald'] text-4xl font-bold uppercase flex items-center mb-6" data-testid="page-title">
              <MagnifyingGlass size={36} className="mr-3 text-[#79B92A]" />
              Suche
            </h1>
            
            <form onSubmit={handleSubmit} className="flex gap-4 max-w-2xl">
              <Input
                type="text"
                placeholder="Spieler, Verein, Wettbewerb..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="flex-1"
                data-testid="search-input"
              />
              <Button type="submit" className="bg-[#79B92A] hover:bg-[#6aa325]" data-testid="search-submit">
                Suchen
              </Button>
            </form>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Main Content */}
            <div className="lg:col-span-2">
              {loading ? (
                <div className="space-y-4">
                  {[...Array(5)].map((_, i) => (
                    <div key={i} className="bg-white border p-4">
                      <Skeleton className="h-6 w-3/4 mb-3" />
                      <Skeleton className="h-4 w-1/2" />
                    </div>
                  ))}
                </div>
              ) : results ? (
                <>
                  <p className="text-gray-500 mb-4">
                    {totalResults} Ergebnisse für "{searchParams.get("q")}"
                  </p>

                  <Tabs defaultValue="all" className="bg-white border border-gray-200">
                    <TabsList className="w-full justify-start border-b rounded-none bg-gray-50 p-0 flex-wrap">
                      <TabsTrigger value="all" className="rounded-none border-b-2 border-transparent data-[state=active]:border-[#79B92A]">
                        Alle ({totalResults})
                      </TabsTrigger>
                      <TabsTrigger value="players" className="rounded-none border-b-2 border-transparent data-[state=active]:border-[#79B92A]">
                        Spieler ({results.players.length})
                      </TabsTrigger>
                      <TabsTrigger value="clubs" className="rounded-none border-b-2 border-transparent data-[state=active]:border-[#79B92A]">
                        Vereine ({results.clubs.length})
                      </TabsTrigger>
                      <TabsTrigger value="articles" className="rounded-none border-b-2 border-transparent data-[state=active]:border-[#79B92A]">
                        News ({results.articles.length})
                      </TabsTrigger>
                    </TabsList>

                    <TabsContent value="all" className="p-4">
                      <div className="space-y-6">
                        {/* Players */}
                        {results.players.length > 0 && (
                          <div>
                            <h3 className="font-['Oswald'] text-lg font-bold uppercase mb-3 flex items-center">
                              <User size={20} className="mr-2 text-[#79B92A]" />
                              Spieler
                            </h3>
                            <div className="space-y-2">
                              {results.players.slice(0, 5).map((player) => (
                                <Link
                                  key={player.id}
                                  to={`/spieler/${player.slug}`}
                                  className="flex items-center justify-between p-3 border hover:border-[#79B92A] transition-colors"
                                >
                                  <div>
                                    <span className="font-medium">{player.name}</span>
                                    {player.position && (
                                      <span className="text-sm text-gray-500 ml-2">({player.position})</span>
                                    )}
                                  </div>
                                  {player.country && (
                                    <span className="text-sm text-gray-400">{player.country}</span>
                                  )}
                                </Link>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Clubs */}
                        {results.clubs.length > 0 && (
                          <div>
                            <h3 className="font-['Oswald'] text-lg font-bold uppercase mb-3 flex items-center">
                              <Buildings size={20} className="mr-2 text-[#79B92A]" />
                              Vereine
                            </h3>
                            <div className="space-y-2">
                              {results.clubs.slice(0, 5).map((club) => (
                                <Link
                                  key={club.id}
                                  to={`/verein/${club.slug}`}
                                  className="flex items-center justify-between p-3 border hover:border-[#79B92A] transition-colors"
                                >
                                  <span className="font-medium">{club.name}</span>
                                  {club.country && (
                                    <span className="text-sm text-gray-400">{club.country}</span>
                                  )}
                                </Link>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Articles */}
                        {results.articles.length > 0 && (
                          <div>
                            <h3 className="font-['Oswald'] text-lg font-bold uppercase mb-3 flex items-center">
                              <Newspaper size={20} className="mr-2 text-[#79B92A]" />
                              News
                            </h3>
                            <div className="space-y-3">
                              {results.articles.slice(0, 5).map((article) => (
                                <NewsCard key={article.id} article={article} />
                              ))}
                            </div>
                          </div>
                        )}

                        {totalResults === 0 && (
                          <div className="text-center py-8 text-gray-500">
                            Keine Ergebnisse gefunden
                          </div>
                        )}
                      </div>
                    </TabsContent>

                    <TabsContent value="players" className="p-4">
                      {results.players.length > 0 ? (
                        <div className="space-y-2">
                          {results.players.map((player) => (
                            <Link
                              key={player.id}
                              to={`/spieler/${player.slug}`}
                              className="flex items-center justify-between p-3 border hover:border-[#79B92A] transition-colors"
                            >
                              <div className="flex items-center gap-3">
                                <User size={24} className="text-gray-400" />
                                <div>
                                  <span className="font-medium">{player.name}</span>
                                  {player.position && (
                                    <span className="text-sm text-gray-500 ml-2">({player.position})</span>
                                  )}
                                </div>
                              </div>
                              {player.country && (
                                <span className="text-sm text-gray-400">{player.country}</span>
                              )}
                            </Link>
                          ))}
                        </div>
                      ) : (
                        <p className="text-center py-8 text-gray-500">Keine Spieler gefunden</p>
                      )}
                    </TabsContent>

                    <TabsContent value="clubs" className="p-4">
                      {results.clubs.length > 0 ? (
                        <div className="space-y-2">
                          {results.clubs.map((club) => (
                            <Link
                              key={club.id}
                              to={`/verein/${club.slug}`}
                              className="flex items-center justify-between p-3 border hover:border-[#79B92A] transition-colors"
                            >
                              <div className="flex items-center gap-3">
                                <Buildings size={24} className="text-gray-400" />
                                <span className="font-medium">{club.name}</span>
                              </div>
                              {club.country && (
                                <span className="text-sm text-gray-400">{club.country}</span>
                              )}
                            </Link>
                          ))}
                        </div>
                      ) : (
                        <p className="text-center py-8 text-gray-500">Keine Vereine gefunden</p>
                      )}
                    </TabsContent>

                    <TabsContent value="articles" className="p-4">
                      {results.articles.length > 0 ? (
                        <div className="space-y-3">
                          {results.articles.map((article) => (
                            <NewsCard key={article.id} article={article} />
                          ))}
                        </div>
                      ) : (
                        <p className="text-center py-8 text-gray-500">Keine News gefunden</p>
                      )}
                    </TabsContent>
                  </Tabs>
                </>
              ) : (
                <div className="text-center py-12 bg-white border">
                  <MagnifyingGlass size={48} className="mx-auto text-gray-300 mb-4" />
                  <p className="text-gray-500">Gib einen Suchbegriff ein</p>
                </div>
              )}
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
