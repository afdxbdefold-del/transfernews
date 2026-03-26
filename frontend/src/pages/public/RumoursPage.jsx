import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { AdSlot, SidebarAd } from "@/components/AdSlot";
import { useEffect, useState } from "react";
import { getRumours, getPlayer, getClub } from "@/api";
import { TrendUp, ArrowRight } from "@phosphor-icons/react";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Link } from "react-router-dom";

export default function RumoursPage() {
  const [rumours, setRumours] = useState([]);
  const [rumoursWithDetails, setRumoursWithDetails] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const res = await getRumours({ limit: 50 });
        setRumours(res.data);

        // Fetch player and club details for each rumour
        const detailed = await Promise.all(
          res.data.map(async (rumour) => {
            let player = null;
            let targetClub = null;

            if (rumour.player_id) {
              try {
                const playerRes = await getPlayer(rumour.player_id);
                player = playerRes.data;
              } catch (e) {}
            }

            if (rumour.target_club_id) {
              try {
                const clubRes = await getClub(rumour.target_club_id);
                targetClub = clubRes.data;
              } catch (e) {}
            }

            return { ...rumour, player, targetClub };
          })
        );

        setRumoursWithDetails(detailed);
      } catch (e) {
        console.error("Rumours load error:", e);
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

  return (
    <div className="min-h-screen flex flex-col bg-gray-50" data-testid="rumours-page">
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
              <TrendUp size={36} className="mr-3 text-yellow-600" />
              Transfer-Gerüchte
            </h1>
            <p className="text-gray-500 mt-2">
              Die neuesten Gerüchte und Spekulationen vom Transfermarkt
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Main Content */}
            <div className="lg:col-span-2">
              {loading ? (
                <div className="space-y-4">
                  {[...Array(5)].map((_, i) => (
                    <div key={i} className="bg-white border p-4">
                      <Skeleton className="h-6 w-3/4 mb-3" />
                      <Skeleton className="h-4 w-1/2" />
                    </div>
                  ))}
                </div>
              ) : rumoursWithDetails.length > 0 ? (
                <div className="space-y-4">
                  {rumoursWithDetails.map((rumour, idx) => (
                    <div key={rumour.id}>
                      <div className="bg-white border border-gray-200 p-4 hover:border-yellow-400 transition-colors">
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-3">
                              <Badge className="badge-rumour">Gerücht</Badge>
                              <Badge
                                className={
                                  rumour.status === "active"
                                    ? "bg-yellow-100 text-yellow-800"
                                    : rumour.status === "confirmed"
                                    ? "badge-confirmed"
                                    : "bg-gray-100 text-gray-600"
                                }
                              >
                                {rumour.status === "active"
                                  ? "Aktuell"
                                  : rumour.status === "confirmed"
                                  ? "Bestätigt"
                                  : rumour.status}
                              </Badge>
                            </div>

                            <div className="flex items-center gap-2 text-lg font-medium mb-2">
                              {rumour.player ? (
                                <Link
                                  to={`/spieler/${rumour.player.slug}`}
                                  className="text-[#79B92A] hover:underline"
                                >
                                  {rumour.player.name}
                                </Link>
                              ) : (
                                <span>Unbekannter Spieler</span>
                              )}
                              {rumour.targetClub && (
                                <>
                                  <ArrowRight size={20} className="text-gray-400" />
                                  <Link
                                    to={`/verein/${rumour.targetClub.slug}`}
                                    className="text-[#79B92A] hover:underline"
                                  >
                                    {rumour.targetClub.name}
                                  </Link>
                                </>
                              )}
                            </div>

                            <div className="flex items-center gap-4 text-sm text-gray-500">
                              <span>{formatDate(rumour.created_at)}</span>
                              <div className="flex items-center gap-2">
                                <span>Wahrscheinlichkeit:</span>
                                <div className="h-2 w-20 bg-gray-200 rounded">
                                  <div
                                    className="h-full bg-yellow-500 rounded"
                                    style={{ width: `${rumour.confidence_score}%` }}
                                  />
                                </div>
                                <span className="font-medium">{rumour.confidence_score}%</span>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Insert ad after every 4th item */}
                      {(idx + 1) % 4 === 0 && idx < rumoursWithDetails.length - 1 && (
                        <div className="my-4">
                          <AdSlot slotKey={`listing_after_card_${idx + 1}`} minHeight="90px" />
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 bg-white border">
                  <TrendUp size={48} className="mx-auto text-gray-300 mb-4" />
                  <p className="text-gray-500">Noch keine Gerüchte vorhanden</p>
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
