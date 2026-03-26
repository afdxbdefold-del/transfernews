import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { AdSlot, SidebarAd } from "@/components/AdSlot";
import { NewsCardCompact } from "@/components/NewsCard";
import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getArticleBySlug, getPublishedArticles, getPlayer, getClub } from "@/api";
import { Clock, CaretLeft, ShareNetwork, User, Buildings, FacebookLogo, XLogo, WhatsappLogo, EnvelopeSimple } from "@phosphor-icons/react";
import { Skeleton } from "@/components/ui/skeleton";
import { Helmet } from "react-helmet-async";

// Schema.org NewsArticle for Google Discover
function ArticleSchema({ article }) {
  if (!article) return null;
  
  const schema = {
    "@context": "https://schema.org",
    "@type": "NewsArticle",
    "headline": article.title,
    "description": article.excerpt || article.title,
    "image": article.feature_image ? [
      window.location.origin + article.feature_image
    ] : [],
    "datePublished": article.published_at,
    "dateModified": article.updated_at || article.published_at,
    "author": {
      "@type": "Organization",
      "name": "transfernews.de",
      "url": "https://transfernews.de"
    },
    "publisher": {
      "@type": "Organization",
      "name": "transfernews.de",
      "logo": {
        "@type": "ImageObject",
        "url": window.location.origin + "/logo.svg"
      }
    },
    "mainEntityOfPage": {
      "@type": "WebPage",
      "@id": window.location.href
    },
    "articleSection": "Transfer News",
    "keywords": ["Fußball", "Transfer", "Bundesliga", article.category || "Transfer"].join(", ")
  };

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
    />
  );
}

