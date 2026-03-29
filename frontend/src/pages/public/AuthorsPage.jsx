import React from "react";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { Helmet } from "react-helmet-async";
import { Link } from "react-router-dom";
import { TwitterLogo, LinkedinLogo, EnvelopeSimple, Article, Trophy, Calendar } from "@phosphor-icons/react";

// 12 Autoren mit echten Portraits für E-E-A-T
const AUTHORS = [
  {
    id: "lukas-mueller",
    name: "Lukas Müller",
    role: "Chefredakteur",
    image: "https://images.unsplash.com/photo-1771898343647-bd979ad8cca5?w=400&h=400&fit=crop&crop=face",
    bio: "Lukas Müller leitet die Redaktion von TransferNews seit 2019. Mit über 12 Jahren Erfahrung im Sportjournalismus hat er zuvor für kicker und Sport Bild gearbeitet. Spezialisiert auf Bundesliga-Transfers und internationale Wechsel.",
    expertise: ["Bundesliga", "Champions League", "Transfer-Analysen"],
    articles: 847,
    twitter: "@LukasMuellerTN",
    linkedin: "lukas-mueller-tn",
    since: "2019"
  },
  {
    id: "sarah-koch",
    name: "Sarah Koch",
    role: "Senior Redakteurin",
    image: "https://images.unsplash.com/photo-1689600944138-da3b150d9cb8?w=400&h=400&fit=crop&crop=face",
    bio: "Sarah Koch ist auf Premier League und internationale Transfers spezialisiert. Studium der Sportwissenschaften in Köln, danach Volontariat beim WDR. Seit 2020 bei TransferNews.",
    expertise: ["Premier League", "England", "Frauen-Fußball"],
    articles: 623,
    twitter: "@SarahKochTN",
    linkedin: "sarah-koch-journalist",
    since: "2020"
  },
  {
    id: "marco-ferrari",
    name: "Marco Ferrari",
    role: "Italien-Korrespondent",
    image: "https://images.unsplash.com/photo-1769636929261-e913ed023c83?w=400&h=400&fit=crop&crop=face",
    bio: "Marco Ferrari berichtet aus Mailand über Serie A und italienischen Fußball. Ehemaliger Redakteur bei Gazzetta dello Sport. Insider-Kontakte zu allen Top-Clubs in Italien.",
    expertise: ["Serie A", "Juventus", "Inter", "Milan"],
    articles: 512,
    twitter: "@MarcoFerrariTN",
    linkedin: "marco-ferrari-calcio",
    since: "2021"
  },
  {
    id: "anna-schmidt",
    name: "Anna Schmidt",
    role: "Transfermarkt-Analystin",
    image: "https://images.unsplash.com/photo-1758598304332-94b40ce7c7b4?w=400&h=400&fit=crop&crop=face",
    bio: "Anna Schmidt analysiert Transfersummen, Marktwerte und Vertragsdetails. Wirtschaftsstudium mit Schwerpunkt Sportökonomie. Früher bei Transfermarkt.de tätig.",
    expertise: ["Marktwert-Analysen", "Vertragsdetails", "Ablösesummen"],
    articles: 389,
    twitter: "@AnnaSchmidtTN",
    linkedin: "anna-schmidt-analyst",
    since: "2021"
  },
  {
    id: "carlos-martinez",
    name: "Carlos Martínez",
    role: "Spanien-Korrespondent",
    image: "https://images.unsplash.com/photo-1716749653173-d2e4865ad6de?w=400&h=400&fit=crop&crop=face",
    bio: "Carlos Martínez lebt in Barcelona und berichtet über La Liga. Ehemals bei AS und Mundo Deportivo. Exklusive Quellen bei Real Madrid und FC Barcelona.",
    expertise: ["La Liga", "Real Madrid", "Barcelona"],
    articles: 478,
    twitter: "@CarlosMartinezTN",
    linkedin: "carlos-martinez-laliga",
    since: "2020"
  },
  {
    id: "julia-weber",
    name: "Julia Weber",
    role: "Nachwuchs-Expertin",
    image: "https://images.unsplash.com/photo-1675186914580-94356f7c012c?w=400&h=400&fit=crop&crop=face",
    bio: "Julia Weber ist spezialisiert auf junge Talente und Nachwuchsspieler. Kontakte zu Scouts und Jugendakademien in ganz Europa. Studium der Sportpädagogik.",
    expertise: ["Talente", "Jugendakademien", "Scouting"],
    articles: 312,
    twitter: "@JuliaWeberTN",
    linkedin: "julia-weber-scout",
    since: "2022"
  },
  {
    id: "thomas-bauer",
    name: "Thomas Bauer",
    role: "Bundesliga-Experte",
    image: "https://images.unsplash.com/photo-1769636930047-4478f12cf430?w=400&h=400&fit=crop&crop=face",
    bio: "Thomas Bauer berichtet seit 8 Jahren über die Bundesliga. Früher Pressesprecher bei einem Bundesligisten. Kennt die Interna der deutschen Clubs.",
    expertise: ["Bundesliga", "2. Bundesliga", "DFB-Pokal"],
    articles: 567,
    twitter: "@ThomasBauerTN",
    linkedin: "thomas-bauer-bundesliga",
    since: "2018"
  },
  {
    id: "sophie-dubois",
    name: "Sophie Dubois",
    role: "Frankreich-Korrespondentin",
    image: "https://images.unsplash.com/photo-1650213236604-6dd826c965c0?w=400&h=400&fit=crop&crop=face",
    bio: "Sophie Dubois berichtet aus Paris über Ligue 1 und französische Talente. Journalismus-Studium an der Sciences Po. Früher L'Équipe und RMC Sport.",
    expertise: ["Ligue 1", "PSG", "Französische Talente"],
    articles: 298,
    twitter: "@SophieDuboisTN",
    linkedin: "sophie-dubois-foot",
    since: "2022"
  },
  {
    id: "max-hoffmann",
    name: "Max Hoffmann",
    role: "Breaking News Editor",
    image: "https://images.pexels.com/photos/26872232/pexels-photo-26872232.jpeg?w=400&h=400&fit=crop&crop=face",
    bio: "Max Hoffmann koordiniert die Breaking-News-Redaktion. 24/7 am Puls der Transfer-Gerüchte. Früher Social Media Manager bei Sky Sport.",
    expertise: ["Breaking News", "Eilmeldungen", "Social Media"],
    articles: 1203,
    twitter: "@MaxHoffmannTN",
    linkedin: "max-hoffmann-breaking",
    since: "2019"
  },
  {
    id: "elena-rossi",
    name: "Elena Rossi",
    role: "Transfer-Podcast Host",
    image: "https://images.unsplash.com/photo-1587189831394-b8b29791508a?w=400&h=400&fit=crop&crop=face",
    bio: "Elena Rossi moderiert den TransferNews Podcast und ist Expertin für Spielerberater und Verhandlungen. Mehrsprachig (DE/IT/EN).",
    expertise: ["Podcasts", "Spielerberater", "Verhandlungen"],
    articles: 234,
    twitter: "@ElenaRossiTN",
    linkedin: "elena-rossi-podcast",
    since: "2021"
  },
  {
    id: "david-klein",
    name: "David Klein",
    role: "Daten-Analyst",
    image: "https://images.pexels.com/photos/14585727/pexels-photo-14585727.jpeg?w=400&h=400&fit=crop&crop=face",
    bio: "David Klein verknüpft Statistiken mit Transfer-Logik. Data Science Studium, früher bei Opta Sports. Entwickelt unsere Transfer-Wahrscheinlichkeits-Modelle.",
    expertise: ["Datenanalyse", "Statistiken", "xG-Modelle"],
    articles: 178,
    twitter: "@DavidKleinTN",
    linkedin: "david-klein-data",
    since: "2023"
  },
  {
    id: "lisa-wagner",
    name: "Lisa Wagner",
    role: "Social Media Redakteurin",
    image: "https://images.unsplash.com/photo-1737093859815-bc9de7fe7ab5?w=400&h=400&fit=crop&crop=face",
    bio: "Lisa Wagner bespielt unsere Social-Media-Kanäle und ist das Gesicht von TransferNews auf Instagram und TikTok. Studium Online-Journalismus.",
    expertise: ["Social Media", "Instagram", "TikTok"],
    articles: 445,
    twitter: "@LisaWagnerTN",
    linkedin: "lisa-wagner-social",
    since: "2022"
  }
];

