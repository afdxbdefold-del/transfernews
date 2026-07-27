import PageLayout from "@/components/PageLayout";
import React from "react";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { Helmet } from "react-helmet-async";
import { Link } from "react-router-dom";
import { ShieldCheck, Cookie, Eye, Database, Lock, Globe, EnvelopeSimple, UserCircle } from "@phosphor-icons/react";

export default function DatenschutzPage() {
  return (
    <PageLayout>
      <Helmet>
        <title>Datenschutzerklärung - TransferNews</title>
        <meta name="description" content="Datenschutzerklärung von TransferNews.de - Informationen zum Schutz Ihrer persönlichen Daten gemäß DSGVO." />
        <link rel="canonical" href="https://transfernews.de/datenschutz" />
      </Helmet>
      
      <Header />
      
      <main className="flex-1 py-6 px-4">
        <div className="bg-white rounded-lg shadow-sm p-8">
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
          
          <section className="mb-10">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <UserCircle size={20} className="text-[#79B92A]" />
              1. Verantwortlicher
            </h2>
            <div className="bg-gray-50 p-5 rounded-lg text-gray-700">
              <p className="font-semibold mb-2">AF Consulting</p>
              <p>Am Nesseufer 1<br />26789 Leer<br />Deutschland</p>
              <p className="mt-3">
                Vertreten durch: Andreas Frey<br />
                E-Mail: <a href="mailto:mail@serien.de" className="text-[#79B92A] hover:underline">mail@serien.de</a>
              </p>
            </div>
          </section>
          
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
          </section>
          
          <section className="mb-10">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <Lock size={20} className="text-[#79B92A]" />
              4. Ihre Rechte
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
                <p className="text-sm text-gray-600">Sie können die Löschung Ihrer Daten verlangen.</p>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-semibold text-gray-900 mb-1">Widerspruchsrecht</h4>
                <p className="text-sm text-gray-600">Sie können der Verarbeitung Ihrer Daten widersprechen.</p>
              </div>
            </div>
          </section>
          
          <section className="mb-10">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <Globe size={20} className="text-[#79B92A]" />
              5. Drittanbieter-Dienste
            </h2>
            
            <h3 className="font-bold text-gray-800 mt-4 mb-2">Hosting</h3>
            <p className="text-gray-600 mb-4">
              Unsere Website wird auf Servern in Deutschland gehostet (Hetzner Online GmbH).
            </p>
            
            <h3 className="font-bold text-gray-800 mt-4 mb-2">Werbung (TheMonetizer)</h3>
            <p className="text-gray-600 mb-4">
              Wir nutzen TheMonetizer zur Einbindung von Werbeanzeigen. Dabei können Cookies gesetzt 
              und personenbezogene Daten verarbeitet werden. Weitere Informationen finden Sie in der 
              Datenschutzerklärung von TheMonetizer.
            </p>
            
            <h3 className="font-bold text-gray-800 mt-4 mb-2">Bilder (Wikimedia Commons, Unsplash, Pexels)</h3>
            <p className="text-gray-600 mb-4">
              Wir verwenden lizenzfreie Bilder. Beim Laden dieser Bilder kann Ihre IP-Adresse an die 
              jeweiligen Anbieter übermittelt werden.
            </p>
          </section>
          
          <section className="mb-10">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <EnvelopeSimple size={20} className="text-[#79B92A]" />
              6. Kontakt bei Datenschutzfragen
            </h2>
            <div className="bg-gray-50 p-5 rounded-lg">
              <p className="text-gray-700">
                Andreas Frey<br />
                AF Consulting<br />
                Am Nesseufer 1, 26789 Leer<br />
                E-Mail: <a href="mailto:mail@serien.de" className="text-[#79B92A] hover:underline">mail@serien.de</a>
              </p>
            </div>
          </section>
          
          <section className="mb-10">
            <h2 className="text-xl font-bold text-gray-900 mb-4">7. Beschwerderecht bei der Aufsichtsbehörde</h2>
            <p className="text-gray-600">
              Sie haben das Recht, sich bei einer Datenschutz-Aufsichtsbehörde zu beschweren:
            </p>
            <div className="bg-gray-50 p-5 rounded-lg mt-4 text-gray-600 text-sm">
              <p>
                <strong>Die Landesbeauftragte für Datenschutz Niedersachsen</strong><br />
                Prinzenstraße 5, 30159 Hannover<br />
                <a href="https://www.lfd.niedersachsen.de" target="_blank" rel="noopener noreferrer" className="text-[#79B92A] hover:underline">
                  www.lfd.niedersachsen.de
                </a>
              </p>
            </div>
          </section>
          
          <section className="border-t border-gray-200 pt-6">
            <p className="text-sm text-gray-500">
              <strong>Stand:</strong> Juli 2026
            </p>
          </section>
        </div>
        
        <div className="mt-8 flex flex-wrap justify-center gap-4 text-sm">
          <Link to="/impressum" className="text-[#79B92A] hover:underline">Impressum</Link>
          <span className="text-gray-300">|</span>
          <Link to="/ueber-uns" className="text-[#79B92A] hover:underline">Über uns</Link>
        </div>
      </main>
      
      <Footer />
    </PageLayout>
  );
}
