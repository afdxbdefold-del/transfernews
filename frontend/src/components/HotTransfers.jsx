import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Fire, ArrowRight, TrendUp } from "@phosphor-icons/react";
import { getPublishedArticles } from "@/api";

// Club logo mapping
const CLUB_LOGOS = {
  'bayern': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/132.png&w=60',
  'münchen': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/132.png&w=60',
  'dortmund': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/124.png&w=60',
  'leverkusen': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/131.png&w=60',
  'leipzig': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/11420.png&w=60',
  'manchester city': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/382.png&w=60',
  'city': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/382.png&w=60',
  'manchester united': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/360.png&w=60',
  'united': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/360.png&w=60',
  'liverpool': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/364.png&w=60',
  'chelsea': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/363.png&w=60',
  'arsenal': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/359.png&w=60',
  'real madrid': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/86.png&w=60',
  'madrid': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/86.png&w=60',
  'barcelona': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/83.png&w=60',
  'barca': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/83.png&w=60',
  'juventus': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/111.png&w=60',
  'inter': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/110.png&w=60',
  'milan': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/103.png&w=60',
  'napoli': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/114.png&w=60',
  'psg': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/160.png&w=60',
  'paris': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/160.png&w=60',
  'tottenham': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/367.png&w=60',
  'athletic': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/93.png&w=60',
  'bilbao': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/93.png&w=60',
  'stuttgart': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/134.png&w=60',
  'fulham': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/370.png&w=60',
};

function getClubLogo(clubName) {
  if (!clubName) return null;
  const lower = clubName.toLowerCase();
  for (const [key, url] of Object.entries(CLUB_LOGOS)) {
    if (lower.includes(key)) return url;
  }
  return null;
}

export function HotTransfers({ className = "" }) {
  const [hotTransfers, setHotTransfers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHotTransfers = async () => {
      try {
        const res = await getPublishedArticles(20);
        // Filter for rumours with high confidence or recent hot topics
        const articles = res.data || [];
        const hot = articles
          .filter(a => a.article_type === 'rumour' || a.transfer_probability)
          .sort((a, b) => (b.transfer_probability || 50) - (a.transfer_probability || 50))
          .slice(0, 3);
        setHotTransfers(hot);
      } catch (e) {
        console.error("Hot transfers load error:", e);
      } finally {
        setLoading(false);
      }
    };
    fetchHotTransfers();
  }, []);

  if (loading || hotTransfers.length === 0) return null;

  return (
    <div className={`bg-gradient-to-r from-red-600 to-orange-500 ${className}`} data-testid="hot-transfers">
      <div className="max-w-[1000px] mx-auto px-3 py-3">
        {/* Header */}
        <div className="flex items-center gap-2 mb-3">
          <Fire size={20} weight="fill" className="text-yellow-300 animate-pulse" />
          <h2 className="text-white font-black text-sm uppercase tracking-wide" style={{ fontFamily: "'Oswald', sans-serif" }}>
            Heißeste Transfers
          </h2>
        </div>
        
        {/* Hot Transfer Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {hotTransfers.map((transfer, idx) => (
            <HotTransferCard key={transfer.id} transfer={transfer} rank={idx + 1} />
          ))}
        </div>
      </div>
    </div>
  );
}

function HotTransferCard({ transfer, rank }) {
  const fromLogo = getClubLogo(transfer.from_club);
  const toLogo = getClubLogo(transfer.to_club);
  const probability = transfer.transfer_probability || Math.floor(Math.random() * 30) + 40;
  
  return (
    <a 
      href={`/news/${transfer.slug}`}
      className="bg-white/10 backdrop-blur-sm rounded-lg p-3 hover:bg-white/20 transition-all group"
      data-testid={`hot-transfer-${rank}`}
    >
      {/* Player Name + Clubs */}
      <div className="flex items-center gap-2 mb-2">
        <span className="text-yellow-300 font-black text-lg">#{rank}</span>
        <span className="text-white font-bold text-sm truncate flex-1">
          {transfer.player_name || transfer.title?.split(':')[0]}
        </span>
      </div>
      
      {/* Club Transfer Visual */}
      <div className="flex items-center justify-center gap-2 mb-2">
        {fromLogo ? (
          <img src={fromLogo} alt="" className="w-8 h-8 object-contain bg-white rounded-full p-0.5" />
        ) : (
          <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center text-white text-xs">?</div>
        )}
        <ArrowRight size={16} className="text-yellow-300" weight="bold" />
        {toLogo ? (
          <img src={toLogo} alt="" className="w-8 h-8 object-contain bg-white rounded-full p-0.5" />
        ) : (
          <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center text-white text-xs">?</div>
        )}
      </div>
      
      {/* Probability Meter */}
      <div className="flex items-center gap-2">
        <div className="flex-1 h-2 bg-white/20 rounded-full overflow-hidden">
          <div 
            className="h-full bg-gradient-to-r from-yellow-400 to-green-400 transition-all"
            style={{ width: `${probability}%` }}
          />
        </div>
        <span className="text-white text-xs font-bold">{probability}%</span>
      </div>
      
      {/* Label */}
      <div className="flex items-center gap-1 mt-1">
        <TrendUp size={12} className="text-yellow-300" />
        <span className="text-white/70 text-[10px]">Wahrscheinlichkeit</span>
      </div>
    </a>
  );
}

export default HotTransfers;
