import Header from "@/components/Header";
import Footer from "@/components/Footer";
import PageLayout from "@/components/PageLayout";
import { useEffect, useState } from "react";
import { getTopDeals } from "@/api";
import { CaretRight, TrendUp, ArrowRight, Trophy } from "@phosphor-icons/react";
import { Link } from "react-router-dom";
import { Helmet } from "react-helmet-async";

function formatFee(amount) {
  if (!amount || amount === 0) return 'ablösefrei';
  if (amount >= 1000000) {
    return `${(amount / 1000000).toFixed(1).replace('.0', '')} Mio. €`;
  }
  return `${(amount / 1000).toFixed(0)} Tsd. €`;
}

function TopDealRow({ transfer, rank }) {
  const hasFromSlug = transfer.from_club_slug;
  const hasToSlug = transfer.to_club_slug;
  const hasPlayerSlug = transfer.player_slug;
  
  return (
    <div 
      className="flex items-center gap-3 p-3 hover:bg-[#f8fdf8] border-b border-gray-200 last:border-0 group"
      data-testid={`top-deal-${rank}`}
    >
      {/* Rank */}
      <div className={`w-8 h-8 flex-shrink-0 rounded-full flex items-center justify-center text-[13px] font-bold ${
        rank === 1 ? 'bg-yellow-400 text-yellow-900' :
        rank === 2 ? 'bg-gray-300 text-gray-700' :
        rank === 3 ? 'bg-amber-600 text-white' :
        'bg-gray-100 text-gray-600'
      }`}>
        {rank}
      </div>
      
      {/* Player Info */}
      <div className="flex-1 min-w-0">
        {hasPlayerSlug ? (
          <Link 
            to={`/spieler/${transfer.player_slug}`}
            className="text-[14px] font-bold text-gray-900 hover:text-[#79B92A] transition-colors"
          >
            {transfer.player_name}
          </Link>
        ) : (
          <span className="text-[14px] font-bold text-gray-900">{transfer.player_name}</span>
        )}
        
        {/* Transfer Flow */}
        <div className="flex items-center gap-2 mt-1 text-[12px] text-gray-600">
          {hasFromSlug ? (
            <Link 
              to={`/verein/${transfer.from_club_slug}`}
              className="hover:text-[#79B92A] hover:underline transition-colors"
            >
              {transfer.from_club}
            </Link>
          ) : (
            <span>{transfer.from_club}</span>
          )}
          <ArrowRight size={12} className="text-[#79B92A] flex-shrink-0" />
          {hasToSlug ? (
            <Link 
              to={`/verein/${transfer.to_club_slug}`}
              className="hover:text-[#79B92A] hover:underline transition-colors"
            >
              {transfer.to_club}
            </Link>
          ) : (
            <span>{transfer.to_club}</span>
          )}
        </div>
      </div>
      
      {/* Season */}
      <div className="text-[11px] text-gray-500 flex-shrink-0 w-16 text-center">
        {transfer.season || transfer.year}
      </div>
      
      {/* Fee */}
      <div className="text-right flex-shrink-0 w-24">
        <div className={`text-[15px] font-bold ${transfer.fee_amount > 100000000 ? 'text-[#79B92A]' : 'text-gray-900'}`}>
          {formatFee(transfer.fee_amount)}
        </div>
        <div className="text-[9px] text-gray-500 uppercase">{transfer.transfer_type || 'Fest'}</div>
      </div>
      
      <CaretRight size={14} className="text-gray-400 flex-shrink-0" />
    </div>
  );
}

export default function TopDealsPage() {
  const [transfers, setTransfers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetch = async () => {
      try {
        const res = await getTopDeals({ limit: 30 });
        setTransfers(res.data || []);
      } catch (e) {
        console.error("Error:", e);
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, []);

  // Calculate totals
  const totalFees = transfers.reduce((sum, t) => sum + (t.fee_amount || 0), 0);
  const avgFee = transfers.length > 0 ? totalFees / transfers.length : 0;

  return (
    <PageLayout>
      <Helmet>
        <title>Top-Transfers | Die teuersten Transfers | TransferNews.de</title>
        <meta name="description" content="Die teuersten Fußball-Transfers aller Zeiten - sortiert nach Ablösesumme." />
        <link rel="canonical" href="https://transfernews.de/top-deals" />
      </Helmet>
      
      <Header />
      
      <main className="flex-1 py-3 px-3" data-testid="top-deals-page">
        <div className="bg-white border border-gray-300 rounded-sm overflow-hidden">
          <div className="bg-[#79B92A] px-3 py-2.5 flex items-center gap-2">
            <Trophy size={18} className="text-white" weight="fill" />
            <h1 className="text-white text-[13px] font-bold uppercase">Top-Transfers nach Ablösesumme</h1>
          </div>
          
          {/* Stats Bar */}
          <div className="bg-gray-50 px-3 py-2.5 border-b border-gray-200 flex items-center justify-between text-[11px]">
            <div className="flex items-center gap-6">
              <span className="text-gray-500">
                <strong className="text-gray-700">{transfers.length}</strong> Transfers
              </span>
              <span className="text-gray-500">
                Gesamtvolumen: <strong className="text-[#79B92A]">{formatFee(totalFees)}</strong>
              </span>
              <span className="text-gray-500">
                Durchschnitt: <strong className="text-gray-700">{formatFee(avgFee)}</strong>
              </span>
            </div>
            <div className="flex items-center gap-3 text-[10px]">
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-yellow-400"></span> 1. Platz
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-gray-300"></span> 2. Platz
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-amber-600"></span> 3. Platz
              </span>
            </div>
          </div>
          
          {loading ? (
            <div className="divide-y divide-gray-200">
              {[...Array(10)].map((_, i) => (
                <div key={i} className="flex items-center gap-3 p-3 animate-pulse">
                  <div className="w-8 h-8 bg-gray-200 rounded-full" />
                  <div className="flex-1">
                    <div className="h-4 bg-gray-200 rounded w-1/3 mb-2" />
                    <div className="h-3 bg-gray-200 rounded w-1/2" />
                  </div>
                  <div className="w-16 h-4 bg-gray-200 rounded" />
                  <div className="w-24 h-5 bg-gray-200 rounded" />
                </div>
              ))}
            </div>
          ) : transfers.length > 0 ? (
            <div>
              {transfers.map((transfer, idx) => (
                <TopDealRow key={transfer.id} transfer={transfer} rank={idx + 1} />
              ))}
            </div>
          ) : (
            <div className="p-8 text-center text-gray-500 text-[13px]">
              Keine Transfers mit Ablösesumme vorhanden.
              <Link to="/" className="block mt-2 text-[#79B92A] hover:underline">
                Alle News ansehen
              </Link>
            </div>
          )}
        </div>
      </main>
      
      <Footer />
    </PageLayout>
  );
}
