import { FreestarPage, FreestarSlot, FreestarRails } from './FreestarAds';
export default function PageLayout({ children, ads = true }) {
  return <FreestarPage enabled={ads}>
    <div className="min-h-screen bg-[#f2f2f2] dark:bg-[#1a1a1a] relative" data-testid="page-layout">
      <div className="w-full max-w-[1000px] mx-auto"><FreestarSlot name="leaderboard_1" /></div>
      <div className="w-full max-w-[1000px] mx-auto min-h-screen bg-[#e8e8e8] dark:bg-gray-950">
        {children}
      </div>
      <FreestarRails />
    </div>
  </FreestarPage>;
}
export function ContentWrapper({ children, className = "" }) {
  return <div className={`px-3 py-3 ${className}`}>{children}</div>;
}
