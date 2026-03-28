import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getAllTrending } from "@/api";
import { TrendUp, Users, Buildings, Fire } from "@phosphor-icons/react";
import { Skeleton } from "@/components/ui/skeleton";

export function TrendingWidget({ className = "" }) {
  const [trending, setTrending] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTrending = async () => {
      try {
        const res = await getAllTrending(24);
        setTrending(res.data);
      } catch (e) {
        console.error("Trending load error:", e);
      } finally {
        setLoading(false);
      }
    };
    fetchTrending();
  }, []);

  if (loading) {
    return (
      <div className={`bg-white border border-gray-200 ${className}`}>
        <div className="bg-black px-4 py-3">
          <Skeleton className="h-5 w-32 bg-gray-700" />
        </div>
        <div className="p-4 space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <Skeleton key={i} className="h-6 w-full" />
          ))}
        </div>
      </div>
    );
  }

  if (!trending) return null;

  const { trending_players = [], trending_clubs = [] } = trending;

  return (
    <div className={`bg-white border border-gray-200 ${className}`} data-testid="trending-widget">
      {/* Header */}
      <div className="bg-black px-4 py-3 flex items-center gap-2">
        <TrendUp size={18} weight="bold" className="text-[#79B92A]" />
        <span className="text-white font-bold text-sm uppercase tracking-wide">Trending</span>
        <Fire size={16} weight="fill" className="text-orange-500 ml-auto animate-pulse" />
      </div>

      {/* Trending Players */}
      {trending_players.length > 0 && (
        <div className="border-b border-gray-100">
          <div className="px-4 py-2 bg-gray-50 flex items-center gap-2">
            <Users size={14} className="text-[#79B92A]" />
            <span className="text-xs font-semibold uppercase text-gray-600">Spieler</span>
          </div>
          <ul className="divide-y divide-gray-50">
            {trending_players.slice(0, 5).map((player, idx) => (
              <li key={player.name}>
                <Link
                  to={`/spieler/${player.name.toLowerCase().replace(/\s+/g, '-')}`}
                  className="flex items-center px-4 py-2.5 hover:bg-gray-50 transition-colors group"
                  data-testid={`trending-player-${idx}`}
                >
                  <span className="w-6 h-6 bg-[#79B92A] text-white text-xs font-bold flex items-center justify-center mr-3">
                    {idx + 1}
                  </span>
                  <span className="flex-1 text-sm font-medium text-gray-900 group-hover:text-[#79B92A] capitalize">
                    {player.name}
                  </span>
                  <span className="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded">
                    {player.trend_score ? `${player.trend_score} Score` : `${player.count} News`}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Trending Clubs */}
      {trending_clubs.length > 0 && (
        <div>
          <div className="px-4 py-2 bg-gray-50 flex items-center gap-2">
            <Buildings size={14} className="text-[#79B92A]" />
            <span className="text-xs font-semibold uppercase text-gray-600">Vereine</span>
          </div>
          <ul className="divide-y divide-gray-50">
            {trending_clubs.slice(0, 5).map((club, idx) => (
              <li key={club.name}>
                <Link
                  to={`/verein/${club.name.toLowerCase().replace(/\s+/g, '-')}`}
                  className="flex items-center px-4 py-2.5 hover:bg-gray-50 transition-colors group"
                  data-testid={`trending-club-${idx}`}
                >
                  <span className="w-6 h-6 bg-black text-white text-xs font-bold flex items-center justify-center mr-3">
                    {idx + 1}
                  </span>
                  <span className="flex-1 text-sm font-medium text-gray-900 group-hover:text-[#79B92A] capitalize">
                    {club.name}
                  </span>
                  <span className="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded">
                    {club.trend_score ? `${club.trend_score} Score` : `${club.count} News`}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Empty State */}
      {trending_players.length === 0 && trending_clubs.length === 0 && (
        <div className="p-6 text-center text-gray-500 text-sm">
          Keine Trending-Daten verfügbar
        </div>
      )}
    </div>
  );
}

export function TrendingBar({ className = "" }) {
  const [trending, setTrending] = useState(null);

  useEffect(() => {
    const fetchTrending = async () => {
      try {
        const res = await getAllTrending(24);
        setTrending(res.data);
      } catch (e) {
        console.error("Trending bar load error:", e);
      }
    };
    fetchTrending();
  }, []);

  if (!trending) return null;

  const allTrending = [
    ...trending.trending_players.slice(0, 3).map(p => ({ ...p, type: 'player' })),
    ...trending.trending_clubs.slice(0, 2).map(c => ({ ...c, type: 'club' }))
  ];

  if (allTrending.length === 0) return null;

  return (
    <div className={`bg-gray-900 text-white overflow-hidden ${className}`} data-testid="trending-bar">
      <div className="max-w-[1280px] mx-auto px-4 py-2 flex items-center gap-4">
        <div className="flex items-center gap-2 shrink-0">
          <TrendUp size={16} weight="bold" className="text-[#79B92A]" />
          <span className="text-xs font-bold uppercase">Trending:</span>
        </div>
        <div className="flex items-center gap-3 overflow-x-auto scrollbar-hide">
          {allTrending.map((item, idx) => (
            <Link
              key={`${item.type}-${item.name}`}
              to={`/${item.type === 'player' ? 'spieler' : 'verein'}/${item.name.toLowerCase().replace(/\s+/g, '-')}`}
              className="text-xs hover:text-[#79B92A] transition-colors whitespace-nowrap capitalize"
            >
              {item.name}
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}

export default TrendingWidget;
