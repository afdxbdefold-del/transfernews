import { Link } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import Header from '@/components/Header';
import Footer from '@/components/Footer';

export default function NotFoundPage({ title = 'Seite nicht gefunden' }) {
  return <div className="mx-auto max-w-[1000px] bg-white min-h-screen">
    <Helmet><title>{`${title} | TransferNews.de`}</title><meta name="robots" content="noindex, follow" /></Helmet>
    <Header />
    <main className="px-6 py-20 text-center" data-testid="not-found">
      <p className="text-sm text-gray-500 mb-3">404</p>
      <h1 className="text-3xl font-bold mb-4">{title}</h1>
      <p className="text-gray-600 mb-6">Diese Seite ist nicht verfügbar.</p>
      <Link to="/" className="font-semibold text-[#79B92A] underline">Zur Startseite</Link>
    </main>
    <Footer />
  </div>;
}
