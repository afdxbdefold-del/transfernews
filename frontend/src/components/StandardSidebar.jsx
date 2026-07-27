import { SidebarAd300x600, MrecAd, MrecAd2 } from "@/components/TheMoneytizerAds";
import { TrendingWidget } from "@/components/TrendingWidget";

// Standard Sidebar für alle Seiten
export default function StandardSidebar({ showTrending = true }) {
  return (
    <aside className="hidden lg:block space-y-3" data-testid="standard-sidebar">
      {/* Sidebar 300x600 */}
      <SidebarAd300x600 />
      
      {/* Trending Widget */}
      {showTrending && <TrendingWidget />}
      
      {/* MREC */}
      <MrecAd />
      
      {/* MREC 2 */}
      <MrecAd2 />
    </aside>
  );
}
