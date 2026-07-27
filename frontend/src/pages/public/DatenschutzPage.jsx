import PageLayout from "@/components/PageLayout";
import React from "react";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { Helmet } from "react-helmet-async";
import { Link } from "react-router-dom";
import { ShieldCheck, Cookie, Eye, Database, Lock, Globe, EnvelopeSimple, UserCircle } from "@phosphor-icons/react";

export default function DatenschutzPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Helmet>
        <title>Datenschutzerklärung - TransferNews</title>
        <meta name="description" content="Datenschutzerklärung von TransferNews.de - Informationen zum Schutz Ihrer persönlichen Daten gemäß DSGVO." />
        <link rel="canonical" href="https://transfernews.de/datenschutz" />
      </Helmet>
      
      <Header />
      
      <main className="max-w-4xl mx-auto px-4 py-12">
        <div className="bg-white rounded-lg shadow-sm p-8 md:p-12">
          {/* Header */}
          <div className="flex items-center gap-3 mb-8">
            <ShieldCheck size={32} className="text-[#79B92A]" weight="fill" />
            <h1 className="text-3xl font-black text-gray-900" style={{ fontFamily: "'Oswald', sans-serif" }}>
              Datenschutzerklärung
            </h1>
          </div>
          
          <p className="text-gray-600 mb-8">
            Der Schutz Ihrer persönlichen Daten ist uns ein besonderes Anliegen. Wir verarbeiten Ihre Daten 
            daher ausschließlich auf Grundlage der gesetzlichen Bestimmungen (DSGVO, TKG 2003).
          </p>
          
          {/* 1. Verantwortlicher */}
          <section className="mb-10">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <UserCircle size={20} className="text-[#79B92A]" />
              1. Verantwortlicher
            </h2>
            <div className="bg-gray-50 p-5 rounded-lg text-gray-700">
              <p className="font-semibold mb-2">TransferNews Media GmbH</p>
              <p>Musterstraße 123<br />80331 München<br />Deutschland</p>
              <p className="mt-3">
                E-Mail: <a href="mailto:datenschutz@transfernews.de" className="text-[#79B92A] hover:underline">datenschutz@transfernews.de</a>
              </p>
            </div>
          </section>
          
          {/* 2. Erhobene Daten */}
          <section className="mb-10">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <Database size={20} className="text-[#79B92A]" />
              2. Welche Daten wir erheben
            </h2>
            <p className="text-gray-600 mb-4">
              Beim Besuch unserer Website werden automatisch folgende Daten erhoben:
            </p>
            <ul className="list-disc list-inside text-gray-600 space-y-2 ml-4">
              <li>IP-Adresse (anonymisiert)</li>
              <li>Datum und Uhrzeit des Zugriffs</li>
              <li>Aufgerufene Seiten</li>
              <li>Browsertyp und -version</li>
              <li>Betriebssystem</li>
              <li>Referrer URL (zuvor besuchte Seite)</li>
            </ul>
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 mt-4">
              <p className="text-sm text-green-800 flex items-center gap-2">
                <Lock size={18} weight="fill" />
                Diese Daten werden nicht mit anderen Datenquellen zusammengeführt.
              </p>
            </div>
          </section>
          
          {/* 3. Cookies */}
          <section className="mb-10">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <Cookie size={20} className="text-[#79B92A]" />
              3. Cookies
            </h2>
            <p className="text-gray-600 mb-4">
              Unsere Website verwendet Cookies. Dabei handelt es sich um kleine Textdateien, die auf Ihrem 
              Endgerät gespeichert werden.
            </p>
            
            <h3 className="font-bold text-gray-800 mt-4 mb-2">Technisch notwendige Cookies</h3>
            <p className="text-gray-600 mb-4">
              Diese Cookies sind für den Betrieb der Website erforderlich und können nicht deaktiviert werden. 
              Sie speichern keine personenbezogenen Daten.
            </p>
            
            <h3 className="font-bold text-gray-800 mt-4 mb-2">Analyse-Cookies</h3>
            <p className="text-gray-600 mb-4">
              Mit Ihrer Einwilligung nutzen wir Analyse-Cookies, um die Nutzung unserer Website zu verstehen 
              und zu verbessern. Diese Cookies werden erst nach Ihrer Zustimmung gesetzt.
            </p>
            
            <div className="bg-gray-100 rounded-lg p-4">
              <p className="text-sm text-gray-600">
                <strong>Cookie-Einstellungen:</strong> Sie können Ihre Cookie-Präferenzen jederzeit in Ihren 
                Browsereinstellungen ändern oder alle Cookies löschen.
              </p>
            </div>
          </section>
          
          {/* 4. Rechtsgrundlage */}
          <section className="mb-10">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <Eye size={20} className="text-[#79B92A]" />
              4. Rechtsgrundlage der Verarbeitung
            </h2>
            <p className="text-gray-600 mb-4">
              Die Verarbeitung Ihrer Daten erfolgt auf folgenden Rechtsgrundlagen:
            </p>
            <ul className="space-y-3 text-gray-600">
              <li className="flex items-start gap-2">
                <span className="bg-[#79B92A] text-white text-xs font-bold px-2 py-0.5 rounded mt-0.5">Art. 6 Abs. 1a</span>
                <span>Einwilligung (z.B. bei Newsletter-Anmeldung)</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="bg-[#79B92A] text-white text-xs font-bold px-2 py-0.5 rounded mt-0.5">Art. 6 Abs. 1b</span>
                <span>Vertragserfüllung oder vorvertragliche Maßnahmen</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="bg-[#79B92A] text-white text-xs font-bold px-2 py-0.5 rounded mt-0.5">Art. 6 Abs. 1f</span>
                <span>Berechtigtes Interesse (z.B. Website-Sicherheit, Statistiken)</span>
              </li>
            </ul>
          </section>
          
          {/* 5. Ihre Rechte */}
          <section className="mb-10">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <Lock size={20} className="text-[#79B92A]" />
              5. Ihre Rechte
            </h2>
            <p className="text-gray-600 mb-4">
              Nach DSGVO stehen Ihnen folgende Rechte zu:
            </p>
            <div className="grid md:grid-cols-2 gap-4">
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-semibold text-gray-900 mb-1">Auskunftsrecht</h4>
                <p className="text-sm text-gray-600">Sie können Auskunft über Ihre bei uns gespeicherten Daten verlangen.</p>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-semibold text-gray-900 mb-1">Berichtigungsrecht</h4>
                <p className="text-sm text-gray-600">Sie können die Berichtigung unrichtiger Daten verlangen.</p>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-semibold text-gray-900 mb-1">Löschungsrecht</h4>
                <p className="text-sm text-gray-600">Sie können die Löschung Ihrer Daten verlangen ("Recht auf Vergessenwerden").</p>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-semibold text-gray-900 mb-1">Einschränkung</h4>
                <p className="text-sm text-gray-600">Sie können die Einschränkung der Verarbeitung verlangen.</p>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-semibold text-gray-900 mb-1">Datenübertragbarkeit</h4>
                <p className="text-sm text-gray-600">Sie können Ihre Daten in einem gängigen Format erhalten.</p>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-semibold text-gray-900 mb-1">Widerspruchsrecht</h4>
                <p className="text-sm text-gray-600">Sie können der Verarbeitung Ihrer Daten widersprechen.</p>
              </div>
            </div>
          </section>
          
          {/* 6. Drittanbieter */}
          <section className="mb-10">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <Globe size={20} className="text-[#79B92A]" />
              6. Drittanbieter-Dienste
            </h2>
            
            <h3 className="font-bold text-gray-800 mt-4 mb-2">Hosting</h3>
            <p className="text-gray-600 mb-4">
              Unsere Website wird auf Servern in Deutschland gehostet. Der Hosting-Anbieter verarbeitet 
              Daten in unserem Auftrag gemäß Art. 28 DSGVO.
            </p>
            
            <h3 className="font-bold text-gray-800 mt-4 mb-2">Bilder (Wikimedia Commons)</h3>
            <p className="text-gray-600 mb-4">
              Wir verwenden lizenzfreie Bilder von Wikimedia Commons. Beim Laden dieser Bilder kann 
              Ihre IP-Adresse an die Wikimedia Foundation übermittelt werden.
            </p>
            
            <h3 className="font-bold text-gray-800 mt-4 mb-2">Social Media Sharing</h3>
            <p className="text-gray-600 mb-4">
              Unsere Share-Buttons öffnen lediglich neue Fenster zu den jeweiligen Plattformen. 
              Es werden keine Daten automatisch an soziale Netzwerke übertragen.
            </p>
          </section>
          
          {/* 7. Datensicherheit */}
          <section className="mb-10">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <ShieldCheck size={20} className="text-[#79B92A]" />
              7. Datensicherheit
            </h2>
            <p className="text-gray-600 mb-4">
              Wir setzen technische und organisatorische Sicherheitsmaßnahmen ein, um Ihre Daten gegen 
              zufällige oder vorsätzliche Manipulationen, Verlust, Zerstörung oder unbefugten Zugriff zu schützen.
            </p>
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <p className="text-sm text-green-800">
                <strong>SSL-Verschlüsselung:</strong> Unsere Website nutzt aus Sicherheitsgründen eine 
                SSL-Verschlüsselung (HTTPS). Dadurch sind Daten, die Sie an uns übermitteln, vor dem 
                Zugriff Dritter geschützt.
              </p>
            </div>
          </section>
          
          {/* 8. Kontakt */}
          <section className="mb-10">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <EnvelopeSimple size={20} className="text-[#79B92A]" />
              8. Kontakt bei Datenschutzfragen
            </h2>
            <p className="text-gray-600 mb-4">
              Bei Fragen zur Erhebung, Verarbeitung oder Nutzung Ihrer personenbezogenen Daten, 
              bei Auskünften, Berichtigung, Sperrung oder Löschung von Daten wenden Sie sich bitte an:
            </p>
            <div className="bg-gray-50 p-5 rounded-lg">
              <p className="text-gray-700">
                <strong>Datenschutzbeauftragter</strong><br />
                TransferNews Media GmbH<br />
                E-Mail: <a href="mailto:datenschutz@transfernews.de" className="text-[#79B92A] hover:underline">datenschutz@transfernews.de</a>
              </p>
            </div>
          </section>
          
          {/* 9. Beschwerderecht */}
          <section className="mb-10">
            <h2 className="text-xl font-bold text-gray-900 mb-4">9. Beschwerderecht bei der Aufsichtsbehörde</h2>
            <p className="text-gray-600">
              Sie haben das Recht, sich bei einer Datenschutz-Aufsichtsbehörde über die Verarbeitung 
              Ihrer personenbezogenen Daten durch uns zu beschweren. Die für uns zuständige 
              Aufsichtsbehörde ist:
            </p>
            <div className="bg-gray-50 p-5 rounded-lg mt-4 text-gray-600 text-sm">
              <p>
                <strong>Bayerisches Landesamt für Datenschutzaufsicht (BayLDA)</strong><br />
                Promenade 18, 91522 Ansbach<br />
                <a href="https://www.lda.bayern.de" target="_blank" rel="noopener noreferrer" className="text-[#79B92A] hover:underline">
                  www.lda.bayern.de
                </a>
              </p>
            </div>
          </section>
          
          {/* Stand */}
          <section className="border-t border-gray-200 pt-6">
            <p className="text-sm text-gray-500">
              <strong>Stand:</strong> März 2026
            </p>
            <p className="text-sm text-gray-500 mt-2">
              Wir behalten uns vor, diese Datenschutzerklärung anzupassen, damit sie stets den aktuellen 
              rechtlichen Anforderungen entspricht.
            </p>
          </section>
        </div>
        
        {/* Quick Links */}
        <div className="mt-8 flex flex-wrap justify-center gap-4 text-sm">
          <Link to="/impressum" className="text-[#79B92A] hover:underline">Impressum</Link>
          <span className="text-gray-300">|</span>
          <Link to="/ueber-uns" className="text-[#79B92A] hover:underline">Über uns</Link>
        </div>
      </main>
      
      <Footer />
    </div>
  );
}
