import { Link } from "react-router-dom";
import { Play, Circle } from "@phosphor-icons/react";
import { useState } from "react";

const formatTime = (dateString) => {
  if (!dateString) return "";
  const date = new Date(dateString);
  const now = new Date();
  const diff = now - date;
  const hours = Math.floor(diff / 3600000);
  
  if (hours < 1) return "vor " + Math.floor(diff / 60000) + " Min.";
  if (hours < 24) return "vor " + hours + " Std.";
  return date.toLocaleDateString("de-DE", { day: "2-digit", month: "2-digit" });
};

// Fallback images for different categories
const FALLBACK_IMAGES = [
  "https://images.unsplash.com/photo-1574629810360-7efbbe195018?w=800",
  "https://images.unsplash.com/photo-1508098682722-e99c43a406b2?w=800",
  "https://images.unsplash.com/photo-1553778263-73a83bab9b0c?w=800",
  "https://images.unsplash.com/photo-1431324155629-1a6deb1dec8d?w=800",
];

function getFallbackImage(id) {
  const index = id ? id.charCodeAt(0) % FALLBACK_IMAGES.length : 0;
  return FALLBACK_IMAGES[index];
}

// Image component with error handling
function ArticleImage({ src, alt, className, articleId }) {
  const [error, setError] = useState(false);
  const fallback = getFallbackImage(articleId);
  
  return (
    <img
      src={error ? fallback : (src || fallback)}
      alt={alt}
      className={className}
      onError={() => setError(true)}
    />
  );
}

// Club logo mapping - Extended
const CLUB_LOGOS = {
  // Bundesliga
  'bayern': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/132.png&w=60',
  'münchen': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/132.png&w=60',
  'dortmund': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/124.png&w=60',
  'bvb': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/124.png&w=60',
  'leverkusen': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/131.png&w=60',
  'bayer 04': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/131.png&w=60',
  'leipzig': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/11420.png&w=60',
  'frankfurt': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/3771.png&w=60',
  'stuttgart': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/134.png&w=60',
  'gladbach': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/129.png&w=60',
  'wolfsburg': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/135.png&w=60',
  
  // Premier League
  'manchester city': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/382.png&w=60',
  'man city': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/382.png&w=60',
  'city': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/382.png&w=60',
  'manchester united': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/360.png&w=60',
  'man united': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/360.png&w=60',
  'liverpool': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/364.png&w=60',
  'chelsea': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/363.png&w=60',
  'arsenal': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/359.png&w=60',
  'tottenham': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/367.png&w=60',
  'newcastle': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/361.png&w=60',
  'aston villa': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/362.png&w=60',
  'fulham': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/370.png&w=60',
  
  // La Liga
  'real madrid': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/86.png&w=60',
  'madrid': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/86.png&w=60',
  'barcelona': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/83.png&w=60',
  'barca': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/83.png&w=60',
  'atletico': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/1068.png&w=60',
  'athletic bilbao': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/93.png&w=60',
  'bilbao': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/93.png&w=60',
  
  // Serie A
  'juventus': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/111.png&w=60',
  'juve': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/111.png&w=60',
  'inter': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/110.png&w=60',
  'mailand': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/103.png&w=60',
  'ac milan': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/103.png&w=60',
  'milan': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/103.png&w=60',
  'napoli': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/114.png&w=60',
  'roma': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/104.png&w=60',
  
  // Ligue 1
  'psg': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/160.png&w=60',
  'paris': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/160.png&w=60',
  'paris saint': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/160.png&w=60',
};

// Get TWO club logos for transfer articles (from -> to)
function getTransferClubLogos(article) {
  const fromClub = article?.from_club?.toLowerCase() || '';
  const toClub = article?.to_club?.toLowerCase() || '';
  const title = article?.title?.toLowerCase() || '';
  
  let fromLogo = null;
  let toLogo = null;
  
  for (const [key, url] of Object.entries(CLUB_LOGOS)) {
    if (fromClub.includes(key) && !fromLogo) fromLogo = url;
    if (toClub.includes(key) && !toLogo) toLogo = url;
  }
  
  // Fallback: try to find from title
  if (!fromLogo || !toLogo) {
    for (const [key, url] of Object.entries(CLUB_LOGOS)) {
      if (title.includes(key)) {
        if (!fromLogo) fromLogo = url;
        else if (!toLogo && url !== fromLogo) toLogo = url;
      }
    }
  }
  
  return { fromLogo, toLogo };
}

