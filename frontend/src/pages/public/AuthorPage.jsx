import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { NewsCard } from "@/components/NewsCard";
import { TrendingWidget } from "@/components/TrendingWidget";
import { PersonSchema } from "@/components/SchemaMarkup";
import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { Badge } from "@/components/ui/badge";
import { User, Envelope, TwitterLogo, LinkedinLogo, ArrowLeft, Newspaper, PencilLine } from "@phosphor-icons/react";
import { Skeleton } from "@/components/ui/skeleton";
import { Helmet } from "react-helmet-async";
import api from "@/api";

export default function AuthorPage() {
  const { slug } = useParams();
  const [author, setAuthor] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAuthor = async () => {
      try {
        setLoading(true);
        const res = await api.get(`/public/authors/${slug}`);
        setAuthor(res.data);
      } catch (e) {
        console.error("Author load error:", e);
      } finally {
        setLoading(false);
      }
    };
    fetchAuthor();
  }, [slug]);

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col bg-gray-50">
        <Header />
        <main className="flex-1 py-8">
          <div className="max-w-[1280px] mx-auto px-4">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              <div className="lg:col-span-2 space-y-6">
                <Skeleton className="h-48 w-full" />
                <Skeleton className="h-8 w-3/4" />
                <Skeleton className="h-32 w-full" />
              </div>
              <div>
                <Skeleton className="h-64 w-full" />
              </div>
            </div>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  if (!author) {
    return (
      <div className="min-h-screen flex flex-col bg-gray-50">
        <Header />
        <main className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <h1 className="text-2xl font-bold mb-4">Autor nicht gefunden</h1>
            <Link to="/" className="text-[#79B92A] hover:underline">
              Zur Startseite
            </Link>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  // Schema.org Person data for author
  const personData = {
    name: author.name,
    url: `https://transfernews.de/autor/${slug}`,
    jobTitle: "Sportjournalist"
  };

  return (
    <div className="min-h-screen flex flex-col bg-gray-50" data-testid="author-page">
      <Helmet>
        <title>{`${author.name} - Autor | TransferNews.de`}</title>
        <meta name="description" content={author.bio || `Artikel von ${author.name} auf TransferNews.de`} />
        <meta name="robots" content="index, follow" />
        <link rel="canonical" href={`https://transfernews.de/autor/${slug}`} />
        
        {/* OpenGraph */}
        <meta property="og:title" content={`${author.name} - TransferNews.de`} />
        <meta property="og:description" content={author.bio || `Artikel von ${author.name}`} />
        <meta property="og:type" content="profile" />
        <meta property="og:url" content={`https://transfernews.de/autor/${slug}`} />
        {author.avatar_url && <meta property="og:image" content={author.avatar_url} />}
        
        {/* Twitter */}
        <meta name="twitter:card" content="summary" />
        <meta name="twitter:title" content={`${author.name} - TransferNews.de`} />
        {author.twitter_handle && <meta name="twitter:creator" content={`@${author.twitter_handle}`} />}
      </Helmet>
      
      {/* Schema.org Person JSON-LD */}
      <PersonSchema person={personData} />
      
      <Header />

      <main className="flex-1 py-8">
        <div className="max-w-[1280px] mx-auto px-4">
          {/* Back Link */}
          <Link 
            to="/" 
            className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-[#79B92A] mb-6"
          >
            <ArrowLeft size={16} />
            <span>Zurück zur Startseite</span>
          </Link>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Main Content */}
            <div className="lg:col-span-2">
              {/* Author Card */}
              <div className="bg-white border border-gray-200 p-6 mb-8">
                <div className="flex items-start gap-6">
                  {/* Avatar */}
                  <div className="w-24 h-24 bg-[#79B92A] rounded-full flex items-center justify-center shrink-0">
                    {author.avatar_url ? (
                      <img 
                        src={author.avatar_url} 
                        alt={author.name}
                        className="w-full h-full rounded-full object-cover"
                      />
                    ) : (
                      <User size={48} weight="bold" className="text-white" />
                    )}
                  </div>
                  
                  {/* Info */}
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h1 className="text-2xl font-bold text-gray-900">{author.name}</h1>
                      <Badge variant="outline" className="bg-[#79B92A]/10 text-[#79B92A] border-[#79B92A]">
                        <PencilLine size={12} weight="bold" className="mr-1" />
                        Autor
                      </Badge>
                    </div>
                    
                    {author.bio && (
                      <p className="text-gray-600 mb-4">{author.bio}</p>
                    )}
                    
                    {/* Expertise Tags */}
                    {author.expertise && author.expertise.length > 0 && (
                      <div className="flex flex-wrap gap-2 mb-4">
                        {author.expertise.map((exp) => (
                          <Badge key={exp} variant="secondary" className="bg-gray-100 text-gray-700">
                            {exp}
                          </Badge>
                        ))}
                      </div>
                    )}
                    
                    {/* Social Links */}
                    <div className="flex items-center gap-4">
                      {author.twitter_handle && (
                        <a 
                          href={`https://twitter.com/${author.twitter_handle}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-gray-400 hover:text-[#1DA1F2] transition-colors"
                          aria-label="Twitter"
                        >
                          <TwitterLogo size={20} weight="fill" />
                        </a>
                      )}
                      {author.linkedin_url && (
                        <a 
                          href={author.linkedin_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-gray-400 hover:text-[#0077B5] transition-colors"
                          aria-label="LinkedIn"
                        >
                          <LinkedinLogo size={20} weight="fill" />
                        </a>
                      )}
                      {author.email && (
                        <a 
                          href={`mailto:${author.email}`}
                          className="text-gray-400 hover:text-[#79B92A] transition-colors"
                          aria-label="Email"
                        >
                          <Envelope size={20} weight="fill" />
                        </a>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Articles */}
              <div>
                <div className="flex items-center gap-2 mb-4">
                  <Newspaper size={20} weight="bold" className="text-[#79B92A]" />
                  <h2 className="text-lg font-bold">
                    Artikel von {author.name}
                    <span className="text-gray-400 font-normal ml-2">({author.article_count})</span>
                  </h2>
                </div>

                {author.articles && author.articles.length > 0 ? (
                  <div className="space-y-4">
                    {author.articles.map((article) => (
                      <NewsCard key={article.id} article={article} />
                    ))}
                  </div>
                ) : (
                  <div className="bg-white border border-gray-200 p-8 text-center text-gray-500">
                    Noch keine Artikel veröffentlicht.
                  </div>
                )}
              </div>
            </div>

            {/* Sidebar */}
            <aside className="space-y-6">
              <TrendingWidget />
            </aside>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
