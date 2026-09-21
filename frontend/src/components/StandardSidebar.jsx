import { SidebarAd300x600, MrecAd, MrecAd2 } from "@/components/TheMoneytizerAds";
import { TrendingWidget } from "@/components/TrendingWidget";

// Existing sidebars can include all three formats without adding another column.
export function SidebarAdSlots() {
  return (
    <div className="mx-auto w-full max-w-[300px] space-y-3">
      <SidebarAd300x600 />
      <MrecAd />
      <MrecAd2 />
    </div>
  );
}

// Standard Sidebar für alle Seiten
export default function StandardSidebar({ showTrending = true }) {
  return (
    <aside className="min-w-0 space-y-3" data-testid="standard-sidebar">
      {/* Sidebar 300x600 */}
      <div className="mx-auto w-full max-w-[300px]"><SidebarAd300x600 /></div>
      
      {/* Trending Widget */}
      {showTrending && <TrendingWidget />}
      
      {/* MREC */}
      <div className="mx-auto w-full max-w-[300px]"><MrecAd /></div>
      
      {/* MREC 2 */}
      <div className="mx-auto w-full max-w-[300px]"><MrecAd2 /></div>
    </aside>
  );
}