// Status badge configuration
const STATUS_BADGES = {
  'official': { label: 'OFFIZIELL', bg: 'bg-green-500', text: 'text-white' },
  'confirmed': { label: 'BESTÄTIGT', bg: 'bg-green-500', text: 'text-white' },
  'done': { label: 'DONE DEAL', bg: 'bg-green-500', text: 'text-white' },
  'hot': { label: 'HEISS', bg: 'bg-red-500', text: 'text-white' },
  'breaking': { label: 'BREAKING', bg: 'bg-red-600', text: 'text-white' },
  'rumour': { label: 'GERÜCHT', bg: 'bg-amber-500', text: 'text-black' },
  'transfer': { label: 'TRANSFER', bg: 'bg-blue-500', text: 'text-white' },
  'denied': { label: 'DEMENTIERT', bg: 'bg-gray-400', text: 'text-white' },
  'news': { label: 'NEWS', bg: 'bg-[#79B92A]', text: 'text-white' },
};

function getStatusBadge(article) {
  const type = article?.article_type?.toLowerCase() || '';
  const status = article?.transfer_status?.toLowerCase() || '';
  const isBreaking = article?.is_breaking;
  
  if (isBreaking) return STATUS_BADGES['breaking'];
  if (status === 'official' || status === 'offiziell' || status === 'bestätigt') return STATUS_BADGES['official'];
  if (status === 'confirmed' || status === 'done') return STATUS_BADGES['confirmed'];
  if (status === 'denied' || status === 'dementiert') return STATUS_BADGES['denied'];
  if (type === 'rumour' || type === 'gerücht') return STATUS_BADGES['rumour'];
  if (type === 'transfer') return STATUS_BADGES['transfer'];
  return STATUS_BADGES['news'];
}

function getClubLogo(title) {
  const titleLower = title?.toLowerCase() || '';
  for (const [key, url] of Object.entries(CLUB_LOGOS)) {
    if (titleLower.includes(key)) {
      return url;
    }
  }
  return null;
}

// Transfer Status Badge Component
function TransferBadge({ status }) {
  const statusConfig = {
    'GERÜCHT': { bg: 'bg-gray-600', text: 'text-white' },
    'FORTGESCHRITTEN': { bg: 'bg-blue-600', text: 'text-white' },
    'BESTÄTIGT': { bg: 'bg-[#79B92A]', text: 'text-white' },
    'OFFIZIELL': { bg: 'bg-[#79B92A]', text: 'text-white' },
  };
  
  const config = statusConfig[status] || statusConfig['GERÜCHT'];
  
  return (
    <div className={`text-[9px] font-black uppercase px-1.5 py-0.5 ${config.bg} ${config.text}`}>
      {status || "GERÜCHT"}
    </div>
  );
}

// Transfer Probability Bar Component - ENHANCED
function ProbabilityBar({ probability, size = "small" }) {
  if (!probability) return null;
  
  const getColor = (p) => {
    if (p >= 80) return { bar: 'bg-gradient-to-r from-green-500 to-green-400', text: 'text-green-600' };
    if (p >= 60) return { bar: 'bg-gradient-to-r from-lime-500 to-lime-400', text: 'text-lime-600' };
    if (p >= 40) return { bar: 'bg-gradient-to-r from-amber-500 to-yellow-400', text: 'text-amber-600' };
    return { bar: 'bg-gradient-to-r from-gray-400 to-gray-300', text: 'text-gray-500' };
  };
  
  const colors = getColor(probability);
  const isLarge = size === "large";
  
  return (
    <div className={`flex items-center gap-2 ${isLarge ? 'w-full' : ''}`}>
      <div className={`flex-1 ${isLarge ? 'h-3' : 'h-2'} bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden shadow-inner`}>
        <div 
          className={`h-full ${colors.bar} rounded-full transition-all duration-500 ease-out animate-pulse-subtle`}
          style={{ width: `${probability}%` }}
        />
      </div>
      <span className={`${isLarge ? 'text-sm font-black' : 'text-[11px] font-bold'} ${colors.text} dark:text-gray-300 min-w-[36px] text-right`}>
        {probability}%
      </span>
    </div>
  );
}

