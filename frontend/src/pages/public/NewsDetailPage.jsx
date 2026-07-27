import Header from "@/components/Header";
import Footer from "@/components/Footer";
import PageLayout from "@/components/PageLayout";
import { AdSlot, SidebarAd } from "@/components/AdSlot";
import { NewsCardCompact } from "@/components/NewsCard";
import { TrendingWidget } from "@/components/TrendingWidget";
import { RelatedLinks } from "@/components/RelatedLinks";
import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getArticleBySlug, getPublishedArticles, getPlayer, getClub, getPublicNewsDetail } from "@/api";
import { Clock, CaretLeft, ShareNetwork, User, Buildings, FacebookLogo, XLogo, WhatsappLogo, EnvelopeSimple, CurrencyEur, Calendar, MapPin, SoccerBall, ShieldCheck, Newspaper, CheckCircle, Info } from "@phosphor-icons/react";
import { Skeleton } from "@/components/ui/skeleton";
import { Helmet } from "react-helmet-async";

// Source Trust Badge Komponente
function SourceBadge({ article }) {
  const source = article.primary_source || article.source_name;
  const secondarySources = article.secondary_sources || [];
  
  if (!source) return null;
  
  // Tier-Klassifizierung
  const tier1Sources = ["Sky Sports", "L'Équipe", "kicker", "BILD", "Marca", "Gazzetta dello Sport"];
  const tier2Sources = ["BBC Sport", "Goal", "AS", "Corriere dello Sport", "RMC Sport", "Sport1"];
  
  let tier = 3;
  let tierColor = "bg-orange-100 text-orange-700 border-orange-200";
  let tierLabel = "Gerücht";
  
  if (tier1Sources.some(s => source.includes(s))) {
    tier = 1;
    tierColor = "bg-green-100 text-green-700 border-green-200";
    tierLabel = "Tier 1";
  } else if (tier2Sources.some(s => source.includes(s))) {
    tier = 2;
    tierColor = "bg-yellow-100 text-yellow-700 border-yellow-200";
    tierLabel = "Tier 2";
  }
  
  return (
    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-6">
      <div className="flex items-center gap-2 mb-3">
        <Newspaper size={18} className="text-gray-500" />
        <span className="text-sm font-semibold text-gray-700">Quellen</span>
      </div>
      
      <div className="flex flex-wrap items-center gap-2">
        {/* Primary Source */}
        <div className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-sm font-medium ${tierColor}`}>
          {tier === 1 && <ShieldCheck size={14} weight="fill" />}
          <span>{source}</span>
          <span className="text-xs opacity-75">({tierLabel})</span>
        </div>
        
        {/* Secondary Sources */}
        {secondarySources.slice(0, 2).map((sec, i) => (
          <div key={i} className="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 text-gray-600 rounded-full text-xs">
            <span>+{sec}</span>
          </div>
        ))}
        
        {secondarySources.length > 2 && (
          <span className="text-xs text-gray-400">+{secondarySources.length - 2} weitere</span>
        )}
      </div>
      
      {/* Confidence Score wenn vorhanden */}
      {article.confidence_score && article.confidence_score > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-200">
          <div className="flex items-center justify-between text-xs text-gray-500">
            <span>Konfidenz-Score</span>
            <span className="font-medium">{article.confidence_score}%</span>
          </div>
          <div className="mt-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
            <div 
              className={`h-full rounded-full ${
                article.confidence_score >= 80 ? 'bg-green-500' :
                article.confidence_score >= 60 ? 'bg-yellow-500' : 'bg-orange-500'
              }`}
              style={{ width: `${article.confidence_score}%` }}
            />
          </div>
        </div>
      )}
    </div>
  );
}

// Fact-Check Badge
function FactCheckBadge({ article }) {
  if (!article.author_name) return null;
  
  const updateDate = article.updated_at || article.gpt_rewritten_at || article.published_at;
  const formattedDate = updateDate ? new Date(updateDate).toLocaleDateString('de-DE', {
    day: '2-digit',
    month: 'long',
    year: 'numeric'
  }) : null;
  
  return (
    <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
          <CheckCircle size={20} className="text-green-600" weight="fill" />
        </div>
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="font-semibold text-green-800">Geprüfter Artikel</span>
          </div>
          <p className="text-sm text-green-700">
            Dieser Artikel wurde von <strong>{article.author_name}</strong> 
            {article.author_role && <span className="text-green-600"> ({article.author_role})</span>} verfasst und redaktionell geprüft.
          </p>
          {formattedDate && (
            <p className="text-xs text-green-600 mt-1">
              Zuletzt aktualisiert: {formattedDate}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

// Info-Box Komponente für strukturierte Spielerdaten (Marktwert, Vertrag, etc.)
function PlayerInfoBox({ article }) {
  // Nur anzeigen wenn mindestens ein strukturiertes Feld vorhanden
  const hasData = article.market_value || article.contract_until || article.player_age || article.player_position;
  
  if (!hasData) return null;
  
  return (
    <div 
      className="bg-gradient-to-r from-gray-900 to-gray-800 text-white p-4 md:p-5"
      data-testid="player-info-box"
    >
      <div className="flex items-center gap-2 mb-3">
        <SoccerBall size={18} weight="fill" className="text-[#79B92A]" />
        <span 
          className="text-sm font-bold uppercase tracking-wide text-gray-300"
          style={{ fontFamily: "'Oswald', sans-serif" }}
        >
          Spieler-Profil
        </span>
      </div>
      
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Marktwert */}
        {article.market_value && (
          <div className="space-y-1">
            <div className="flex items-center gap-1.5 text-gray-400 text-xs uppercase">
              <CurrencyEur size={14} />
              <span>Marktwert</span>
            </div>
            <div className="text-lg md:text-xl font-bold text-[#79B92A]">
              {article.market_value}
            </div>
          </div>
        )}
        
        {/* Vertrag bis */}
        {article.contract_until && (
          <div className="space-y-1">
            <div className="flex items-center gap-1.5 text-gray-400 text-xs uppercase">
              <Calendar size={14} />
              <span>Vertrag bis</span>
            </div>
            <div className="text-lg md:text-xl font-bold">
              {article.contract_until}
            </div>
          </div>
        )}
        
        {/* Alter */}
        {article.player_age && (
          <div className="space-y-1">
            <div className="flex items-center gap-1.5 text-gray-400 text-xs uppercase">
              <User size={14} />
              <span>Alter</span>
            </div>
            <div className="text-lg md:text-xl font-bold">
              {article.player_age} Jahre
            </div>
          </div>
        )}
        
        {/* Position */}
        {article.player_position && (
          <div className="space-y-1">
            <div className="flex items-center gap-1.5 text-gray-400 text-xs uppercase">
              <MapPin size={14} />
              <span>Position</span>
            </div>
            <div className="text-lg md:text-xl font-bold">
              {article.player_position}
            </div>
          </div>
        )}
      </div>
      
      {/* Zusätzliche Infos in zweiter Reihe */}
      {(article.player_nationality || article.current_club || article.player_full_name) && (
        <div className="mt-3 pt-3 border-t border-gray-700 flex flex-wrap gap-x-4 gap-y-1 text-sm text-gray-400">
          {article.player_full_name && article.player_full_name !== article.player_name && (
            <span>Name: <span className="text-white">{article.player_full_name}</span></span>
          )}
          {article.player_nationality && (
            <span>Nationalität: <span className="text-white">{article.player_nationality}</span></span>
          )}
          {article.current_club && (
            <span>Verein: <span className="text-white">{article.current_club}</span></span>
          )}
        </div>
      )}
    </div>
  );
}

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
      "@type": "Person",
      "name": article.author_name || "Redaktion",
      "url": `https://transfernews.de/autor/${article.author_slug || 'redaktion'}`
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
    "wordCount": article.word_count || 0,
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
  const [relatedLinks, setRelatedLinks] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Try to get article with related links first
        let articleData;
        try {
          const publicRes = await getPublicNewsDetail(slug);
          articleData = publicRes.data;
          setRelatedLinks(articleData.related_links || []);
        } catch {
          // Fallback to regular endpoint
          const res = await getArticleBySlug(slug);
          articleData = res.data;
        }
        
        setArticle(articleData);

        // Fetch related news
        const relatedRes = await getPublishedArticles({ limit: 5 });
        setRelatedNews(relatedRes.data.filter((a) => a.slug !== slug).slice(0, 4));

        // Fetch linked entities
        if (articleData.linked_player_ids?.length > 0) {
          const players = await Promise.all(
            articleData.linked_player_ids.slice(0, 3).map((id) => getPlayer(id).catch(() => null))
          );
          setLinkedPlayers(players.filter(Boolean).map((r) => r.data));
        }

        if (articleData.linked_club_ids?.length > 0) {
          const clubs = await Promise.all(
            articleData.linked_club_ids.slice(0, 3).map((id) => getClub(id).catch(() => null))
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
  // Handle both \n\n (double newline) and ## headings
  const paragraphs = article?.body
    ?.split(/\n\n/)
    .flatMap(block => {
      // Check if block contains a heading followed by text
      const headingMatch = block.match(/^(## .+?)(?:\n(.+))?$/s);
      if (headingMatch && headingMatch[2]) {
        // Split heading and following text
        return [headingMatch[1], headingMatch[2]];
      }
      return [block];
    })
    .map(p => p.trim())
    .filter(Boolean) || [];

  if (loading) {
    return (
      <PageLayout>
        <Header />
        <main className="flex-1 py-3 px-3">
            <div className="bg-white p-6">
              <Skeleton className="h-8 w-3/4 mb-4" />
              <Skeleton className="h-64 w-full mb-4" />
              <Skeleton className="h-4 w-full mb-2" />
              <Skeleton className="h-4 w-full mb-2" />
              <Skeleton className="h-4 w-2/3" />
            </div>
        </main>
        <Footer />
      </PageLayout>
    );
  }

  if (!article) {
    return (
      <PageLayout>
        <Header />
        <main className="flex-1 flex items-center justify-center py-3 px-3">
          <div className="text-center bg-white p-8">
            <h1 
              className="text-2xl font-black uppercase mb-4"
              style={{ fontFamily: "'Oswald', sans-serif" }}
            >
              Artikel nicht gefunden
            </h1>
            <Link to="/" className="text-[#79B92A] hover:underline font-bold">
              Zurück zur Startseite
            </Link>
          </div>
        </main>
        <Footer />
      </PageLayout>
    );
  }

  const badge = getTypeBadge(article.article_type);
  const shareUrl = encodeURIComponent(window.location.href);
  const shareTitle = encodeURIComponent(article.title);

  return (
    <PageLayout>
      {/* SEO Meta Tags for Google Discover */}
      {article && (
        <Helmet>
          <title>{`${article.title || 'Transfer News'} | transfernews.de`}</title>
          <meta name="description" content={article.excerpt || article.title || ''} />
          <meta property="og:title" content={article.title || 'Transfer News'} />
          <meta property="og:description" content={article.excerpt || article.title || ''} />
          {/* Google Discover optimiertes Bild (min 1200px) */}
          <meta property="og:image" content={article.og_image || article.hero_image || (article.feature_image ? window.location.origin + article.feature_image : '')} />
          <meta property="og:image:width" content={article.hero_image_width || "1200"} />
          <meta property="og:image:height" content={article.hero_image_height || "675"} />
          <meta property="og:type" content="article" />
          <meta property="article:published_time" content={article.published_at || ''} />
          <meta property="article:modified_time" content={article.updated_at || article.published_at || ''} />
          <meta property="article:section" content="Transfer News" />
          <meta name="twitter:card" content="summary_large_image" />
          <meta name="twitter:title" content={article.title || 'Transfer News'} />
          <meta name="twitter:description" content={article.excerpt || article.title || ''} />
          <meta name="twitter:image" content={article.og_image || article.hero_image || ''} />
          <meta name="robots" content="max-image-preview:large" />
        </Helmet>
      )}
      
      {/* Schema.org NewsArticle */}
      <ArticleSchema article={article} />
      
      <Header />

      {/* Top Ad */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-[1000px] mx-auto px-3 py-2">
          <AdSlot slotKey="below_header" minHeight="90px" />
        </div>
      </div>

      <main className="flex-1">
        <div className="max-w-[1000px] mx-auto px-3 py-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Article Content */}
            <article className="lg:col-span-2">
              {/* Back Link */}
              <Link
                to="/"
                className="inline-flex items-center gap-1 text-sm text-gray-600 hover:text-[#79B92A] mb-4 transition-colors"
                data-testid="back-link"
              >
                <CaretLeft size={16} weight="bold" />
                <span className="font-medium">Zurück</span>
              </Link>

              {/* Article Card */}
              <div className="bg-white">
                {/* Feature/Hero Image - Optimiert für Google Discover (min 1200px) */}
                {(article.hero_image || article.feature_image) ? (
                  <div className="relative">
                    <div className="aspect-[16/10] bg-gray-100">
                      <img
                        src={article.hero_image || article.feature_image}
                        alt={article.hero_image_alt || article.title}
                        className="w-full h-full object-cover object-top"
                        width={article.hero_image_width || 1200}
                        height={article.hero_image_height || 675}
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
                    {/* Bild-Attribution (Wikimedia Commons / Unsplash) */}
                    {article.hero_image_meta && (
                      <div 
                        className="bg-gray-800 text-gray-300 text-xs px-3 py-1.5 flex items-center justify-between"
                        data-testid="image-attribution"
                      >
                        <span>
                          {article.hero_image_meta.is_fallback ? (
                            <>Foto: {article.hero_image_meta.author} / {article.hero_image_meta.license_name}</>
                          ) : (
                            <>
                              Foto: {article.hero_image_meta.author || 'Unbekannt'} / 
                              <a 
                                href={article.hero_image_meta.source_url || '#'} 
                                target="_blank" 
                                rel="noopener noreferrer"
                                className="hover:text-white ml-1 underline"
                              >
                                Wikimedia Commons
                              </a>
                              <span className="ml-1">/ {article.hero_image_meta.license_name || 'CC'}</span>
                            </>
                          )}
                        </span>
                        {article.hero_image_meta.quality_score > 0 && (
                          <span className="text-gray-500 ml-2" title="Bildqualitäts-Score">
                            Q{article.hero_image_meta.quality_score}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="aspect-video bg-gradient-to-br from-[#3d5c1f] to-[#79B92A] flex items-center justify-center">
                    <span className="text-white/20 text-8xl font-black">TN</span>
                  </div>
                )}
                
                {/* Player Info Box (Marktwert, Vertrag, etc.) */}
                <PlayerInfoBox article={article} />
                
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

                  {/* Author & Reading Time */}
                  <div className="flex items-center gap-4 mb-4 text-sm">
                    <Link 
                      to={`/autor/${article.author_id || 'redaktion'}`}
                      className="flex items-center gap-2 hover:opacity-80 transition-opacity"
                    >
                      {article.author_image ? (
                        <img 
                          src={article.author_image} 
                          alt={article.author_name}
                          className="w-10 h-10 rounded-full object-cover object-top"
                        />
                      ) : (
                        <div className="w-10 h-10 rounded-full bg-[#79B92A] flex items-center justify-center text-white font-bold text-sm">
                          {article.author_name?.charAt(0) || 'R'}
                        </div>
                      )}
                      <div>
                        <span className="font-medium text-gray-900 hover:text-[#79B92A] transition-colors">{article.author_name || 'Redaktion'}</span>
                        {article.author_role && (
                          <span className="text-gray-400 text-xs block">{article.author_role}</span>
                        )}
                      </div>
                      <span className="text-gray-400 mx-1">·</span>
                      <span className="text-gray-500">{article.reading_time_minutes || 1} Min. Lesezeit</span>
                    </Link>
                    {article.word_count > 0 && (
                      <span className="text-gray-400 text-xs hidden md:inline">
                        ({article.word_count} Wörter)
                      </span>
                    )}
                  </div>

                  {/* Meta Row */}
                  <div className="flex items-center justify-between py-3 border-t border-b border-gray-100 mb-4">
                    <div className="flex items-center gap-3 text-sm text-gray-500">
                      <div className="flex items-center gap-1.5">
                        <Clock size={14} />
                        <span>{formatDate(article.published_at)}</span>
                      </div>
                      {article.updated_at && article.updated_at !== article.published_at && (
                        <span className="text-[#79B92A] text-xs font-medium">
                          Aktualisiert
                        </span>
                      )}
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
                  {paragraphs.map((paragraph, idx) => {
                    // Check if paragraph is a H2 heading (starts with ##)
                    const isH2 = paragraph.trim().startsWith('## ');
                    
                    if (isH2) {
                      const headingText = paragraph.trim().replace(/^##\s*/, '');
                      return (
                        <h2 
                          key={idx}
                          className="text-xl md:text-2xl font-bold text-gray-900 mt-6 mb-3"
                          style={{ fontFamily: "'Oswald', sans-serif" }}
                        >
                          {headingText}
                        </h2>
                      );
                    }
                    
                    return (
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
                    );
                  })}

                  {!article.body && (
                    <p className="text-gray-500 italic">Kein Inhalt verfügbar</p>
                  )}
                </div>
                
                {/* Source Badge & Fact-Check (E-E-A-T) */}
                <div className="mt-8 grid md:grid-cols-2 gap-4">
                  <SourceBadge article={article} />
                  <FactCheckBadge article={article} />
                </div>

                {/* Auto-generated Related Links from Trending System */}
                {relatedLinks.length > 0 && (
                  <div className="mt-6">
                    <RelatedLinks links={relatedLinks} />
                  </div>
                )}
                
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
              <TrendingWidget />
              <SidebarAd slotKey="sidebar_top" />
              <SidebarAd slotKey="sidebar_middle" />
            </aside>
          </div>
        </div>
      </main>

      <Footer />
    </PageLayout>
  );
}