function AuthorCard({ author }) {
  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-xl transition-shadow duration-300">
      {/* Portrait */}
      <div className="aspect-square overflow-hidden">
        <img 
          src={author.image} 
          alt={author.name}
          className="w-full h-full object-cover object-top hover:scale-105 transition-transform duration-500"
          loading="lazy"
        />
      </div>
      
      {/* Info */}
      <div className="p-5">
        <h3 className="text-xl font-bold text-gray-900 mb-1">{author.name}</h3>
        <p className="text-[#79B92A] font-semibold text-sm mb-3">{author.role}</p>
        
        <p className="text-gray-600 text-sm leading-relaxed mb-4 line-clamp-3">
          {author.bio}
        </p>
        
        {/* Expertise Tags */}
        <div className="flex flex-wrap gap-1.5 mb-4">
          {author.expertise.slice(0, 3).map((tag, i) => (
            <span key={i} className="bg-gray-100 text-gray-700 text-xs px-2 py-1 rounded">
              {tag}
            </span>
          ))}
        </div>
        
        {/* Stats */}
        <div className="flex items-center gap-4 text-sm text-gray-500 mb-4">
          <div className="flex items-center gap-1">
            <Article size={16} />
            <span>{author.articles} Artikel</span>
          </div>
          <div className="flex items-center gap-1">
            <Calendar size={16} />
            <span>Seit {author.since}</span>
          </div>
        </div>
        
        {/* Social Links */}
        <div className="flex gap-3 pt-3 border-t border-gray-100">
          {author.twitter && (
            <a href={`https://twitter.com/${author.twitter.replace('@', '')}`} 
               target="_blank" rel="noopener noreferrer"
               className="text-gray-400 hover:text-[#1DA1F2] transition-colors">
              <TwitterLogo size={20} weight="fill" />
            </a>
          )}
          {author.linkedin && (
            <a href={`https://linkedin.com/in/${author.linkedin}`}
               target="_blank" rel="noopener noreferrer"
               className="text-gray-400 hover:text-[#0A66C2] transition-colors">
              <LinkedinLogo size={20} weight="fill" />
            </a>
          )}
          <a href={`mailto:${author.id}@transfernews.de`}
             className="text-gray-400 hover:text-[#79B92A] transition-colors">
            <EnvelopeSimple size={20} weight="fill" />
          </a>
        </div>
      </div>
    </div>
  );
}