// Hero Card - Featured article with smaller image
export function HeroCard({ article, isLive = false }) {
  if (!article) return null;
  
  const { fromLogo, toLogo } = getTransferClubLogos(article);
  const statusBadge = getStatusBadge(article);
  
  return (
    <Link to={"/news/" + article.slug} className="block relative" data-testid={"hero-" + article.id}>
      <div className="relative aspect-[16/10] bg-gray-900">
        <ArticleImage
          src={article.hero_image || article.feature_image}
          alt={article.title}
          className="w-full h-full object-cover object-top"
          articleId={article.id}
        />
        
        {/* Transfer Club Logos - Top Right - ENHANCED */}
        {(fromLogo || toLogo) && (
          <div className="absolute top-3 right-3 flex items-center gap-2 bg-white/95 dark:bg-gray-800/95 rounded-xl px-3 py-2 shadow-xl backdrop-blur-sm border border-gray-100 dark:border-gray-700">
            {fromLogo && (
              <div className="w-10 h-10 rounded-full bg-gray-50 dark:bg-gray-700 p-1 shadow-inner">
                <img src={fromLogo} alt="" className="w-full h-full object-contain" />
              </div>
            )}
            {fromLogo && toLogo && (
              <div className="flex flex-col items-center">
                <span className="text-[#79B92A] text-lg font-black">→</span>
              </div>
            )}
            {toLogo && (
              <div className="w-10 h-10 rounded-full bg-gray-50 dark:bg-gray-700 p-1 shadow-inner">
                <img src={toLogo} alt="" className="w-full h-full object-contain" />
              </div>
            )}
          </div>
        )}
        
        {/* Status Badge - Top Left */}
        <div className="absolute top-3 left-3 flex items-center gap-2">
          {isLive && (
            <div className="bg-[#e91e63] text-white text-xs font-bold px-2 py-1 flex items-center gap-1">
              <Circle size={8} weight="fill" className="animate-pulse" />
              LIVE
            </div>
          )}
          <div className={`text-[10px] font-black uppercase px-2 py-1 ${statusBadge.bg} ${statusBadge.text}`}>
            {statusBadge.label}
          </div>
        </div>
        
        {/* Gradient Overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/30 to-transparent" />
        
        {/* Content */}
        <div className="absolute bottom-0 left-0 right-0 p-4">
          {/* Probability Bar - ENHANCED */}
          {article.transfer_probability && (
            <div className="mb-3 max-w-[220px]">
              <ProbabilityBar probability={article.transfer_probability} size="large" />
            </div>
          )}
          
          <h2 className="text-white text-base md:text-lg font-black uppercase leading-tight mb-2" style={{ fontFamily: "'Oswald', sans-serif" }}>
            {article.title}
          </h2>
          <button className="bg-[#00a8e8] text-white text-xs font-bold uppercase px-4 py-1.5">
            ANSEHEN
          </button>
        </div>
      </div>
    </Link>
  );
}

