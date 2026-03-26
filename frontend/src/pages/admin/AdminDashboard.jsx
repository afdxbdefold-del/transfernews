import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import AdminLayout from "@/components/AdminLayout";
import { getDashboardStats, initAdSlots, getAvailableCompetitions, importCompetition, scrapeNews } from "@/api";
import { toast } from "sonner";
import {
  User,
  Buildings,
  Trophy,
  Newspaper,
  Lightning,
  Handshake,
  TrendUp,
  Megaphone,
  LinkSimple,
  Download,
  Globe,
} from "@phosphor-icons/react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export default function AdminDashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [competitions, setCompetitions] = useState([]);
  const [selectedCompetition, setSelectedCompetition] = useState("");
  const [importing, setImporting] = useState(false);
  const [scraping, setScraping] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem("adminToken");
    if (!token) {
      navigate("/admin/login");
      return;
    }

    fetchStats();
    fetchCompetitions();
  }, [navigate]);

  const fetchStats = async () => {
    try {
      const res = await getDashboardStats();
      setStats(res.data);
    } catch (e) {
      if (e.response?.status === 401) {
        navigate("/admin/login");
      }
      console.error("Dashboard stats error:", e);
    } finally {
      setLoading(false);
    }
  };

  const fetchCompetitions = async () => {
    try {
      const res = await getAvailableCompetitions();
      setCompetitions(res.data.competitions);
    } catch (e) {
      console.error("Competitions error:", e);
    }
  };

  const handleInitAdSlots = async () => {
    try {
      const res = await initAdSlots();
      toast.success(res.data.message);
      fetchStats();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Fehler beim Erstellen der Ad-Slots");
    }
  };

  const handleImportCompetition = async () => {
    if (!selectedCompetition) {
      toast.error("Bitte Wettbewerb auswählen");
      return;
    }
    setImporting(true);
    try {
      const res = await importCompetition(selectedCompetition);
      toast.success(`${res.data.competition}: ${res.data.clubs_imported} Vereine, ${res.data.players_imported} Spieler importiert`);
      fetchStats();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Import fehlgeschlagen - API-Key prüfen");
    } finally {
      setImporting(false);
    }
  };

  const handleScrapeNews = async () => {
    setScraping(true);
    try {
      const res = await scrapeNews();
      toast.success(`${res.data.new_events} neue Events gescrapt, ${res.data.duplicates_skipped} Duplikate übersprungen`);
      fetchStats();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Scraping fehlgeschlagen");
    } finally {
      setScraping(false);
    }
  };

  const statCards = stats
    ? [
        { label: "Spieler", value: stats.players, icon: User, color: "bg-blue-500" },
        { label: "Vereine", value: stats.clubs, icon: Buildings, color: "bg-purple-500" },
        { label: "Wettbewerbe", value: stats.competitions, icon: Trophy, color: "bg-yellow-500" },
        { label: "Quellen", value: stats.sources, icon: LinkSimple, color: "bg-pink-500" },
        { label: "Events (Ausstehend)", value: stats.events_pending, icon: Lightning, color: "bg-red-500" },
        { label: "Events (Gesamt)", value: stats.events_total, icon: Lightning, color: "bg-orange-500" },
        { label: "Artikel (Entwürfe)", value: stats.articles_draft, icon: Newspaper, color: "bg-gray-500" },
        { label: "Artikel (Veröffentlicht)", value: stats.articles_published, icon: Newspaper, color: "bg-[#00a651]" },
        { label: "Transfers", value: stats.transfers_total, icon: Handshake, color: "bg-teal-500" },
        { label: "Gerüchte (Aktiv)", value: stats.rumours_active, icon: TrendUp, color: "bg-amber-500" },
        { label: "Ad-Slots (Aktiv)", value: stats.ad_slots_active, icon: Megaphone, color: "bg-indigo-500" },
        { label: "Ad-Slots (Gesamt)", value: stats.ad_slots_total, icon: Megaphone, color: "bg-slate-500" },
      ]
    : [];

  return (
    <AdminLayout title="Dashboard">
      <div data-testid="admin-dashboard">
        {/* Data Import Section */}
        <div className="bg-white border border-gray-200 p-6 mb-8">
          <h3 className="font-['Oswald'] text-xl font-bold uppercase mb-4 flex items-center">
            <Download size={24} className="mr-2 text-[#00a651]" />
            Daten-Import
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Competition Import */}
            <div className="border-r border-gray-200 pr-6">
              <h4 className="font-medium mb-3">Wettbewerb importieren (football-data.org)</h4>
              <div className="flex gap-2">
                <Select value={selectedCompetition} onValueChange={setSelectedCompetition}>
                  <SelectTrigger className="w-[200px]" data-testid="competition-select">
                    <SelectValue placeholder="Wettbewerb wählen" />
                  </SelectTrigger>
                  <SelectContent>
                    {competitions.map((c) => (
                      <SelectItem key={c.code} value={c.code}>
                        {c.name} ({c.country})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button
                  onClick={handleImportCompetition}
                  disabled={importing || !selectedCompetition}
                  className="bg-blue-600 hover:bg-blue-700"
                  data-testid="import-competition-btn"
                >
                  {importing ? "Importiere..." : "Importieren"}
                </Button>
              </div>
              <p className="text-xs text-gray-500 mt-2">
                Importiert Vereine und Spieler für den gewählten Wettbewerb
              </p>
            </div>

            {/* News Scraper */}
            <div className="pl-6">
              <h4 className="font-medium mb-3">Transfer-News scrapen</h4>
              <Button
                onClick={handleScrapeNews}
                disabled={scraping}
                className="bg-orange-600 hover:bg-orange-700"
                data-testid="scrape-news-btn"
              >
                <Globe size={18} className="mr-2" />
                {scraping ? "Scrape läuft..." : "News scrapen"}
              </Button>
              <p className="text-xs text-gray-500 mt-2">
                Scrapt Transfer-News von Sky Sport, Kicker, Sport1
              </p>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mb-8 flex gap-4">
          <Button
            onClick={handleInitAdSlots}
            className="bg-[#00a651] hover:bg-[#008c45]"
            data-testid="init-ad-slots-btn"
          >
            <Megaphone size={18} className="mr-2" />
            Ad-Slots initialisieren
          </Button>
        </div>

        {/* Stats Grid */}
        {loading ? (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {[...Array(12)].map((_, i) => (
              <div key={i} className="bg-white border p-4 animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-1/2 mb-2" />
                <div className="h-8 bg-gray-200 rounded w-1/3" />
              </div>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {statCards.map((card) => {
              const Icon = card.icon;
              return (
                <div
                  key={card.label}
                  className="bg-white border border-gray-200 p-4 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-gray-500">{card.label}</span>
                    <div className={`w-8 h-8 ${card.color} rounded flex items-center justify-center`}>
                      <Icon size={16} className="text-white" />
                    </div>
                  </div>
                  <p className="text-3xl font-bold">{card.value}</p>
                </div>
              );
            })}
          </div>
        )}

        {/* Recent Activity */}
        <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="bg-white border border-gray-200 p-6">
            <h3 className="font-['Oswald'] text-xl font-bold uppercase mb-4">Schnellzugriff</h3>
            <div className="space-y-2">
              <a
                href="/admin/articles"
                className="flex items-center gap-3 p-3 bg-gray-50 hover:bg-gray-100 transition-colors"
              >
                <Newspaper size={20} className="text-[#00a651]" />
                <span>Neuen Artikel erstellen</span>
              </a>
              <a
                href="/admin/players"
                className="flex items-center gap-3 p-3 bg-gray-50 hover:bg-gray-100 transition-colors"
              >
                <User size={20} className="text-blue-500" />
                <span>Spieler verwalten</span>
              </a>
              <a
                href="/admin/transfers"
                className="flex items-center gap-3 p-3 bg-gray-50 hover:bg-gray-100 transition-colors"
              >
                <Handshake size={20} className="text-teal-500" />
                <span>Transfer eintragen</span>
              </a>
              <a
                href="/admin/ad-slots"
                className="flex items-center gap-3 p-3 bg-gray-50 hover:bg-gray-100 transition-colors"
              >
                <Megaphone size={20} className="text-indigo-500" />
                <span>Werbeplätze verwalten</span>
              </a>
            </div>
          </div>

          <div className="bg-white border border-gray-200 p-6">
            <h3 className="font-['Oswald'] text-xl font-bold uppercase mb-4">System-Info</h3>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between py-2 border-b">
                <span className="text-gray-500">Version</span>
                <span className="font-medium">1.0.0</span>
              </div>
              <div className="flex justify-between py-2 border-b">
                <span className="text-gray-500">Datenbank</span>
                <span className="font-medium text-green-600">Verbunden</span>
              </div>
              <div className="flex justify-between py-2 border-b">
                <span className="text-gray-500">LLM-Integration</span>
                <span className="font-medium text-yellow-600">Vorbereitet</span>
              </div>
              <div className="flex justify-between py-2">
                <span className="text-gray-500">Scraper-Pipeline</span>
                <span className="font-medium text-yellow-600">Vorbereitet</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AdminLayout>
  );
}
