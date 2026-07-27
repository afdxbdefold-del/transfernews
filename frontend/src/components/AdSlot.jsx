import { useEffect, useState } from "react";
import { getActiveAdSlots } from "@/api";
import { SidebarAd300x600, MrecAd, MrecAd2 } from "./TheMoneytizerAds";

export function AdSlot({ slotKey, className = "", minHeight = "90px" }) {
  const [slot, setSlot] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSlot = async () => {
      try {
        const res = await getActiveAdSlots();
        const foundSlot = res.data.find((s) => s.slot_key === slotKey);
        setSlot(foundSlot);
      } catch (e) {
        console.error("Ad slot error:", e);
      } finally {
        setLoading(false);
      }
    };
    fetchSlot();
  }, [slotKey]);

  if (loading) return null;
  if (!slot || !slot.is_active) return null;
  if (!slot.html_code && !slot.embed_code && !slot.js_code) return null;

  return (
    <div
      className={`ad-slot ${className}`}
      style={{ minHeight }}
      data-testid={`ad-slot-${slotKey}`}
      data-ad-slot={slotKey}
    >
      {slot.html_code && <div dangerouslySetInnerHTML={{ __html: slot.html_code }} />}
      {slot.embed_code && <div dangerouslySetInnerHTML={{ __html: slot.embed_code }} />}
      {slot.js_code && <script dangerouslySetInnerHTML={{ __html: slot.js_code }} />}
    </div>
  );
}

export function AdBanner({ slotKey, size = "leaderboard" }) {
  return <AdSlot slotKey={slotKey} />;
}

// TheMonetizer 300x600 Sidebar Ad
export function SidebarAd({ slotKey }) {
  return <SidebarAd300x600 />;
}

// TheMonetizer MREC
export function FeedAd({ slotKey }) {
  return <MrecAd />;
}

export function MobileStickyAd() {
  return <AdSlot slotKey="mobile_sticky_bottom" minHeight="50px" />;
}
