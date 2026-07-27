import Header from "@/components/Header";
import Footer from "@/components/Footer";
import PageLayout from "@/components/PageLayout";
import { useEffect, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { search } from "@/api";
import { MagnifyingGlass, User, Buildings, Trophy, Newspaper } from "@phosphor-icons/react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
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
    <PageLayout>
      <Header />

      <main className="flex-1 py-3 px-3" data-testid="search-page">
        <div className="bg-white rounded-lg shadow-sm p-4 mb-4">
          <h1 className="font-['Oswald'] text-2xl font-bold uppercase flex items-center mb-4">
            <MagnifyingGlass size={24} className="mr-2 text-[#79B92A]" />
            Suche
          </h1>
          
          <form onSubmit={handleSubmit} className="flex gap-2">
            <Input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Spieler, Verein oder News suchen..."
              className="flex-1"
              data-testid="search-input"
            />
            <Button type="submit" className="bg-[#79B92A] hover:bg-[#6aa025]" data-testid="search-btn">
              Suchen
            </Button>
          </form>
        </div>

        {loading && (
          <div className="bg-white rounded-lg shadow-sm p-4 space-y-3">
            {[...Array(5)].map((_, i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        )}

        {results && !loading && (
          <div className="space-y-4">
            <p className="text-sm text-gray-500">{totalResults} Ergebnisse für "{searchParams.get("q")}"</p>

            {results.players.length > 0 && (
              <div className="bg-white rounded-lg shadow-sm overflow-hidden">
                <div className="bg-[#79B92A] px-3 py-2 flex items-center gap-2">
                  <User size={16} className="text-white" />
                  <span className="text-white text-sm font-bold">Spieler ({results.players.length})</span>
                </div>
                <div className="divide-y">
                  {results.players.map((player) => (
                    <Link
                      key={player.id}
                      to={`/spieler/${player.slug}`}
                      className="block px-3 py-2 hover:bg-gray-50"
                    >
                      <span className="font-medium">{player.name}</span>
                      {player.current_club_name && (
                        <span className="text-gray-500 text-sm ml-2">({player.current_club_name})</span>
                      )}
                    </Link>
                  ))}
                </div>
              </div>
            )}

            {results.clubs.length > 0 && (
              <div className="bg-white rounded-lg shadow-sm overflow-hidden">
                <div className="bg-[#79B92A] px-3 py-2 flex items-center gap-2">
                  <Buildings size={16} className="text-white" />
                  <span className="text-white text-sm font-bold">Vereine ({results.clubs.length})</span>
                </div>
                <div className="divide-y">
                  {results.clubs.map((club) => (
                    <Link
                      key={club.id}
                      to={`/verein/${club.slug}`}
                      className="block px-3 py-2 hover:bg-gray-50"
                    >
                      <span className="font-medium">{club.name}</span>
                      {club.league && (
                        <span className="text-gray-500 text-sm ml-2">({club.league})</span>
                      )}
                    </Link>
                  ))}
                </div>
              </div>
            )}

            {results.articles.length > 0 && (
              <div className="bg-white rounded-lg shadow-sm overflow-hidden">
                <div className="bg-[#79B92A] px-3 py-2 flex items-center gap-2">
                  <Newspaper size={16} className="text-white" />
                  <span className="text-white text-sm font-bold">News ({results.articles.length})</span>
                </div>
                <div className="divide-y">
                  {results.articles.map((article) => (
                    <Link
                      key={article.id}
                      to={`/news/${article.slug}`}
                      className="block px-3 py-2 hover:bg-gray-50"
                    >
                      <span className="font-medium">{article.title}</span>
                    </Link>
                  ))}
                </div>
              </div>
            )}

            {totalResults === 0 && (
              <div className="bg-white rounded-lg shadow-sm p-8 text-center">
                <MagnifyingGlass size={48} className="mx-auto text-gray-300 mb-4" />
                <p className="text-gray-500">Keine Ergebnisse gefunden</p>
              </div>
            )}
          </div>
        )}
      </main>

      <Footer />
    </PageLayout>
  );
}
