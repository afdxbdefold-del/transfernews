import React from "react";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { Helmet } from "react-helmet-async";
import { Link } from "react-router-dom";
import { Buildings, EnvelopeSimple, Phone, MapPin, Scales, ShieldCheck, Certificate } from "@phosphor-icons/react";

export default function ImpressumPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Helmet>
        <title>Impressum - TransferNews</title>
        <meta name="description" content="Impressum und rechtliche Informationen von TransferNews.de - Deutschlands führendes Transfer-Nachrichtenportal." />
        <link rel="canonical" href="https://transfernews.de/impressum" />
      </Helmet>
      
      <Header />
      
      <main className="max-w-4xl mx-auto px-4 py-12">
        <div className="bg-white rounded-lg shadow-sm p-8 md:p-12">
          {/* Header */}
          <div className="flex items-center gap-3 mb-8">
            <Scales size={32} className="text-[#79B92A]" weight="fill" />
            <h1 className="text-3xl font-black text-gray-900" style={{ fontFamily: "'Oswald', sans-serif" }}>
              Impressum
            </h1>
          </div>
          
          {/* Angaben gemäß § 5 TMG */}
          <section className="mb-10">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <Buildings size={20} className="text-[#79B92A]" />
              Angaben gemäß § 5 TMG
            </h2>
            <div className="bg-gray-50 p-6 rounded-lg">
              <p className="font-bold text-lg mb-2">TransferNews Media GmbH</p>
              <p className="text-gray-600 mb-4">
                Musterstraße 123<br />
                80331 München<br />
                Deutschland
              </p>
              <div className="grid md:grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-gray-500">Handelsregister:</p>
                  <p className="font-medium">HRB 123456, Amtsgericht München</p>
                </div>
                <div>
                  <p className="text-gray-500">USt-IdNr.:</p>
                  <p className="font-medium">DE123456789</p>
                </div>
              </div>
            </div>
          </section>
          
          {/* Vertreten durch */}
          <section className="mb-10">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Vertreten durch</h2>
            <p className="text-gray-700">
              Geschäftsführer: Lukas Müller (Chefredakteur)
            </p>
          </section>
          
          {/* Kontakt */}
          <section className="mb-10">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <EnvelopeSimple size={20} className="text-[#79B92A]" />
              Kontakt
            </h2>
            <div className="space-y-3 text-gray-700">
              <p className="flex items-center gap-2">
                <Phone size={18} className="text-gray-400" />
                +49 (0) 89 123 456 78
              </p>
              <p className="flex items-center gap-2">
                <EnvelopeSimple size={18} className="text-gray-400" />
                <a href="mailto:redaktion@transfernews.de" className="text-[#79B92A] hover:underline">
                  redaktion@transfernews.de
                </a>
              </p>
              <p className="flex items-center gap-2">
                <MapPin size={18} className="text-gray-400" />
                München, Deutschland
              </p>
            </div>
          </section>
          
          {/* Verantwortlich für den Inhalt */}
          <section className="mb-10">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <Certificate size={20} className="text-[#79B92A]" />
              Verantwortlich für den Inhalt nach § 55 Abs. 2 RStV
            </h2>
            <p className="text-gray-700">
              Lukas Müller<br />
              TransferNews Media GmbH<br />
              Musterstraße 123<br />
              80331 München
            </p>
          </section>
          
          {/* Redaktionelle Verantwortung */}
          <section className="mb-10">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Redaktionelle Verantwortung</h2>
            <p className="text-gray-700 mb-4">
              Die redaktionelle Verantwortung für die Inhalte auf TransferNews.de liegt bei unserem Team 
              bestehend aus 12 erfahrenen Sportjournalisten.
            </p>
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <p className="text-sm text-green-800 flex items-center gap-2">
                <ShieldCheck size={18} weight="fill" />
                Alle Artikel werden von ausgebildeten Journalisten verfasst und geprüft.
              </p>
            </div>
          </section>
          
          {/* Haftungsausschluss */}
          <section className="mb-10">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Haftungsausschluss</h2>
            
            <h3 className="font-bold text-gray-800 mt-4 mb-2">Haftung für Inhalte</h3>
            <p className="text-gray-600 text-sm leading-relaxed mb-4">
              Als Diensteanbieter sind wir gemäß § 7 Abs.1 TMG für eigene Inhalte auf diesen Seiten nach den 
              allgemeinen Gesetzen verantwortlich. Nach §§ 8 bis 10 TMG sind wir als Diensteanbieter jedoch nicht 
              verpflichtet, übermittelte oder gespeicherte fremde Informationen zu überwachen.
            </p>
            
            <h3 className="font-bold text-gray-800 mt-4 mb-2">Haftung für Links</h3>
            <p className="text-gray-600 text-sm leading-relaxed mb-4">
              Unser Angebot enthält Links zu externen Websites Dritter, auf deren Inhalte wir keinen Einfluss haben. 
              Für die Inhalte der verlinkten Seiten ist stets der jeweilige Anbieter verantwortlich.
            </p>
            
            <h3 className="font-bold text-gray-800 mt-4 mb-2">Urheberrecht</h3>
            <p className="text-gray-600 text-sm leading-relaxed">
              Die durch die Seitenbetreiber erstellten Inhalte und Werke auf diesen Seiten unterliegen dem deutschen 
              Urheberrecht. Beiträge Dritter sind als solche gekennzeichnet. Die Vervielfältigung, Bearbeitung, 
              Verbreitung und jede Art der Verwertung bedürfen der schriftlichen Zustimmung.
            </p>
          </section>
          
          {/* Streitschlichtung */}
          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-4">Streitschlichtung</h2>
            <p className="text-gray-600 text-sm leading-relaxed">
              Die Europäische Kommission stellt eine Plattform zur Online-Streitbeilegung (OS) bereit: 
              <a href="https://ec.europa.eu/consumers/odr" target="_blank" rel="noopener noreferrer" className="text-[#79B92A] hover:underline ml-1">
                https://ec.europa.eu/consumers/odr
              </a>
              <br /><br />
              Wir sind nicht bereit oder verpflichtet, an Streitbeilegungsverfahren vor einer 
              Verbraucherschlichtungsstelle teilzunehmen.
            </p>
          </section>
        </div>
      </main>
      
      <Footer />
    </div>
  );
}
