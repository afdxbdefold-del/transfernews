# Advertising operation

The active publisher is The Moneytizer site **141912**. The frontend owns loading,
responsive layout, and cleanup. The database owns activation, page and device
selection, dates, and any explicitly supplied custom code.

| Slot key | Provider format | Placement |
| --- | --- | --- |
| top_banner_above_header | 1 | Top megabanner |
| below_header | 31 | Billboard |
| sidebar_top | 3 | 300 x 600 |
| sidebar_middle | 2 | First 300 x 250 |
| sidebar_bottom | 19 | Second 300 x 250 |
| footer_top | 28 | Banner above the footer |
| skyscraper | 4 | Provider-managed 120 x 600 sticky side rails |
| global | 6 | Provider-managed footer / slide-in |

`ad_slot_defaults.py` inserts missing canonical entries at startup with
`$setOnInsert`; it never overwrites an existing disabled placement, custom tag,
device setting, or publication period. The initialization endpoint uses the
same definitions. Historical empty position records are only placeholders;
they do not constitute additional provider formats.

The existing six placements remain configured as before: the three sidebar
formats are desktop-only, while top, billboard and footer banners allow all
devices. The restored global format allows all devices. Side rails require at
least 1360 CSS pixels to keep space beside the 1000-pixel site column. Legal and
administration pages do not load advertisements.

The provider selects mobile creatives from the user agent. Resizing a desktop
browser does not emulate a phone user agent. The wrapper fits an oversized
creative without cropping it, and does not start another auction for every
pixel resize. A document-wide owner prevents duplicate format IDs. Public
same-origin navigation starts a new document after ads load, matching the
existing header navigation, so provider auctions and listeners cannot accumulate
across normal navigation. Modified clicks, downloads, and same-page anchors are
preserved. Targeted cleanup covers programmatic route changes and disabling.

The provider creates side rails and footer elements outside React's container.
Only known, integration-specific IDs are managed by `adLifecycle.js`; unrelated
iframes and consent UI must not be removed. Keep the provider's native close
controls; the footer also has an accessible site close button.

Verification must distinguish these outcomes:

1. Slot is active in `/api/ad-slots/active`.
2. The provider tag and target container exist once on the actual page.
3. A rendered creative is visibly present and fits the viewport.
4. Paid fill and revenue are separate provider-account outcomes. A provider
   house advertisement proves rendering, not a paid campaign or revenue.

Keep the existing externally served `/ads.txt`; do not replace it with a sample.
Local tests must not execute production advertising tags on localhost or click
ads. The publisher guide prohibits placing the same format ID twice per page.

Provider references:
- https://de.themoneytizer.com/faq/passen-die-formate-von-the-moneytizer-fr-mobile-gerte
- https://us.themoneytizer.com/publisherguide
