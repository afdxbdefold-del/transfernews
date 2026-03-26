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

// Hero Card - Big featured article with overlay text
export function HeroCard({ article, isLive = false }) {
  if (!article) return null;
  
  return (
    <Link to={"/news/" + article.slug} className="block relative" data-testid={"hero-" + article.id}>
      <div className="relative aspect-[16/10] bg-gray-900">
        <ArticleImage
          src={article.feature_image}
          alt={article.title}
          className="w-full h-full object-cover"
          articleId={article.id}
        />
        
        {/* Live Badge */}
        {isLive && (
          <div className="absolute top-3 left-3 bg-[#e91e63] text-white text-xs font-bold px-2 py-1 flex items-center gap-1">
            <Circle size={8} weight="fill" className="animate-pulse" />
            LIVE
          </div>
        )}
        
        {/* Gradient Overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/40 to-transparent" />
        
        {/* Content */}
        <div className="absolute bottom-0 left-0 right-0 p-4">
          <h2 className="text-white text-lg md:text-xl font-black uppercase leading-tight mb-3" style={{ fontFamily: "'Oswald', sans-serif" }}>
            {article.title}
          </h2>
          <button className="bg-[#00a8e8] text-white text-sm font-bold uppercase px-6 py-2">
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
  
  return (
    <Link 
      to={"/news/" + article.slug} 
      className="flex gap-3 p-3 bg-white border-b border-gray-100"
      data-testid={"news-card-" + article.id}
    >
      {/* Image */}
      <div className="relative w-[140px] h-[95px] flex-shrink-0 bg-gray-100 overflow-hidden">
        <ArticleImage
          src={article.feature_image}
          alt={article.title}
          className="w-full h-full object-cover"
          articleId={article.id}
        />
        
        {/* Video Play Button & Duration */}
        {showVideo && (
          <>
            <div className="absolute bottom-2 left-2 w-8 h-8 bg-[#00a8e8] flex items-center justify-center">
              <Play size={16} weight="fill" className="text-white" />
            </div>
            <div className="absolute bottom-2 right-2 bg-black/80 text-white text-[10px] font-bold px-1.5 py-0.5">
              00:48
            </div>
          </>
        )}
      </div>
      
      {/* Content */}
      <div className="flex-1 flex flex-col justify-between py-0.5">
        <h3 className="text-[15px] font-bold text-gray-900 leading-snug line-clamp-2" style={{ fontFamily: "'Oswald', sans-serif" }}>
          {article.title}
        </h3>
        
        {/* Meta */}
        <div className="flex items-center justify-between mt-2">
          <div className="flex items-center gap-1.5">
            <div className="w-4 h-4 bg-[#79B92A] rounded-full" />
            <span className="text-[11px] text-gray-500 font-medium uppercase">{article.category || "TRANSFER"}</span>
          </div>
          <span className="text-[11px] text-gray-400">{formatTime(article.published_at)}</span>
        </div>
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
