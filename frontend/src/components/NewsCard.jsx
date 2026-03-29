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

// Club logo mapping
const CLUB_LOGOS = {
  'psg': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/160.png&w=60',
  'hakimi': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/160.png&w=60',
  'liverpool': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/364.png&w=60',
  'salah': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/364.png&w=60',
  'bvb': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/124.png&w=60',
  'dortmund': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/124.png&w=60',
  'sancho': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/124.png&w=60',
  'brandt': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/124.png&w=60',
  'bayern': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/132.png&w=60',
  'olise': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/132.png&w=60',
  'real': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/86.png&w=60',
  'madrid': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/86.png&w=60',
  'vinicius': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/86.png&w=60',
  'rudiger': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/86.png&w=60',
  'city': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/382.png&w=60',
  'de bruyne': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/382.png&w=60',
  'rodri': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/382.png&w=60',
  'casemiro': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/360.png&w=60',
  'inter': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/110.png&w=60',
  'calhanoglu': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/110.png&w=60',
  'frankfurt': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/3771.png&w=60',
  'dahoud': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/3771.png&w=60',
  'larsson': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/3771.png&w=60',
};

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

// Transfer Probability Bar Component
function ProbabilityBar({ probability }) {
  if (!probability) return null;
  
  const getColor = (p) => {
    if (p >= 80) return 'bg-[#79B92A]';  // Green - confirmed
    if (p >= 50) return 'bg-[#79B92A]/70';  // Light green
    return 'bg-gray-400';  // Gray - low probability
  };
  
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
        <div 
          className={`h-full ${getColor(probability)} transition-all`}
          style={{ width: `${probability}%` }}
        />
      </div>
      <span className="text-[10px] font-bold text-gray-500">{probability}%</span>
    </div>
  );
}

// Hero Card - Featured article with smaller image
export function HeroCard({ article, isLive = false }) {
  if (!article) return null;
  
  const clubLogo = getClubLogo(article.title);
  
  return (
    <Link to={"/news/" + article.slug} className="block relative" data-testid={"hero-" + article.id}>
      <div className="relative aspect-[16/8] bg-gray-900">
        <ArticleImage
          src={article.hero_image || article.feature_image}
          alt={article.title}
          className="w-full h-full object-cover"
          articleId={article.id}
        />
        
        {/* Club Logo - Top Right */}
        {clubLogo && (
          <img 
            src={clubLogo} 
            alt="" 
            className="absolute top-3 right-3 w-12 h-12 object-contain drop-shadow-lg"
          />
        )}
        
        {/* Status Badge - Top Left */}
        <div className="absolute top-3 left-3 flex items-center gap-2">
          {isLive && (
            <div className="bg-[#e91e63] text-white text-xs font-bold px-2 py-1 flex items-center gap-1">
              <Circle size={8} weight="fill" className="animate-pulse" />
              LIVE
            </div>
          )}
          <TransferBadge status={article.transfer_status} />
        </div>
        
        {/* Gradient Overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/30 to-transparent" />
        
        {/* Content */}
        <div className="absolute bottom-0 left-0 right-0 p-4">
          {/* Probability Bar */}
          {article.transfer_probability && (
            <div className="mb-2 max-w-[180px]">
              <ProbabilityBar probability={article.transfer_probability} />
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
  
  const clubLogo = getClubLogo(article.title);
  
  return (
    <Link 
      to={"/news/" + article.slug} 
      className="flex gap-3 p-3 bg-white border-b border-gray-100"
      data-testid={"news-card-" + article.id}
    >
      {/* Image */}
      <div className="relative w-[100px] h-[70px] flex-shrink-0 bg-gray-100 overflow-hidden rounded">
        <ArticleImage
          src={article.hero_image || article.feature_image}
          alt={article.title}
          className="w-full h-full object-cover"
          articleId={article.id}
        />
        
        {/* Club Logo - Top Right */}
        {clubLogo && (
          <img 
            src={clubLogo} 
            alt="" 
            className="absolute top-0.5 right-0.5 w-6 h-6 object-contain drop-shadow-md"
          />
        )}
      </div>
      
      {/* Content */}
      <div className="flex-1 flex flex-col justify-center py-0.5">
        <div className="flex items-center gap-2 mb-1">
          <TransferBadge status={article.transfer_status} />
          <span className="text-[10px] text-gray-400">{formatTime(article.published_at)}</span>
        </div>
        
        <h3 className="text-[14px] font-bold text-gray-900 leading-snug line-clamp-2" style={{ fontFamily: "'Oswald', sans-serif" }}>
          {article.title}
        </h3>
        
        {/* Probability Bar - smaller */}
        {article.transfer_probability && (
          <div className="mt-1.5 max-w-[150px]">
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
