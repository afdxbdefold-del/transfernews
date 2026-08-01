import PageLayout from "@/components/PageLayout";
import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { Tag, ArrowRight, Clock, TrendingUp, CheckCircle, Bookmark } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Schema.org CollectionPage
function CollectionPageSchema({ data }) {
  if (!data) return null;
  
  const schema = {
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    "name": data.name,
    "description": data.description,
    "url": data.url
  };

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
    />
  );
}

// Theme display names and icons
const THEME_CONFIG = {
  'abloesefreie-transfers': { icon: '🆓', color: 'green' },
  'deadline-day': { icon: '⏰', color: 'red' },
  'sommertransfers': { icon: '☀️', color: 'yellow' },
  'wintertransfers': { icon: '❄️', color: 'blue' },
  'rekordtransfers': { icon: '💰', color: 'purple' },
  'leihen': { icon: '🔄', color: 'orange' },
  'junge-talente': { icon: '⭐', color: 'cyan' }
};

export default function ThemePage() {
  const { slug } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchThemeData();
  }, [slug]);

  const fetchThemeData = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/api/thema/${slug}`);
      if (!response.ok) {
        throw new Error('Thema nicht gefunden');
      }
      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    return new Date(dateString).toLocaleDateString('de-DE', {
      day: 'numeric',
      month: 'short',
      year: 'numeric'
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-4 border-[#79B92A] border-t-transparent rounded-full"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-800 mb-2">Thema nicht gefunden</h1>
          <p className="text-gray-600">{error}</p>
          <Link to="/" className="text-[#79B92A] hover:underline mt-4 inline-block">
            Zurück zur Startseite
          </Link>
        </div>
      </div>
    );
  }

  const { theme, all_news, breaking_news, seo } = data;
  const config = THEME_CONFIG[slug] || { icon: '📰', color: 'gray' };

  return (
    <>
      <Helmet>
        <title>{seo?.title || theme.name}</title>
        <meta name="description" content={seo?.description} />
        <meta property="og:title" content={seo?.title} />
        <meta property="og:description" content={seo?.description} />
        <link rel="canonical" href={`https://transfernews.de/thema/${slug}`} />
      </Helmet>

      <CollectionPageSchema 
        data={{
          name: theme.name,
          description: theme.description,
          url: `https://transfernews.de/thema/${slug}`
        }}
      />

      <div className="min-h-screen bg-gray-50" data-testid="theme-page">
        {/* Hero Section */}
        <div className="bg-gradient-to-r from-gray-900 to-gray-800 text-white py-12">
          <div className="container mx-auto px-4">
            <div className="flex items-center gap-3 mb-4">
              <span className="text-3xl">{config.icon}</span>
              <Tag className="w-6 h-6 text-[#79B92A]" />
            </div>
            <h1 className="text-3xl md:text-4xl font-bold mb-4">{seo?.h1 || theme.name}</h1>
            <p className="text-gray-300 max-w-2xl">{theme.description}</p>
            <div className="mt-6 flex gap-4 text-sm">
              <span className="bg-white/10 px-3 py-1 rounded-full">
                {data.article_count} Artikel
              </span>
              {breaking_news?.length > 0 && (
                <span className="bg-red-500/20 text-red-300 px-3 py-1 rounded-full">
                  {breaking_news.length} Breaking
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="container mx-auto px-4 py-8">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Main Content */}
            <div className="lg:col-span-2 space-y-8">
              {/* Breaking News */}
              {breaking_news && breaking_news.length > 0 && (
                <section>
                  <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                    <TrendingUp className="w-5 h-5 text-red-500" />
                    Aktuelle Breaking News
                  </h2>
                  <div className="space-y-4">
                    {breaking_news.map((article, idx) => (
                      <a 
                        key={article.id || idx}
                        href={`/news/${article.slug}`}
                        className="block bg-white border-l-4 border-red-500 p-4 rounded-r-lg shadow-sm hover:shadow-md transition-shadow"
                      >
                        <span className="text-xs text-red-500 font-semibold uppercase">Breaking</span>
                        <h3 className="font-bold text-lg mt-1">{article.title}</h3>
                        <p className="text-gray-600 text-sm mt-2 line-clamp-2">{article.excerpt}</p>
                        <div className="flex items-center gap-4 mt-3 text-xs text-gray-500">
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {formatDate(article.published_at)}
                          </span>
                        </div>
                      </a>
                    ))}
                  </div>
                </section>
              )}

              {/* All News */}
              <section>
                <h2 className="text-xl font-bold mb-4">Alle Artikel zu {theme.name}</h2>
                <div className="space-y-4">
                  {all_news?.map((article, idx) => (
                    <a 
                      key={article.id || idx}
                      href={`/news/${article.slug}`}
                      className="block bg-white p-4 rounded-lg shadow-sm hover:shadow-md transition-shadow"
                    >
                      <div className="flex items-start gap-4">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            {article.is_breaking && (
                              <span className="text-xs px-2 py-0.5 rounded bg-red-100 text-red-700">
                                Breaking
                              </span>
                            )}
                            {article.transfer_status && (
                              <span className={`text-xs px-2 py-0.5 rounded ${
                                article.transfer_status === 'OFFIZIELL' || article.transfer_status === 'BESTÄTIGT'
                                  ? 'bg-green-100 text-green-700'
                                  : 'bg-yellow-100 text-yellow-700'
                              }`}>
                                {article.transfer_status}
                              </span>
                            )}
                          </div>
                          <h3 className="font-bold">{article.title}</h3>
                          <p className="text-gray-600 text-sm mt-2 line-clamp-2">{article.excerpt}</p>
                          <div className="flex items-center gap-4 mt-3 text-xs text-gray-500">
                            <span>{formatDate(article.published_at)}</span>
                            {article.author_name && (
                              <span>von {article.author_name}</span>
                            )}
                          </div>
                        </div>
                        <ArrowRight className="w-5 h-5 text-gray-400 flex-shrink-0" />
                      </div>
                    </a>
                  ))}
                  
                  {(!all_news || all_news.length === 0) && (
                    <div className="text-center py-12 text-gray-500">
                      <p>Noch keine Artikel zu diesem Thema.</p>
                    </div>
                  )}
                </div>
              </section>
            </div>

            {/* Sidebar */}
            <div className="space-y-6">
              {/* About Theme */}
              <div className="bg-white rounded-lg shadow-sm p-4">
                <h3 className="font-bold mb-4 flex items-center gap-2">
                  <Bookmark className="w-5 h-5 text-[#79B92A]" />
                  Über dieses Thema
                </h3>
                <p className="text-sm text-gray-600">{theme.description}</p>
                <div className="mt-4 text-xs text-gray-400">
                  Keywords: {theme.keywords?.join(', ')}
                </div>
              </div>

              {/* Other Themes */}
              <div className="bg-white rounded-lg shadow-sm p-4">
                <h3 className="font-bold mb-4">Weitere Themen</h3>
                <div className="space-y-2">
                  {Object.entries(THEME_CONFIG)
                    .filter(([s]) => s !== slug)
                    .map(([themeSlug, cfg]) => (
                      <Link 
                        key={themeSlug}
                        to={`/thema/${themeSlug}`}
                        className="flex items-center gap-2 text-sm py-2 px-3 rounded hover:bg-gray-100 transition-colors"
                      >
                        <span>{cfg.icon}</span>
                        <span className="capitalize">{themeSlug.replace(/-/g, ' ')}</span>
                      </Link>
                    ))
                  }
                </div>
              </div>

              {/* Competitions Link */}
              <div className="bg-white rounded-lg shadow-sm p-4">
                <h3 className="font-bold mb-4">Nach Liga filtern</h3>
                <div className="space-y-2">
                  {['bundesliga', 'premier-league', 'la-liga', 'serie-a'].map(compSlug => (
                    <Link 
                      key={compSlug}
                      to={`/wettbewerb/${compSlug}`}
                      className="block text-sm py-2 px-3 rounded hover:bg-gray-100 transition-colors capitalize"
                    >
                      {compSlug.replace('-', ' ')}
                    </Link>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