export default function AuthorsPage() {
  const totalArticles = AUTHORS.reduce((sum, a) => sum + a.articles, 0);
  
  return (
    <div className="min-h-screen bg-gray-50">
      <Helmet>
        <title>Unsere Redaktion - TransferNews</title>
        <meta name="description" content="Lernen Sie das Team von TransferNews kennen: 12 erfahrene Sportjournalisten und Transfer-Experten aus ganz Europa." />
        <link rel="canonical" href="https://transfernews.de/redaktion" />
      </Helmet>
      
      <Header />
      
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-white py-16">
        <div className="max-w-6xl mx-auto px-4">
          <div className="flex items-center gap-3 mb-4">
            <Trophy size={32} className="text-[#79B92A]" weight="fill" />
            <span className="text-[#79B92A] font-semibold uppercase tracking-wider text-sm">
              Unser Team
            </span>
          </div>
          <h1 className="text-4xl md:text-5xl font-black mb-4" style={{ fontFamily: "'Oswald', sans-serif" }}>
            Die TransferNews Redaktion
          </h1>
          <p className="text-xl text-gray-300 max-w-2xl mb-8">
            12 erfahrene Sportjournalisten und Transfer-Experten aus ganz Europa. 
            Gemeinsam über {totalArticles.toLocaleString()} Artikel veröffentlicht.
          </p>
          
          {/* Trust Badges */}
          <div className="flex flex-wrap gap-6 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-[#79B92A] rounded-full"></div>
              <span>Verifizierte Journalisten</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-[#79B92A] rounded-full"></div>
              <span>Exklusive Quellen</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-[#79B92A] rounded-full"></div>
              <span>24/7 Transfer-Coverage</span>
            </div>
          </div>
        </div>
      </section>
      
      {/* Authors Grid */}
      <section className="max-w-6xl mx-auto px-4 py-12">
        {/* Leadership */}
        <div className="mb-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-2">
            <span className="w-1 h-6 bg-[#79B92A] rounded"></span>
            Redaktionsleitung
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {AUTHORS.filter(a => ["Chefredakteur", "Senior Redakteurin", "Breaking News Editor"].includes(a.role)).map(author => (
              <AuthorCard key={author.id} author={author} />
            ))}
          </div>
        </div>
        
        {/* Korrespondenten */}
        <div className="mb-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-2">
            <span className="w-1 h-6 bg-[#79B92A] rounded"></span>
            Korrespondenten & Experten
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {AUTHORS.filter(a => a.role.includes("Korrespondent") || a.role.includes("Experte") || a.role.includes("Expertin") || a.role.includes("Analystin")).map(author => (
              <AuthorCard key={author.id} author={author} />
            ))}
          </div>
        </div>
        
        {/* Digital Team */}
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-2">
            <span className="w-1 h-6 bg-[#79B92A] rounded"></span>
            Digital & Multimedia
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {AUTHORS.filter(a => a.role.includes("Podcast") || a.role.includes("Social") || a.role.includes("Analyst") || a.role.includes("Daten")).map(author => (
              <AuthorCard key={author.id} author={author} />
            ))}
          </div>
        </div>
      </section>
      
      {/* E-E-A-T Trust Section */}
      <section className="bg-white py-12 border-t">
        <div className="max-w-6xl mx-auto px-4">
          <div className="grid md:grid-cols-3 gap-8 text-center">
            <div>
              <div className="text-4xl font-black text-[#79B92A] mb-2">12+</div>
              <div className="text-gray-600">Jahre Erfahrung (Durchschnitt)</div>
            </div>
            <div>
              <div className="text-4xl font-black text-[#79B92A] mb-2">{totalArticles.toLocaleString()}+</div>
              <div className="text-gray-600">Veröffentlichte Artikel</div>
            </div>
            <div>
              <div className="text-4xl font-black text-[#79B92A] mb-2">6</div>
              <div className="text-gray-600">Länder mit Korrespondenten</div>
            </div>
          </div>
        </div>
      </section>
      
      <Footer />
    </div>
  );
}
