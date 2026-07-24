import "@/index.css";
import { BrowserRouter, Routes, Route, useLocation, Navigate } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import { HelmetProvider } from "react-helmet-async";
import { useEffect } from "react";

// Scroll to top on route change
function ScrollToTop() {
  const { pathname } = useLocation();
  
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
  
  return null;
}

// Public Pages
import HomePage from "@/pages/public/HomePage";
import NewsListPage from "@/pages/public/NewsListPage";
import NewsDetailPage from "@/pages/public/NewsDetailPage";
import PlayerPage from "@/pages/public/PlayerPage";
import ClubPage from "@/pages/public/ClubPage";
import CompetitionPage from "@/pages/public/CompetitionPage";
import RumoursPage from "@/pages/public/RumoursPage";
import TransfersPage from "@/pages/public/TransfersPage";
import SearchPage from "@/pages/public/SearchPage";
import AuthorPage from "@/pages/public/AuthorPage";
import ThemePage from "@/pages/public/ThemePage";
import AuthorsPage from "@/pages/public/AuthorsPage";
import ImpressumPage from "@/pages/public/ImpressumPage";
import AboutPage from "@/pages/public/AboutPage";
import DatenschutzPage from "@/pages/public/DatenschutzPage";

// Admin Pages
import AdminLogin from "@/pages/admin/AdminLogin";
import AdminDashboard from "@/pages/admin/AdminDashboard";
import AdminPlayers from "@/pages/admin/AdminPlayers";
import AdminClubs from "@/pages/admin/AdminClubs";
import AdminCompetitions from "@/pages/admin/AdminCompetitions";
import AdminSources from "@/pages/admin/AdminSources";
import AdminEvents from "@/pages/admin/AdminEvents";
import AdminArticles from "@/pages/admin/AdminArticles";
import AdminAdSlots from "@/pages/admin/AdminAdSlots";
import AdminTransfers from "@/pages/admin/AdminTransfers";
import AdminRumours from "@/pages/admin/AdminRumours";
import AdminGSC from "@/pages/admin/AdminGSC";

function App() {
  return (
    <HelmetProvider>
      <div className="App min-h-screen">
        <BrowserRouter>
          <ScrollToTop />
          <Routes>
            {/* Public Routes */}
            <Route path="/" element={<HomePage />} />
            <Route path="/news" element={<Navigate to="/" replace />} />
            <Route path="/news/:slug" element={<NewsDetailPage />} />
            <Route path="/spieler/:slug" element={<PlayerPage />} />
            <Route path="/verein/:slug" element={<ClubPage />} />
            <Route path="/wettbewerb/:slug" element={<CompetitionPage />} />
            <Route path="/thema/:slug" element={<ThemePage />} />
            <Route path="/geruechte" element={<RumoursPage />} />
            <Route path="/transfers" element={<TransfersPage />} />
            <Route path="/suche" element={<SearchPage />} />
            <Route path="/autor/:slug" element={<AuthorPage />} />
            <Route path="/redaktion" element={<AuthorsPage />} />
            <Route path="/impressum" element={<ImpressumPage />} />
            <Route path="/ueber-uns" element={<AboutPage />} />
            <Route path="/datenschutz" element={<DatenschutzPage />} />
            
            {/* Admin Routes */}
            <Route path="/admin/login" element={<AdminLogin />} />
            <Route path="/admin" element={<AdminDashboard />} />
            <Route path="/admin/players" element={<AdminPlayers />} />
            <Route path="/admin/clubs" element={<AdminClubs />} />
            <Route path="/admin/competitions" element={<AdminCompetitions />} />
            <Route path="/admin/sources" element={<AdminSources />} />
            <Route path="/admin/events" element={<AdminEvents />} />
            <Route path="/admin/articles" element={<AdminArticles />} />
            <Route path="/admin/ad-slots" element={<AdminAdSlots />} />
            <Route path="/admin/transfers" element={<AdminTransfers />} />
            <Route path="/admin/rumours" element={<AdminRumours />} />
            <Route path="/admin/gsc" element={<AdminGSC />} />
          </Routes>
        </BrowserRouter>
        <Toaster position="top-right" />
      </div>
    </HelmetProvider>
  );
}

export default App;
