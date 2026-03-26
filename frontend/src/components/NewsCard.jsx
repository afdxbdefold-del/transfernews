import { Link } from "react-router-dom";
import { Clock, ArrowRight } from "@phosphor-icons/react";
import { Badge } from "@/components/ui/badge";

export function NewsCard({ article, featured = false }) {
  const formatDate = (dateString) => {
    if (!dateString) return "";
    const date = new Date(dateString);
    return date.toLocaleDateString("de-DE", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const getTypeBadge = (type) => {
    const badges = {
      news: { label: "News", class: "bg-[#00a651] text-white" },
      rumour: { label: "Gerücht", class: "badge-rumour" },
      transfer: { label: "Transfer", class: "badge-confirmed" },
      analysis: { label: "Analyse", class: "bg-blue-100 text-blue-800" },
    };
    return badges[type] || badges.news;
  };

  const badge = getTypeBadge(article.article_type);

  if (featured) {
    return (
      <Link
        to={`/news/${article.slug}`}
        className="news-card block bg-white border border-gray-200 overflow-hidden group"
        data-testid={`news-card-featured-${article.id}`}
      >
        <div className="relative h-64 bg-gray-100">
          {article.feature_image ? (
            <img
              src={article.feature_image}
              alt={article.title}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full bg-gradient-to-br from-[#053f2c] to-[#00a651] flex items-center justify-center">
              <span className="text-white/30 text-6xl font-bold">TN</span>
            </div>
          )}
          <div className="absolute top-4 left-4">
            <Badge className={badge.class}>{badge.label}</Badge>
            {article.is_breaking && (
              <Badge className="ml-2 badge-breaking">BREAKING</Badge>
            )}
          </div>
        </div>
        <div className="p-6">
          <h3 className="font-['Oswald'] text-2xl font-bold uppercase leading-tight mb-3 group-hover:text-[#00a651] transition-colors">
            {article.title}
          </h3>
          {article.excerpt && (
            <p className="text-gray-600 text-sm line-clamp-2 mb-4">{article.excerpt}</p>
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
      className="news-card block bg-white border border-gray-200 p-4 group hover:border-[#00a651] transition-all"
      data-testid={`news-card-${article.id}`}
    >
      <div className="flex gap-4">
        {article.feature_image && (
          <div className="w-24 h-24 flex-shrink-0 bg-gray-100 overflow-hidden">
            <img
              src={article.feature_image}
              alt={article.title}
              className="w-full h-full object-cover"
            />
          </div>
        )}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <Badge className={`text-xs ${badge.class}`}>{badge.label}</Badge>
            {article.is_breaking && (
              <Badge className="text-xs badge-breaking">BREAKING</Badge>
            )}
          </div>
          <h4 className="font-['Oswald'] text-lg font-bold uppercase leading-tight mb-2 group-hover:text-[#00a651] transition-colors line-clamp-2">
            {article.title}
          </h4>
          <div className="flex items-center text-xs text-gray-500">
            <Clock size={12} className="mr-1" />
            {formatDate(article.published_at)}
          </div>
        </div>
        <ArrowRight size={20} className="text-gray-300 group-hover:text-[#00a651] transition-colors flex-shrink-0 self-center" />
      </div>
    </Link>
  );
}

export function NewsCardCompact({ article }) {
  const formatDate = (dateString) => {
    if (!dateString) return "";
    const date = new Date(dateString);
    return date.toLocaleDateString("de-DE", {
      day: "2-digit",
      month: "2-digit",
    });
  };

  return (
    <Link
      to={`/news/${article.slug}`}
      className="block py-3 border-b border-gray-100 hover:bg-gray-50 transition-colors group"
      data-testid={`news-compact-${article.id}`}
    >
      <h5 className="text-sm font-medium group-hover:text-[#00a651] transition-colors line-clamp-2 mb-1">
        {article.title}
      </h5>
      <span className="text-xs text-gray-400">{formatDate(article.published_at)}</span>
    </Link>
  );
}

export function NewsGrid({ articles, withAds = false, adInterval = 4 }) {
  if (!articles || articles.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        Keine News vorhanden
      </div>
    );
  }

  return (
    <div className="space-y-4" data-testid="news-grid">
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