// Horizontal News Card - Image left, text right (Sport1 mobile style)
export function NewsCardHorizontal({ article, showVideo = false }) {
  if (!article) return null;
  
  const { fromLogo, toLogo } = getTransferClubLogos(article);
  const statusBadge = getStatusBadge(article);
  
  return (
    <Link 
      to={"/news/" + article.slug} 
      className="flex gap-3 p-3 bg-white dark:bg-gray-900 border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors group"
      data-testid={"news-card-" + article.id}
    >
      {/* Image */}
      <div className="relative w-[110px] h-[75px] flex-shrink-0 bg-gray-100 dark:bg-gray-800 overflow-hidden rounded-lg shadow-sm">
        <ArticleImage
          src={article.hero_image || article.feature_image}
          alt={article.title}
          className="w-full h-full object-cover object-top group-hover:scale-105 transition-transform duration-300"
          articleId={article.id}
        />
        
        {/* Transfer Club Logos - ENHANCED */}
        {(fromLogo || toLogo) && (
          <div className="absolute bottom-1 right-1 flex items-center gap-1 bg-white/95 dark:bg-gray-800/95 rounded-lg px-1.5 py-1 shadow-md backdrop-blur-sm">
            {fromLogo && (
              <div className="w-5 h-5 rounded-full bg-gray-50 dark:bg-gray-700 overflow-hidden">
                <img src={fromLogo} alt="" className="w-full h-full object-contain" />
              </div>
            )}
            {fromLogo && toLogo && <span className="text-[10px] text-[#79B92A] font-bold">→</span>}
            {toLogo && (
              <div className="w-5 h-5 rounded-full bg-gray-50 dark:bg-gray-700 overflow-hidden">
                <img src={toLogo} alt="" className="w-full h-full object-contain" />
              </div>
            )}
          </div>
        )}
      </div>
      
      {/* Content */}
      <div className="flex-1 flex flex-col justify-center py-0.5">
        <div className="flex items-center gap-2 mb-1">
          {/* Colorful Status Badge */}
          <div className={`text-[9px] font-black uppercase px-1.5 py-0.5 rounded ${statusBadge.bg} ${statusBadge.text}`}>
            {statusBadge.label}
          </div>
          <span className="text-[10px] text-gray-400 dark:text-gray-500">{formatTime(article.published_at)}</span>
        </div>
        
        <h3 className="text-[14px] font-bold text-gray-900 dark:text-white leading-snug line-clamp-2 group-hover:text-[#79B92A] transition-colors" style={{ fontFamily: "'Oswald', sans-serif" }}>
          {article.title}
        </h3>
        
        {/* Probability Bar - ENHANCED */}
        {article.transfer_probability && (
          <div className="mt-2 max-w-[180px]">
            <ProbabilityBar probability={article.transfer_probability} />
          </div>
        )}
      </div>
    </Link>
  );
}

// Newsticker Entry - Time + Category + Title (Sport1 sidebar style)
export function NewsTickerEntry({ article }) {
  if (!article) return null;
  
  const getTime = (dateString) => {
    if (!dateString) return "--:--";
    const date = new Date(dateString);
    return date.toLocaleTimeString("de-DE", { hour: "2-digit", minute: "2-digit" });
  };
  
  return (
    <Link 
      to={"/news/" + article.slug} 
      className="flex items-start gap-3 py-3 border-b border-gray-100 hover:bg-gray-50 transition-colors"
      data-testid={"ticker-" + article.id}
    >
      <span className="text-[13px] font-bold text-gray-900 w-12 flex-shrink-0">{getTime(article.published_at)}</span>
      <div className="flex-1 min-w-0">
        <span className="text-[11px] font-bold text-[#79B92A] uppercase block mb-0.5">{article.category || "TRANSFER"}</span>
        <span className="text-[13px] font-medium text-gray-900 line-clamp-2">{article.title}</span>
      </div>
    </Link>
  );
}

// Simple News Card for grids
export function NewsCard({ article }) {
  if (!article) return null;
  
  return (
    <Link to={"/news/" + article.slug} className="block bg-white" data-testid={"card-" + article.id}>
      <div className="aspect-[4/3] bg-gray-100 overflow-hidden">
        <ArticleImage
          src={article.feature_image}
          alt={article.title}
          className="w-full h-full object-cover"
          articleId={article.id}
        />
      </div>
      <div className="p-3">
        <h3 className="text-[14px] font-bold text-gray-900 leading-snug line-clamp-2 mb-2" style={{ fontFamily: "'Oswald', sans-serif" }}>
          {article.title}
        </h3>
        <div className="flex items-center gap-1.5">
          <div className="w-4 h-4 bg-[#79B92A] rounded-full" />
          <span className="text-[10px] text-gray-500 font-medium">{article.category || "Transfer"}</span>
          <span className="text-[10px] text-gray-400 ml-auto">{formatTime(article.published_at)}</span>
        </div>
      </div>
    </Link>
  );
}

// Compact list item
export function NewsCardCompact({ article }) {
  if (!article) return null;
  
  return (
    <Link to={"/news/" + article.slug} className="block py-2.5 border-b border-gray-100 hover:bg-gray-50">
      <span className="text-[13px] font-bold text-gray-900 line-clamp-2" style={{ fontFamily: "'Oswald', sans-serif" }}>
        {article.title}
      </span>
      <span className="text-[11px] text-gray-400 mt-1 block">{formatTime(article.published_at)}</span>
    </Link>
  );
}
