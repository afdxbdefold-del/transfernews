const VENDOR = 228;
const CONSENT_PURPOSES = [1, 2, 3, 4, 5, 6];
const INTEREST_PURPOSES = [7, 8, 10];
export const PRIMIS_SRC = 'https://live.primis.tech/live/liveView.php?s=122209';

export function consentAllowsPrimis(data, success) {
  if (!success || !data || data.cmpStatus === 'error' || !['tcloaded', 'useractioncomplete'].includes(data.eventStatus)) return false;
  if (data.gdprApplies === false) return true;
  if (data.gdprApplies !== true || data.vendor?.consents?.[VENDOR] !== true || data.vendor?.legitimateInterests?.[VENDOR] !== true) return false;
  const permitted = (purpose, basis) => {
    const restriction = data.publisher?.restrictions?.[purpose]?.[VENDOR];
    return restriction == null || restriction === basis;
  };
  return CONSENT_PURPOSES.every(id => data.purpose?.consents?.[id] === true && permitted(id, 1)) &&
    INTEREST_PURPOSES.every(id => data.purpose?.legitimateInterests?.[id] === true && permitted(id, 2));
}

// The slider can create frames and timers outside its mount. Keep its page
// marker for the lifetime of the document, even when React removes the mount.
export function loadedPrimisPage() {
  return document.documentElement.dataset.transfernewsPrimisPage;
}

export function mountPrimis(container, page) {
  if (!container?.isConnected || !document.body.contains(container) || loadedPrimisPage()) return;
  const script = document.createElement('script');
  script.id = 'transfernews-primis-loader';
  script.type = 'text/javascript';
  script.setAttribute('language', 'javascript');
  script.src = PRIMIS_SRC;
  document.documentElement.dataset.transfernewsPrimisPage = page;
  container.appendChild(script);
}
