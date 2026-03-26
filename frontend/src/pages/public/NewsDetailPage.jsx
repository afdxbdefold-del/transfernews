import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { AdSlot, SidebarAd } from "@/components/AdSlot";
import { NewsCardCompact } from "@/components/NewsCard";
import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getArticleBySlug, getPublishedArticles, getPlayer, getClub } from "@/api";
import { Badge } from "@/components/ui/badge";
import { Clock, ArrowLeft, Share, User, Buildings } from "@phosphor-icons/react";
import { Skeleton } from "@/components/ui/skeleton";

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

  const getTypeBadge = (type) => {
    const badges = {
      news: { label: "News", class: "bg-[#00a651] text-white" },
      rumour: { label: "Gerücht", class: "badge-rumour" },
      transfer: { label: "Transfer", class: "badge-confirmed" },
      analysis: { label: "Analyse", class: "bg-blue-100 text-blue-800" },
    };
    return badges[type] || badges.news;
  };

  // Split body into paragraphs for ad insertion
  const paragraphs = article?.body?.split("\n\n").filter(Boolean) || [];

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col bg-gray-50">
        <Header />
        <main className="flex-1">
          <div className="max-w-4xl mx-auto px-4 py-8">
            <Skeleton className="h-8 w-3/4 mb-4" />
            <Skeleton className="h-64 w-full mb-4" />
            <Skeleton className="h-4 w-full mb-2" />
            <Skeleton className="h-4 w-full mb-2" />
            <Skeleton className="h-4 w-2/3" />
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  if (!article) {
    return (
      <div className="min-h-screen flex flex-col bg-gray-50">
        <Header />
        <main className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <h1 className="text-2xl font-bold mb-4">Artikel nicht gefunden</h1>
            <Link to="/news" className="text-[#00a651] hover:underline">
              Zurück zu den News
            </Link>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  const badge = getTypeBadge(article.article_type);

  return (
    <div className="min-h-screen flex flex-col bg-gray-50" data-testid="news-detail-page">
      <Header />

      {/* Top Ad */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-2">
          <AdSlot slotKey="below_header" minHeight="90px" />
        </div>
      </div>

      <main className="flex-1">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Article Content */}
            <article className="lg:col-span-2">
              {/* Breadcrumb */}
              <div className="mb-6">
                <Link
                  to="/news"
                  className="text-sm text-gray-500 hover:text-[#00a651] flex items-center"
                  data-testid="back-link"
                >
                  <ArrowLeft size={14} className="mr-1" />
                  Zurück zu den News
                </Link>
              </div>

              {/* Article Header */}
              <div className="bg-white border border-gray-200 mb-6">
                {article.feature_image && (
                  <div className="h-64 md:h-96 bg-gray-100">
                    <img
                      src={article.feature_image}
                      alt={article.title}
                      className="w-full h-full object-cover"
                    />
                  </div>
                )}
                
                <div className="p-6">
                  {/* Badges */}
                  <div className="flex items-center gap-2 mb-4">
                    <Badge className={badge.class}>{badge.label}</Badge>
                    {article.is_breaking && (
                      <Badge className="badge-breaking">BREAKING</Badge>
                    )}
                  </div>

                  {/* Title */}
                  <h1
                    className="font-['Oswald'] text-3xl md:text-4xl font-bold uppercase leading-tight mb-4"
                    data-testid="article-title"
                  >
                    {article.title}
                  </h1>

                  {/* Meta */}
                  <div className="flex items-center gap-4 text-sm text-gray-500 mb-4">
                    <span className="flex items-center">
                      <Clock size={16} className="mr-1" />
                      {formatDate(article.published_at)}
                    </span>
                    <button className="flex items-center hover:text-[#00a651]">
                      <Share size={16} className="mr-1" />
                      Teilen
                    </button>
                  </div>

                  {/* Excerpt */}
                  {article.excerpt && (
                    <p className="text-lg text-gray-700 font-medium border-l-4 border-[#00a651] pl-4">
                      {article.excerpt}
                    </p>
                  )}
                </div>
              </div>

              {/* Ad below title */}
              <AdSlot slotKey="article_below_excerpt" minHeight="90px" className="mb-6" />

              {/* Article Body */}
              <div className="bg-white border border-gray-200 p-6">
                <div className="prose prose-lg max-w-none">
                  {paragraphs.map((paragraph, idx) => (
                    <div key={idx}>
                      <p className="mb-4 text-gray-700 leading-relaxed">{paragraph}</p>
                      {/* Insert ad after every 2nd paragraph */}
                      {(idx + 1) % 2 === 0 && idx < paragraphs.length - 1 && (
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
                  <div className="mt-8 pt-6 border-t">
                    <h3 className="font-['Oswald'] text-lg font-bold uppercase mb-4">
                      Mehr zum Thema
                    </h3>
                    <div className="flex flex-wrap gap-3">
                      {linkedPlayers.map((player) => (
                        <Link
                          key={player.id}
                          to={`/spieler/${player.slug}`}
                          className="flex items-center px-3 py-2 bg-gray-100 hover:bg-gray-200 transition-colors"
                        >
                          <User size={16} className="mr-2 text-[#00a651]" />
                          {player.name}
                        </Link>
                      ))}
                      {linkedClubs.map((club) => (
                        <Link
                          key={club.id}
                          to={`/verein/${club.slug}`}
                          className="flex items-center px-3 py-2 bg-gray-100 hover:bg-gray-200 transition-colors"
                        >
                          <Buildings size={16} className="mr-2 text-[#00a651]" />
                          {club.name}
                        </Link>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Ad before related */}
              <AdSlot slotKey="article_before_related" minHeight="90px" className="my-6" />

              {/* Related News */}
              {relatedNews.length > 0 && (
                <div className="bg-white border border-gray-200 p-6">
                  <h3 className="font-['Oswald'] text-xl font-bold uppercase mb-4">
                    Weitere News
                  </h3>
                  <div className="divide-y">
                    {relatedNews.map((news) => (
                      <NewsCardCompact key={news.id} article={news} />
                    ))}
                  </div>
                </div>
              )}

              {/* Ad after related */}
              <AdSlot slotKey="article_after_related" minHeight="90px" className="mt-6" />
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
