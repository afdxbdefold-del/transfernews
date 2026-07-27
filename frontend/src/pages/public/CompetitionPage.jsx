import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { Trophy, ArrowRight, Clock, TrendingUp, CheckCircle } from 'lucide-react';
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import PageLayout from "@/components/PageLayout";

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

export default function CompetitionPage() {
  const { slug } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchCompetitionData();
  }, [slug]);

  const fetchCompetitionData = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/api/wettbewerb/${slug}`);
      if (!response.ok) {
        throw new Error('Wettbewerb nicht gefunden');
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
          <h1 className="text-2xl font-bold text-gray-800 mb-2">Wettbewerb nicht gefunden</h1>
          <p className="text-gray-600">{error}</p>
          <Link to="/" className="text-[#79B92A] hover:underline mt-4 inline-block">
            Zurück zur Startseite
          </Link>
        </div>
      </div>
    );
  }

  const { competition, all_news, breaking_news, rumours, confirmed_transfers, seo } = data;

  return (
    <PageLayout>
      <Helmet>
        <title>{seo?.title || `${competition.name} Transfer-News`}</title>
        <meta name="description" content={seo?.description} />
        <meta property="og:title" content={seo?.title} />
        <meta property="og:description" content={seo?.description} />
        <link rel="canonical" href={`https://transfernews.de/wettbewerb/${slug}`} />
      </Helmet>

      <CollectionPageSchema 
        data={{
          name: seo?.h1,
          description: seo?.description,
          url: `https://transfernews.de/wettbewerb/${slug}`
        }}
      />

      <Header />

      <main className="flex-1 py-3 px-3" data-testid="competition-page">
        {/* Hero Section */}
        <div className="bg-gradient-to-r from-gray-900 to-gray-800 text-white py-12">
          <div className="container mx-auto px-4">
            <div className="flex items-center gap-3 mb-4">
              <Trophy className="w-8 h-8 text-[#79B92A]" />
              <span className="text-gray-400">{competition.country}</span>
            </div>
            <h1 className="text-3xl md:text-4xl font-bold mb-4">{seo?.h1}</h1>
            <p className="text-gray-300 max-w-2xl">{seo?.description}</p>
            <div className="mt-6 flex gap-4 text-sm">
              <span className="bg-white/10 px-3 py-1 rounded-full">
                {data.article_count} Artikel
              </span>
              <span className="bg-[#79B92A]/20 text-[#79B92A] px-3 py-1 rounded-full">
                {breaking_news?.length || 0} Breaking News
              </span>
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
                    Breaking News
                  </h2>
                  <div className="space-y-4">
                    {breaking_news.map((article, idx) => (
                      <Link 
                        key={article.id || idx}
                        to={`/news/${article.slug}`}
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
                      </Link>
                    ))}
                  </div>
                </section>
              )}

              {/* All News */}
              <section>
                <h2 className="text-xl font-bold mb-4">Alle Transfer-News</h2>
                <div className="space-y-4">
                  {all_news?.map((article, idx) => (
                    <Link 
                      key={article.id || idx}
                      to={`/news/${article.slug}`}
                      className="block bg-white p-4 rounded-lg shadow-sm hover:shadow-md transition-shadow"
                    >
                      <div className="flex items-start gap-4">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            {article.transfer_status && (
                              <span className={`text-xs px-2 py-0.5 rounded ${
                                article.transfer_status === 'OFFIZIELL' || article.transfer_status === 'BESTÄTIGT'
                                  ? 'bg-green-100 text-green-700'
                                  : 'bg-yellow-100 text-yellow-700'
                              }`}>
                                {article.transfer_status}
                              </span>
                            )}
                            {article.transfer_probability && (
                              <span className="text-xs text-gray-500">
                                {article.transfer_probability}% Wahrscheinlichkeit
                              </span>
                            )}
                          </div>
                          <h3 className="font-bold">{article.title}</h3>
                          <p className="text-gray-600 text-sm mt-2 line-clamp-2">{article.excerpt}</p>
                          <div className="flex items-center gap-4 mt-3 text-xs text-gray-500">
                            <span>{formatDate(article.published_at)}</span>
                            {article.reading_time_minutes && (
                              <span>{article.reading_time_minutes} Min. Lesezeit</span>
                            )}
                          </div>
                        </div>
                        <ArrowRight className="w-5 h-5 text-gray-400 flex-shrink-0" />
                      </div>
                    </Link>
                  ))}
                  
                  {(!all_news || all_news.length === 0) && (
                    <div className="text-center py-12 text-gray-500">
                      <p>Noch keine Transfer-News für diesen Wettbewerb.</p>
                    </div>
                  )}
                </div>
              </section>
            </div>

            {/* Sidebar */}
            <div className="space-y-6">
              {/* Confirmed Transfers */}
              {confirmed_transfers && confirmed_transfers.length > 0 && (
                <div className="bg-white rounded-lg shadow-sm p-4">
                  <h3 className="font-bold mb-4 flex items-center gap-2">
                    <CheckCircle className="w-5 h-5 text-green-500" />
                    Bestätigte Transfers
                  </h3>
                  <div className="space-y-3">
                    {confirmed_transfers.slice(0, 5).map((article, idx) => (
                      <Link 
                        key={article.id || idx}
                        to={`/news/${article.slug}`}
                        className="block text-sm hover:text-[#79B92A] transition-colors"
                      >
                        <span className="line-clamp-2">{article.title}</span>
                        <span className="text-xs text-gray-400 block mt-1">
                          {formatDate(article.published_at)}
                        </span>
                      </Link>
                    ))}
                  </div>
                </div>
              )}

              {/* Rumours */}
              {rumours && rumours.length > 0 && (
                <div className="bg-white rounded-lg shadow-sm p-4">
                  <h3 className="font-bold mb-4 flex items-center gap-2">
                    <TrendingUp className="w-5 h-5 text-yellow-500" />
                    Aktuelle Gerüchte
                  </h3>
                  <div className="space-y-3">
                    {rumours.slice(0, 5).map((article, idx) => (
                      <Link 
                        key={article.id || idx}
                        to={`/news/${article.slug}`}
                        className="block text-sm hover:text-[#79B92A] transition-colors"
                      >
                        <span className="line-clamp-2">{article.title}</span>
                        <span className="text-xs text-gray-400 block mt-1">
                          {formatDate(article.published_at)}
                        </span>
                      </Link>
                    ))}
                  </div>
                </div>
              )}

              {/* Other Competitions */}
              <div className="bg-white rounded-lg shadow-sm p-4">
                <h3 className="font-bold mb-4">Andere Wettbewerbe</h3>
                <div className="space-y-2">
                  {['bundesliga', 'premier-league', 'la-liga', 'serie-a', 'ligue-1', 'champions-league']
                    .filter(c => c !== slug)
                    .map(compSlug => (
                      <Link 
                        key={compSlug}
                        to={`/wettbewerb/${compSlug}`}
                        className="block text-sm py-2 px-3 rounded hover:bg-gray-100 transition-colors capitalize"
                      >
                        {compSlug.replace('-', ' ')}
                      </Link>
                    ))
                  }
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      <Footer />
    </PageLayout>
  );
}
