import { Link } from "react-router-dom";
import { Clock } from "@phosphor-icons/react";

// Format date to relative time or specific format
const formatDate = (dateString) => {
  if (!dateString) return "";
  const date = new Date(dateString);
  const now = new Date();
  const diff = now - date;
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  
  if (minutes < 60) {
    return `vor ${minutes} Min.`;
  } else if (hours < 24) {
    return `vor ${hours} Std.`;
  } else {
    return date.toLocaleDateString("de-DE", { day: "2-digit", month: "2-digit" });
  }
};

const formatTime = (dateString) => {
  if (!dateString) return "";
  const date = new Date(dateString);
  return date.toLocaleTimeString("de-DE", { hour: "2-digit", minute: "2-digit" });
};

// Big Hero Teaser (Main Featured Article)
export function HeroTeaser({ article }) {
  if (!article) return null;

  return (
    <Link
      to={`/news/${article.slug}`}
      className="block relative group overflow-hidden"
      data-testid={`hero-teaser-${article.id}`}
    >
      <div className="relative aspect-[3/2] bg-gray-900">
        {article.feature_image ? (
          <img
            src={article.feature_image}
            alt={article.title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
          />
        ) : (
          <div className="w-full h-full bg-gradient-to-br from-[#3d5c1f] to-[#79B92A] flex items-center justify-center">
            <span className="text-white/20 text-8xl font-black">TN</span>
          </div>
        )}
        
        {/* Gradient Overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent" />
        
        {/* Content */}
        <div className="absolute bottom-0 left-0 right-0 p-4 md:p-6">
          {article.is_breaking && (
            <span className="inline-block bg-red-600 text-white text-xs font-bold px-2 py-1 mb-3 uppercase">
              Breaking
            </span>
          )}
          <h2 
            className="text-xl md:text-2xl lg:text-3xl font-black text-white leading-tight mb-2 group-hover:text-[#79B92A] transition-colors"
            style={{ fontFamily: "'Oswald', sans-serif" }}
          >
            {article.title}
          </h2>
          <div className="flex items-center gap-3 text-white/80 text-sm">
            {article.category && (
              <>
                <span className="font-medium">{article.category}</span>
                <span>•</span>
              </>
            )}
            <span>{formatDate(article.published_at)}</span>
          </div>
        </div>
      </div>
    </Link>
  );
}

// Medium Teaser (for 2-column grid below hero)
export function MediumTeaser({ article }) {
  if (!article) return null;

  return (
    <Link
      to={`/news/${article.slug}`}
      className="block bg-white group"
      data-testid={`medium-teaser-${article.id}`}
    >
      <div className="relative aspect-[3/2] overflow-hidden bg-gray-100">
        {article.feature_image ? (
          <img
            src={article.feature_image}
            alt={article.title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
        ) : (
          <div className="w-full h-full bg-gradient-to-br from-gray-200 to-gray-300 flex items-center justify-center">
            <span className="text-gray-400 text-4xl font-black">TN</span>
          </div>
        )}
        
        {article.article_type === "video" && (
          <div className="absolute bottom-2 right-2 bg-black/80 text-white text-xs font-bold px-2 py-1 rounded">
            VIDEO
          </div>
        )}
      </div>
      
      <div className="p-3">
        <h3 
          className="text-base font-bold text-gray-900 leading-snug group-hover:text-[#79B92A] transition-colors line-clamp-2"
          style={{ fontFamily: "'Oswald', sans-serif" }}
        >
          {article.title}
        </h3>
        <div className="flex items-center gap-2 mt-2 text-xs text-gray-500">
          {article.category && (
            <>
              <span className="font-medium text-gray-600">{article.category}</span>
              <span>•</span>
            </>
          )}
          <span>{formatDate(article.published_at)}</span>
        </div>
      </div>
    </Link>
  );
}

// List Teaser (horizontal layout with small image)
export function ListTeaser({ article }) {
  if (!article) return null;

  return (
    <Link
      to={`/news/${article.slug}`}
      className="flex gap-3 py-3 border-b border-gray-100 last:border-0 group"
      data-testid={`list-teaser-${article.id}`}
    >
      {/* Image */}
      <div className="w-[100px] h-[75px] flex-shrink-0 overflow-hidden bg-gray-100">
        {article.feature_image ? (
          <img
            src={article.feature_image}
            alt={article.title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
        ) : (
          <div className="w-full h-full bg-gradient-to-br from-gray-200 to-gray-300 flex items-center justify-center">
            <span className="text-gray-400 text-lg font-bold">TN</span>
          </div>
        )}
      </div>
      
      {/* Content */}
      <div className="flex-1 min-w-0">
        <h4 
          className="text-sm font-bold text-gray-900 leading-snug group-hover:text-[#79B92A] transition-colors line-clamp-2"
          style={{ fontFamily: "'Oswald', sans-serif" }}
        >
          {article.title}
        </h4>
        <div className="flex items-center gap-2 mt-1.5 text-xs text-gray-500">
          {article.category && (
            <span className="font-medium text-gray-600">{article.category}</span>
          )}
          <span>{formatDate(article.published_at)}</span>
        </div>
      </div>
    </Link>
  );
}

// Newsticker Entry (for sidebar news feed - sport1.de style)
export function NewsTickerEntry({ article, showImage = false }) {
  if (!article) return null;

  return (
    <Link
      to={`/news/${article.slug}`}
      className="flex items-start gap-3 py-3 border-b border-gray-100 last:border-0 group hover:bg-gray-50 transition-colors"
      data-testid={`newsticker-${article.id}`}
    >
      {/* Time Badge */}
      <div className="flex-shrink-0 w-12">
        <div className="bg-[#79B92A] text-white text-xs font-bold px-1.5 py-1 text-center" style={{ fontFamily: "'Oswald', sans-serif" }}>
          {formatTime(article.published_at)}
        </div>
      </div>
      
      {/* Content */}
      <div className="flex-1 min-w-0">
        {article.category && (
          <span className="text-[10px] font-medium text-gray-500 uppercase tracking-wide">
            {article.category}
          </span>
        )}
        <h5 
          className="text-sm font-bold text-gray-900 leading-snug group-hover:text-[#79B92A] transition-colors line-clamp-2 mt-0.5"
          style={{ fontFamily: "'Oswald', sans-serif" }}
        >
          {article.title}
        </h5>
      </div>
    </Link>
  );
}

// Standard News Card (for news list pages)
export function NewsCard({ article, featured = false }) {
  if (!article) return null;

  const getTypeBadge = (type) => {
    const badges = {
      news: { label: "News", class: "bg-[#79B92A] text-white" },
      rumour: { label: "Gerücht", class: "bg-yellow-100 text-yellow-800" },
      transfer: { label: "Transfer", class: "bg-green-100 text-green-800" },
      analysis: { label: "Analyse", class: "bg-blue-100 text-blue-800" },
    };
    return badges[type] || badges.news;
  };

  const badge = getTypeBadge(article.article_type);

  if (featured) {
    return (
      <Link
        to={`/news/${article.slug}`}
        className="block bg-white overflow-hidden group shadow-sm hover:shadow-md transition-shadow"
        data-testid={`news-card-featured-${article.id}`}
      >
        <div className="relative aspect-video bg-gray-100">
          {article.feature_image ? (
            <img
              src={article.feature_image}
              alt={article.title}
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            />
          ) : (
            <div className="w-full h-full bg-gradient-to-br from-[#3d5c1f] to-[#79B92A] flex items-center justify-center">
              <span className="text-white/30 text-6xl font-bold">TN</span>
            </div>
          )}
          {article.is_breaking && (
            <div className="absolute top-3 left-3">
              <span className="bg-red-600 text-white text-xs font-bold px-2 py-1 uppercase">Breaking</span>
            </div>
          )}
        </div>
        <div className="p-4">
          <div className="flex items-center gap-2 mb-2">
            <span className={`text-xs font-bold px-2 py-0.5 ${badge.class}`}>{badge.label}</span>
          </div>
          <h3 
            className="text-lg md:text-xl font-bold leading-tight mb-2 group-hover:text-[#79B92A] transition-colors"
            style={{ fontFamily: "'Oswald', sans-serif" }}
          >
            {article.title}
          </h3>
          {article.excerpt && (
            <p className="text-gray-600 text-sm line-clamp-2 mb-3">{article.excerpt}</p>
          )}
          <div className="flex items-center text-xs text-gray-500">
            <Clock size={14} className="mr-1" />
            {formatDate(article.published_at)}
          </div>
        </div>
      </Link>
    );
  }

  return (
    <Link
      to={`/news/${article.slug}`}
      className="flex gap-4 p-3 bg-white group hover:bg-gray-50 transition-colors border-b border-gray-100"
      data-testid={`news-card-${article.id}`}
    >
      {/* Thumbnail */}
      <div className="w-24 h-[72px] flex-shrink-0 overflow-hidden bg-gray-100">
        {article.feature_image ? (
          <img
            src={article.feature_image}
            alt={article.title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
        ) : (
          <div className="w-full h-full bg-gradient-to-br from-gray-200 to-gray-300 flex items-center justify-center">
            <span className="text-gray-400 text-lg font-bold">TN</span>
          </div>
        )}
      </div>
      
      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className={`text-[10px] font-bold px-1.5 py-0.5 ${badge.class}`}>{badge.label}</span>
          {article.is_breaking && (
            <span className="text-[10px] font-bold px-1.5 py-0.5 bg-red-100 text-red-700">BREAKING</span>
          )}
        </div>
        <h4 
          className="text-sm font-bold leading-snug group-hover:text-[#79B92A] transition-colors line-clamp-2"
          style={{ fontFamily: "'Oswald', sans-serif" }}
        >
          {article.title}
        </h4>
        <div className="flex items-center text-xs text-gray-500 mt-1">
          <Clock size={12} className="mr-1" />
          {formatDate(article.published_at)}
        </div>
      </div>
    </Link>
  );
}

// Compact News Card (for sidebar widgets)
export function NewsCardCompact({ article }) {
  if (!article) return null;

  return (
    <Link
      to={`/news/${article.slug}`}
      className="block py-2.5 border-b border-gray-100 hover:bg-gray-50 transition-colors group"
      data-testid={`news-compact-${article.id}`}
    >
      <h5 
        className="text-sm font-bold text-gray-900 group-hover:text-[#79B92A] transition-colors line-clamp-2"
        style={{ fontFamily: "'Oswald', sans-serif" }}
      >
        {article.title}
      </h5>
      <span className="text-xs text-gray-400 mt-1 block">{formatDate(article.published_at)}</span>
    </Link>
  );
}

// News Grid Component
export function NewsGrid({ articles, withAds = false, adInterval = 4 }) {
  if (!articles || articles.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        Keine News vorhanden
      </div>
    );
  }

  return (
    <div data-testid="news-grid">
      {articles.map((article, idx) => (
        <div key={article.id}>
          <NewsCard article={article} featured={idx === 0} />
          {withAds && (idx + 1) % adInterval === 0 && idx < articles.length - 1 && (
            <div className="my-4 ad-slot" style={{ minHeight: "90px" }} data-testid={`feed-ad-${idx}`}>
              <span className="text-xs text-gray-400">Anzeige</span>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
