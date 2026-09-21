import DynamicAdSlot from './DynamicAds';
export { useShouldShowAds } from './DynamicAds';
// One canonical admin placement per Moneytizer format, including its native rails/footer.
export function MegabannerAd() { return <DynamicAdSlot slotKey="top_banner_above_header" minHeight="90px" />; }
export function BillboardAd() { return <DynamicAdSlot slotKey="below_header" minHeight="250px" />; }
export function SidebarAd300x600() { return <DynamicAdSlot slotKey="sidebar_top" minHeight="600px" />; }
export function MrecAd() { return <DynamicAdSlot slotKey="sidebar_middle" minHeight="250px" />; }
export function MrecAd2() { return <DynamicAdSlot slotKey="sidebar_bottom" minHeight="250px" />; }
export function AboveFooterAd() { return <DynamicAdSlot slotKey="footer_top" minHeight="90px" />; }
export function StickySkyscraperAd() { return <DynamicAdSlot slotKey="skyscraper" minHeight="0px" />; }
export function GlobalAd() { return <DynamicAdSlot slotKey="global" minHeight="0px" />; }
