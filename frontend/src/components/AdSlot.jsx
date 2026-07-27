import { useEffect, useState, useRef } from "react";
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

  // Only render if slot has actual ad code
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

// TheMonetizer 300x600 Sidebar Ad (format 3)
export function SidebarAd({ slotKey }) {
  const containerRef = useRef(null);
  
  useEffect(() => {
    if (containerRef.current && !containerRef.current.hasChildNodes()) {
      const script1 = document.createElement('script');
      script1.src = '//ads.themoneytizer.com/s/gen.js?type=3';
      script1.async = true;
      
      const script2 = document.createElement('script');
      script2.src = '//ads.themoneytizer.com/s/requestform.js?siteId=141912&formatId=3';
      script2.async = true;
      
      containerRef.current.appendChild(script1);
      containerRef.current.appendChild(script2);
    }
  }, []);

  return <div id="141912-3" ref={containerRef} data-testid={`ad-slot-${slotKey}`}></div>;
}

export function FeedAd({ slotKey }) {
  return <AdSlot slotKey={slotKey} minHeight="90px" />;
}

export function MobileStickyAd() {
  return <AdSlot slotKey="mobile_sticky_bottom" minHeight="50px" />;
}
