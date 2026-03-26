import { useEffect, useState } from "react";
import { getActiveAdSlots } from "@/api";

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

  // Render immediately without lazy loading
  return (
    <div
      className={`ad-slot ${className}`}
      style={{ minHeight }}
      data-testid={`ad-slot-${slotKey}`}
      data-ad-slot={slotKey}
    >
      {loading ? (
        <span className="text-xs text-gray-400">Lädt Anzeige...</span>
      ) : slot && slot.is_active ? (
        <div className="w-full h-full">
          {slot.html_code && (
            <div dangerouslySetInnerHTML={{ __html: slot.html_code }} />
          )}
          {slot.embed_code && (
            <div dangerouslySetInnerHTML={{ __html: slot.embed_code }} />
          )}
          {slot.js_code && (
            <script dangerouslySetInnerHTML={{ __html: slot.js_code }} />
          )}
          {!slot.html_code && !slot.embed_code && !slot.js_code && (
            <span className="text-xs text-gray-400">{slot.name}</span>
          )}
        </div>
      ) : (
        <span className="text-xs text-gray-400">Werbeplatz: {slotKey}</span>
      )}
    </div>
  );
}

export function AdBanner({ slotKey, size = "leaderboard" }) {
  const sizes = {
    leaderboard: { width: "728px", height: "90px" },
    rectangle: { width: "300px", height: "250px" },
    banner: { width: "468px", height: "60px" },
    skyscraper: { width: "160px", height: "600px" },
    mobile: { width: "320px", height: "50px" },
  };

  const { height } = sizes[size] || sizes.leaderboard;

  return (
    <div className="flex justify-center my-4" data-testid={`ad-banner-${slotKey}`}>
      <AdSlot slotKey={slotKey} minHeight={height} />
    </div>
  );
}

export function SidebarAd({ slotKey }) {
  return (
    <div className="mb-6" data-testid={`sidebar-ad-${slotKey}`}>
      <AdSlot slotKey={slotKey} minHeight="250px" className="ad-slot-rectangle" />
    </div>
  );
}

export function FeedAd({ slotKey, interval }) {
  return (
    <div className="my-4" data-testid={`feed-ad-${slotKey}`} data-interval={interval}>
      <AdSlot slotKey={slotKey} minHeight="90px" />
    </div>
  );
}

export function MobileStickyAd() {
  return (
    <div className="mobile-sticky-ad md:hidden" data-testid="mobile-sticky-ad">
      <AdSlot slotKey="mobile_sticky_bottom" minHeight="50px" />
    </div>
  );
}
