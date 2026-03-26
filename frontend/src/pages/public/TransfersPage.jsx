import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { AdSlot, SidebarAd } from "@/components/AdSlot";
import { useEffect, useState } from "react";
import { getConfirmedTransfers, getPlayer, getClub } from "@/api";
import { Handshake, ArrowRight } from "@phosphor-icons/react";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Link } from "react-router-dom";

export default function TransfersPage() {
  const [transfers, setTransfers] = useState([]);
  const [transfersWithDetails, setTransfersWithDetails] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const res = await getConfirmedTransfers({ limit: 50 });
        setTransfers(res.data);

        // Fetch player and club details
        const detailed = await Promise.all(
          res.data.map(async (transfer) => {
            let player = null;
            let fromClub = null;
            let toClub = null;

            if (transfer.player_id) {
              try {
                const playerRes = await getPlayer(transfer.player_id);
                player = playerRes.data;
              } catch (e) {}
            }

            if (transfer.from_club_id) {
              try {
                const clubRes = await getClub(transfer.from_club_id);
                fromClub = clubRes.data;
              } catch (e) {}
            }

            if (transfer.to_club_id) {
              try {
                const clubRes = await getClub(transfer.to_club_id);
                toClub = clubRes.data;
              } catch (e) {}
            }

            return { ...transfer, player, fromClub, toClub };
          })
        );

        setTransfersWithDetails(detailed);
      } catch (e) {
        console.error("Transfers load error:", e);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const formatDate = (dateString) => {
    if (!dateString) return "";
    const date = new Date(dateString);
    return date.toLocaleDateString("de-DE", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    });
  };

  const formatFee = (amount, currency) => {
    if (!amount) return "Ablösefrei";
    if (amount >= 1000000) {
      return `${(amount / 1000000).toFixed(1)} Mio. ${currency}`;
    }
    return `${amount.toLocaleString("de-DE")} ${currency}`;
  };

  return (
    <div className="min-h-screen flex flex-col bg-gray-50" data-testid="transfers-page">
      <Header />

      {/* Top Ad */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-2">
          <AdSlot slotKey="below_header" minHeight="90px" />
        </div>
      </div>

      <main className="flex-1">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Page Title */}
          <div className="mb-8">
            <h1 className="font-['Oswald'] text-4xl font-bold uppercase flex items-center" data-testid="page-title">
              <Handshake size={36} className="mr-3 text-[#79B92A]" />
              Bestätigte Transfers
            </h1>
            <p className="text-gray-500 mt-2">
              Alle offiziell bestätigten Transfers und Wechsel
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Main Content */}
            <div className="lg:col-span-2">
              {loading ? (
                <div className="bg-white border">
                  <div className="p-4">
                    {[...Array(5)].map((_, i) => (
                      <div key={i} className="py-4 border-b last:border-0">
                        <Skeleton className="h-6 w-3/4 mb-2" />
                        <Skeleton className="h-4 w-1/2" />
                      </div>
                    ))}
                  </div>
                </div>
              ) : transfersWithDetails.length > 0 ? (
                <div className="bg-white border border-gray-200 overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="transfer-table w-full">
                      <thead>
                        <tr>
                          <th>Spieler</th>
                          <th>Von</th>
                          <th>Zu</th>
                          <th>Ablöse</th>
                          <th>Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {transfersWithDetails.map((t, idx) => (
                          <>
                            <tr key={t.id}>
                              <td>
                                {t.player ? (
                                  <Link
                                    to={`/spieler/${t.player.slug}`}
                                    className="font-medium text-[#79B92A] hover:underline"
                                  >
                                    {t.player.name}
                                  </Link>
                                ) : (
                                  <span className="text-gray-400">-</span>
                                )}
                              </td>
                              <td>
                                {t.fromClub ? (
                                  <Link
                                    to={`/verein/${t.fromClub.slug}`}
                                    className="hover:text-[#79B92A]"
                                  >
                                    {t.fromClub.name}
                                  </Link>
                                ) : (
                                  <span className="text-gray-400">-</span>
                                )}
                              </td>
                              <td>
                                {t.toClub ? (
                                  <Link
                                    to={`/verein/${t.toClub.slug}`}
                                    className="hover:text-[#79B92A]"
                                  >
                                    {t.toClub.name}
                                  </Link>
                                ) : (
                                  <span className="text-gray-400">-</span>
                                )}
                              </td>
                              <td className="font-medium">
                                {formatFee(t.fee_amount, t.fee_currency)}
                              </td>
                              <td>
                                <Badge
                                  className={
                                    t.status === "official"
                                      ? "badge-official"
                                      : "badge-confirmed"
                                  }
                                >
                                  {t.status === "official" ? "Offiziell" : "Bestätigt"}
                                </Badge>
                              </td>
                            </tr>
                            {/* Insert ad row after every 6th transfer */}
                            {(idx + 1) % 6 === 0 && idx < transfersWithDetails.length - 1 && (
                              <tr key={`ad-${idx}`}>
                                <td colSpan={5} className="p-0">
                                  <AdSlot slotKey={`listing_after_card_${idx + 1}`} minHeight="60px" />
                                </td>
                              </tr>
                            )}
                          </>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : (
                <div className="text-center py-12 bg-white border">
                  <Handshake size={48} className="mx-auto text-gray-300 mb-4" />
                  <p className="text-gray-500">Noch keine Transfers vorhanden</p>
                </div>
              )}
            </div>

            {/* Sidebar */}
            <aside className="space-y-6">
              <SidebarAd slotKey="sidebar_top" />
              <SidebarAd slotKey="sidebar_middle" />
              <SidebarAd slotKey="sidebar_bottom" />
            </aside>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