export default function NewsDetailPage() {
  const { slug } = useParams();
  const [article, setArticle] = useState(null);
  const [relatedNews, setRelatedNews] = useState([]);
  const [linkedPlayers, setLinkedPlayers] = useState([]);
  const [linkedClubs, setLinkedClubs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const res = await getArticleBySlug(slug);
        setArticle(res.data);

        // Fetch related news
        const relatedRes = await getPublishedArticles({ limit: 5 });
        setRelatedNews(relatedRes.data.filter((a) => a.slug !== slug).slice(0, 4));

        // Fetch linked entities
        if (res.data.linked_player_ids?.length > 0) {
          const players = await Promise.all(
            res.data.linked_player_ids.slice(0, 3).map((id) => getPlayer(id).catch(() => null))
          );
          setLinkedPlayers(players.filter(Boolean).map((r) => r.data));
        }

        if (res.data.linked_club_ids?.length > 0) {
          const clubs = await Promise.all(
            res.data.linked_club_ids.slice(0, 3).map((id) => getClub(id).catch(() => null))
          );
          setLinkedClubs(clubs.filter(Boolean).map((r) => r.data));
        }
      } catch (e) {
        console.error("Article load error:", e);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [slug]);

  const formatDate = (dateString) => {
    if (!dateString) return "";
    const date = new Date(dateString);
    return date.toLocaleDateString("de-DE", {
      day: "2-digit",
      month: "long",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const formatRelativeTime = (dateString) => {
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

  const getTypeBadge = (type) => {
    const badges = {
      news: { label: "NEWS", class: "bg-[#79B92A] text-white" },
      rumour: { label: "GERÜCHT", class: "bg-yellow-100 text-yellow-800" },
      transfer: { label: "TRANSFER", class: "bg-green-100 text-green-800" },
      analysis: { label: "ANALYSE", class: "bg-blue-100 text-blue-800" },
    };
    return badges[type] || badges.news;
  };

  // Split body into paragraphs for ad insertion
  const paragraphs = article?.body?.split("\n\n").filter(Boolean) || [];

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col bg-[#f5f5f5]">
        <Header />
        <main className="flex-1">
          <div className="max-w-[1200px] mx-auto px-3 py-6">
            <div className="bg-white p-6">
              <Skeleton className="h-8 w-3/4 mb-4" />
              <Skeleton className="h-64 w-full mb-4" />
              <Skeleton className="h-4 w-full mb-2" />
              <Skeleton className="h-4 w-full mb-2" />
              <Skeleton className="h-4 w-2/3" />
            </div>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  if (!article) {
    return (
      <div className="min-h-screen flex flex-col bg-[#f5f5f5]">
        <Header />
        <main className="flex-1 flex items-center justify-center">
          <div className="text-center bg-white p-8">
            <h1 
              className="text-2xl font-black uppercase mb-4"
              style={{ fontFamily: "'Oswald', sans-serif" }}
            >
              Artikel nicht gefunden
            </h1>
            <Link to="/news" className="text-[#79B92A] hover:underline font-bold">
              Zurück zum Newsticker
            </Link>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  const badge = getTypeBadge(article.article_type);
  const shareUrl = encodeURIComponent(window.location.href);
  const shareTitle = encodeURIComponent(article.title);

  return (
    <div className="min-h-screen flex flex-col bg-[#f5f5f5]" data-testid="news-detail-page">
      {/* SEO Meta Tags for Google Discover */}
      {article && (
        <Helmet>
          <title>{`${article.title || 'Transfer News'} | transfernews.de`}</title>
          <meta name="description" content={article.excerpt || article.title || ''} />
          <meta property="og:title" content={article.title || 'Transfer News'} />
          <meta property="og:description" content={article.excerpt || article.title || ''} />
          <meta property="og:image" content={article.feature_image ? window.location.origin + article.feature_image : ''} />
          <meta property="og:type" content="article" />
          <meta property="article:published_time" content={article.published_at || ''} />
          <meta property="article:section" content="Transfer News" />
          <meta name="twitter:card" content="summary_large_image" />
          <meta name="twitter:title" content={article.title || 'Transfer News'} />
          <meta name="twitter:description" content={article.excerpt || article.title || ''} />
          <meta name="robots" content="max-image-preview:large" />
        </Helmet>
      )}
      
      {/* Schema.org NewsArticle */}
      <ArticleSchema article={article} />
      
      <Header />

      {/* Top Ad */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-[1200px] mx-auto px-3 py-2">
          <AdSlot slotKey="below_header" minHeight="90px" />
        </div>
      </div>

      <main className="flex-1">
        <div className="max-w-[1200px] mx-auto px-3 py-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Article Content */}
            <article className="lg:col-span-2">
              {/* Back Link */}
              <Link
                to="/news"
                className="inline-flex items-center gap-1 text-sm text-gray-600 hover:text-[#79B92A] mb-4 transition-colors"
                data-testid="back-link"
              >
                <CaretLeft size={16} weight="bold" />
                <span className="font-medium">Zurück zum Newsticker</span>
              </Link>

              {/* Article Card */}
              <div className="bg-white">
                {/* Feature Image */}
                {article.feature_image ? (
                  <div className="relative aspect-video bg-gray-100">
                    <img
                      src={article.feature_image}
                      alt={article.title}
                      className="w-full h-full object-cover"
                    />
                    {/* Breaking Badge on Image */}
                    {article.is_breaking && (
                      <div className="absolute top-4 left-4">
                        <span className="bg-red-600 text-white text-xs font-bold px-2 py-1 uppercase">
                          Breaking
                        </span>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="aspect-video bg-gradient-to-br from-[#3d5c1f] to-[#79B92A] flex items-center justify-center">
                    <span className="text-white/20 text-8xl font-black">TN</span>
                  </div>
                )}
                
                {/* Article Header */}
                <div className="p-4 md:p-6">
                  {/* Category & Time */}
                  <div className="flex items-center gap-3 mb-3">
                    <span className={`text-xs font-bold px-2 py-1 ${badge.class}`}>
                      {badge.label}
                    </span>
                    <span className="text-sm text-gray-500">
                      {formatRelativeTime(article.published_at)}
                    </span>
                  </div>

                  {/* Title */}
                  <h1
                    className="text-2xl md:text-3xl lg:text-4xl font-black leading-tight mb-4"
                    style={{ fontFamily: "'Oswald', sans-serif" }}
                    data-testid="article-title"
                  >
                    {article.title}
                  </h1>

                  {/* Meta Row */}
                  <div className="flex items-center justify-between py-3 border-t border-b border-gray-100 mb-4">
                    <div className="flex items-center gap-2 text-sm text-gray-500">
                      <Clock size={16} />
                      <span>{formatDate(article.published_at)}</span>
                    </div>
                    
                    {/* Share Buttons */}
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-gray-400 mr-2 hidden sm:inline">Teilen:</span>
                      <a 
                        href={`https://www.facebook.com/sharer/sharer.php?u=${shareUrl}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="w-8 h-8 bg-[#1877f2] text-white flex items-center justify-center hover:opacity-80 transition-opacity"
                      >
                        <FacebookLogo size={16} weight="fill" />
                      </a>
                      <a 
                        href={`https://twitter.com/intent/tweet?url=${shareUrl}&text=${shareTitle}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="w-8 h-8 bg-black text-white flex items-center justify-center hover:opacity-80 transition-opacity"
                      >
                        <XLogo size={16} weight="fill" />
                      </a>
                      <a 
                        href={`https://wa.me/?text=${shareTitle}%20${shareUrl}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="w-8 h-8 bg-[#25d366] text-white flex items-center justify-center hover:opacity-80 transition-opacity"
                      >
                        <WhatsappLogo size={16} weight="fill" />
                      </a>
                      <a 
                        href={`mailto:?subject=${shareTitle}&body=${shareUrl}`}
                        className="w-8 h-8 bg-gray-600 text-white flex items-center justify-center hover:opacity-80 transition-opacity"
                      >
                        <EnvelopeSimple size={16} weight="fill" />
                      </a>
                    </div>
                  </div>

                  {/* Excerpt */}
                  {article.excerpt && (
                    <p className="text-lg text-gray-800 font-medium leading-relaxed border-l-4 border-[#79B92A] pl-4 mb-6">
                      {article.excerpt}
                    </p>
                  )}
                </div>
              </div>

              {/* Ad below excerpt */}
              <div className="my-4">
                <AdSlot slotKey="article_below_excerpt" minHeight="90px" />
              </div>

              {/* Article Body */}
              <div className="bg-white p-4 md:p-6">
                <div className="prose prose-lg max-w-none">
                  {paragraphs.map((paragraph, idx) => (
                    <div key={idx}>
                      <p className="mb-4 text-gray-700 leading-relaxed text-base md:text-lg">
                        {paragraph}
                      </p>
                      {/* Insert ad after every 3rd paragraph */}
                      {(idx + 1) % 3 === 0 && idx < paragraphs.length - 1 && (
                        <div className="my-6">
                          <AdSlot slotKey={`article_after_paragraph_${Math.min(idx + 1, 3)}`} minHeight="90px" />
                        </div>
                      )}
                    </div>
                  ))}

                  {!article.body && (
                    <p className="text-gray-500 italic">Kein Inhalt verfügbar</p>
                  )}
                </div>

                {/* Linked Entities */}
                {(linkedPlayers.length > 0 || linkedClubs.length > 0) && (
                  <div className="mt-8 pt-6 border-t border-gray-100">
                    <h3 
                      className="text-lg font-black uppercase mb-4"
                      style={{ fontFamily: "'Oswald', sans-serif" }}
                    >
                      Mehr zum Thema
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      {linkedPlayers.map((player) => (
                        <Link
                          key={player.id}
                          to={`/spieler/${player.slug}`}
                          className="flex items-center gap-2 px-3 py-2 bg-gray-100 hover:bg-[#79B92A] hover:text-white transition-colors text-sm font-medium"
                        >
                          <User size={16} />
                          {player.name}
                        </Link>
                      ))}
                      {linkedClubs.map((club) => (
                        <Link
                          key={club.id}
                          to={`/verein/${club.slug}`}
                          className="flex items-center gap-2 px-3 py-2 bg-gray-100 hover:bg-[#79B92A] hover:text-white transition-colors text-sm font-medium"
                        >
                          <Buildings size={16} />
                          {club.name}
                        </Link>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Ad before related */}
              <div className="my-4">
                <AdSlot slotKey="article_before_related" minHeight="90px" />
              </div>

              {/* Related News */}
              {relatedNews.length > 0 && (
                <div className="bg-white">
                  <div className="p-4 border-b border-gray-100">
                    <h3 
                      className="text-xl font-black uppercase"
                      style={{ fontFamily: "'Oswald', sans-serif" }}
                    >
                      Weitere News
                    </h3>
                  </div>
                  <div className="divide-y divide-gray-100 px-4">
                    {relatedNews.map((news) => (
                      <NewsCardCompact key={news.id} article={news} />
                    ))}
                  </div>
                </div>
              )}

              {/* Ad after related */}
              <div className="mt-4">
                <AdSlot slotKey="article_after_related" minHeight="90px" />
              </div>
            </article>

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
