import DynamicAdSlot from './DynamicAds';
export function AdSlot(props) { return <DynamicAdSlot {...props} />; }
export function AdBanner({ slotKey }) { return <AdSlot slotKey={slotKey} />; }
export function SidebarAd({ slotKey = 'sidebar_top' }) { return <AdSlot slotKey={slotKey} />; }
export function FeedAd({ slotKey }) { return <AdSlot slotKey={slotKey} minHeight="250px" />; }
export function MobileStickyAd() { return <AdSlot slotKey="mobile_sticky_bottom" minHeight="50px" />; }
