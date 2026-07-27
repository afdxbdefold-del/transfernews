import { useLocation } from "react-router-dom";
import { SidebarAd300x600, MrecAd, MrecAd2 } from "@/components/TheMoneytizerAds";
import { TrendingWidget } from "@/components/TrendingWidget";

// Standard Sidebar für alle Seiten
export default function StandardSidebar({ showTrending = true }) {
  const location = useLocation();
  
  return (
    <aside className="hidden lg:block space-y-3" data-testid="standard-sidebar">
      {/* Sidebar 300x600 */}
      <SidebarAd300x600 key={`sidebar-ad-${location.pathname}`} />
      
      {/* Trending Widget */}
      {showTrending && <TrendingWidget />}
      
      {/* MREC */}
      <MrecAd key={`mrec-${location.pathname}`} />
      
      {/* MREC 2 */}
      <MrecAd2 key={`mrec2-${location.pathname}`} />
    </aside>
  );
}
