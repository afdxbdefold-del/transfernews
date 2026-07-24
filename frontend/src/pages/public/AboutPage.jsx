import React from "react";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { Helmet } from "react-helmet-async";
import { Link } from "react-router-dom";
import { 
  Target, ShieldCheck, Users, Lightning, Eye, CheckCircle, 
  Newspaper, Globe, Clock, Certificate, TrendUp, HandShake
} from "@phosphor-icons/react";

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Helmet>
        <title>Über Uns - TransferNews</title>
        <meta name="description" content="TransferNews ist Deutschlands führendes Transfer-Nachrichtenportal. Erfahren Sie mehr über unsere Mission, Werte und wie wir arbeiten." />
        <link rel="canonical" href="https://transfernews.de/ueber-uns" />
      </Helmet>
      
      <Header />
      
      {/* Hero */}
      <section className="bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-white py-20">
        <div className="max-w-[1000px] mx-auto px-4 text-center">
          <h1 className="text-4xl md:text-5xl font-black mb-6" style={{ fontFamily: "'Oswald', sans-serif" }}>
            Über TransferNews
          </h1>
          <p className="text-xl text-gray-300 max-w-3xl mx-auto">
            Deutschlands führendes Transfer-Nachrichtenportal. Schnell, zuverlässig, verifiziert.
          </p>
        </div>
      </section>
      
      {/* Mission */}
      <section className="max-w-[1000px] mx-auto px-4 py-16">
        <div className="grid md:grid-cols-2 gap-12 items-center">
          <div>
            <div className="flex items-center gap-2 mb-4">
              <Target size={24} className="text-[#79B92A]" weight="fill" />
              <span className="text-[#79B92A] font-semibold uppercase tracking-wider text-sm">Unsere Mission</span>
            </div>
            <h2 className="text-3xl font-bold text-gray-900 mb-6">
              Die schnellsten und zuverlässigsten Transfer-News
            </h2>
            <p className="text-gray-600 leading-relaxed mb-4">
              TransferNews wurde 2019 mit einer klaren Vision gegründet: Fußballfans verdienen 
              schnelle, akkurate und gut recherchierte Transfer-Nachrichten – ohne Clickbait 
              und ohne unbelegte Gerüchte.
            </p>
            <p className="text-gray-600 leading-relaxed">
              Heute erreichen wir monatlich über 2 Millionen Leser und sind eine der vertrauenswürdigsten 
              Quellen für Transfer-News im deutschsprachigen Raum.
            </p>
          </div>
          <div className="bg-white rounded-xl shadow-lg p-8">
            <div className="grid grid-cols-2 gap-6 text-center">
              <div>
                <div className="text-4xl font-black text-[#79B92A]">2M+</div>
                <div className="text-gray-500 text-sm">Monatliche Leser</div>
              </div>
              <div>
                <div className="text-4xl font-black text-[#79B92A]">12</div>
                <div className="text-gray-500 text-sm">Redakteure</div>
              </div>
              <div>
                <div className="text-4xl font-black text-[#79B92A]">6</div>
                <div className="text-gray-500 text-sm">Länder-Korrespondenten</div>
              </div>
              <div>
                <div className="text-4xl font-black text-[#79B92A]">24/7</div>
                <div className="text-gray-500 text-sm">Redaktion aktiv</div>
              </div>
            </div>
          </div>
        </div>
      </section>
      
      {/* Werte */}
      <section className="bg-white py-16">
        <div className="max-w-[1000px] mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Unsere Werte</h2>
            <p className="text-gray-600 max-w-2xl mx-auto">
              Diese Prinzipien leiten unsere tägliche Arbeit und garantieren die Qualität unserer Berichterstattung.
            </p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center p-6">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <ShieldCheck size={32} className="text-[#79B92A]" weight="fill" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">Zuverlässigkeit</h3>
              <p className="text-gray-600 text-sm">
                Wir veröffentlichen nur Informationen aus verifizierten Quellen. 
                Jede Meldung wird von mindestens einem Redakteur geprüft.
              </p>
            </div>
            
            <div className="text-center p-6">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Lightning size={32} className="text-[#79B92A]" weight="fill" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">Geschwindigkeit</h3>
              <p className="text-gray-600 text-sm">
                Breaking News in unter 2 Minuten. Unser 24/7-Team garantiert, 
                dass Sie keine wichtige Meldung verpassen.
              </p>
            </div>
            
            <div className="text-center p-6">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Eye size={32} className="text-[#79B92A]" weight="fill" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">Transparenz</h3>
              <p className="text-gray-600 text-sm">
                Wir nennen unsere Quellen und kennzeichnen den Sicherheitsgrad 
                jeder Meldung. Keine versteckten Agenden.
              </p>
            </div>
          </div>
        </div>
      </section>
      
      {/* So arbeiten wir */}
      <section className="max-w-[1000px] mx-auto px-4 py-16">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">So arbeiten wir</h2>
          <p className="text-gray-600 max-w-2xl mx-auto">
            Unser redaktioneller Prozess garantiert höchste Qualität bei maximaler Geschwindigkeit.
          </p>
        </div>
        
        <div className="grid md:grid-cols-4 gap-6">
          <div className="bg-white rounded-lg p-6 shadow-sm border-t-4 border-[#79B92A]">
            <div className="text-3xl font-black text-[#79B92A] mb-2">01</div>
            <h3 className="font-bold text-gray-900 mb-2">Quellenmonitoring</h3>
            <p className="text-gray-600 text-sm">
              19 internationale Quellen werden rund um die Uhr überwacht – von Sky Sports bis Gazzetta.
            </p>
          </div>
          
          <div className="bg-white rounded-lg p-6 shadow-sm border-t-4 border-[#79B92A]">
            <div className="text-3xl font-black text-[#79B92A] mb-2">02</div>
            <h3 className="font-bold text-gray-900 mb-2">Verifizierung</h3>
            <p className="text-gray-600 text-sm">
              Jede Meldung wird auf Glaubwürdigkeit geprüft. Wir nutzen ein Tier-System für Quellen.
            </p>
          </div>
          
          <div className="bg-white rounded-lg p-6 shadow-sm border-t-4 border-[#79B92A]">
            <div className="text-3xl font-black text-[#79B92A] mb-2">03</div>
            <h3 className="font-bold text-gray-900 mb-2">Anreicherung</h3>
            <p className="text-gray-600 text-sm">
              Wir fügen Kontext hinzu: Marktwerte, Vertragsdaten, Karriere-Historie aus Transfermarkt.
            </p>
          </div>
          
          <div className="bg-white rounded-lg p-6 shadow-sm border-t-4 border-[#79B92A]">
            <div className="text-3xl font-black text-[#79B92A] mb-2">04</div>
            <h3 className="font-bold text-gray-900 mb-2">Publikation</h3>
            <p className="text-gray-600 text-sm">
              Fertige Artikel werden mit Autorennennung, Quellen-Badge und Confidence-Score veröffentlicht.
            </p>
          </div>
        </div>
      </section>
      
      {/* Quellen-Tiers */}
      <section className="bg-gray-900 text-white py-16">
        <div className="max-w-[1000px] mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-4">Unser Quellen-System</h2>
            <p className="text-gray-400 max-w-2xl mx-auto">
              Nicht alle Quellen sind gleich. Wir kategorisieren sie nach Zuverlässigkeit.
            </p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-6">
            <div className="bg-gray-800 rounded-lg p-6">
              <div className="flex items-center gap-2 mb-4">
                <span className="bg-green-500 text-white text-xs font-bold px-2 py-1 rounded">TIER 1</span>
                <span className="text-green-400 font-semibold">Höchste Zuverlässigkeit</span>
              </div>
              <p className="text-gray-400 text-sm mb-4">
                Offizielle Club-Statements, etablierte Journalisten mit direkten Vereinskontakten.
              </p>
              <div className="text-xs text-gray-500">
                Sky Sports, L'Équipe, kicker, Fabrizio Romano
              </div>
            </div>
            
            <div className="bg-gray-800 rounded-lg p-6">
              <div className="flex items-center gap-2 mb-4">
                <span className="bg-yellow-500 text-white text-xs font-bold px-2 py-1 rounded">TIER 2</span>
                <span className="text-yellow-400 font-semibold">Gute Zuverlässigkeit</span>
              </div>
              <p className="text-gray-400 text-sm mb-4">
                Renommierte Sportmedien mit guter Track-Record bei Transfers.
              </p>
              <div className="text-xs text-gray-500">
                BBC Sport, Marca, Gazzetta, Goal.com
              </div>
            </div>
            
            <div className="bg-gray-800 rounded-lg p-6">
              <div className="flex items-center gap-2 mb-4">
                <span className="bg-orange-500 text-white text-xs font-bold px-2 py-1 rounded">TIER 3</span>
                <span className="text-orange-400 font-semibold">Gerüchte-Niveau</span>
              </div>
              <p className="text-gray-400 text-sm mb-4">
                Aggregatoren und kleinere Medien. Wir markieren diese explizit als "Gerücht".
              </p>
              <div className="text-xs text-gray-500">
                90min, CaughtOffside, TEAMtalk
              </div>
            </div>
          </div>
        </div>
      </section>
      
      {/* Team CTA */}
      <section className="max-w-5xl mx-auto px-4 py-16 text-center">
        <h2 className="text-3xl font-bold text-gray-900 mb-4">Lernen Sie unser Team kennen</h2>
        <p className="text-gray-600 mb-8 max-w-2xl mx-auto">
          12 erfahrene Sportjournalisten aus 6 Ländern arbeiten täglich daran, 
          Ihnen die besten Transfer-News zu liefern.
        </p>
        <Link 
          to="/redaktion"
          className="inline-flex items-center gap-2 bg-[#79B92A] hover:bg-[#6aa825] text-white font-bold px-8 py-4 rounded-lg transition-colors"
        >
          <Users size={20} weight="fill" />
          Zur Redaktion
        </Link>
      </section>
      
      {/* Trust Footer */}
      <section className="bg-gray-100 py-8">
        <div className="max-w-[1000px] mx-auto px-4">
          <div className="flex flex-wrap justify-center gap-8 text-sm text-gray-500">
            <div className="flex items-center gap-2">
              <CheckCircle size={18} className="text-[#79B92A]" weight="fill" />
              <span>Verifizierte Quellen</span>
            </div>
            <div className="flex items-center gap-2">
              <Certificate size={18} className="text-[#79B92A]" weight="fill" />
              <span>Ausgebildete Journalisten</span>
            </div>
            <div className="flex items-center gap-2">
              <Clock size={18} className="text-[#79B92A]" weight="fill" />
              <span>24/7 Redaktion</span>
            </div>
            <div className="flex items-center gap-2">
              <Globe size={18} className="text-[#79B92A]" weight="fill" />
              <span>6 Länder-Korrespondenten</span>
            </div>
          </div>
        </div>
      </section>
      
      <Footer />
    </div>
  );
}
