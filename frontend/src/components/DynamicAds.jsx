import { FreestarSlot } from './FreestarAds';
// Compatibility for editorial insertion points. Stored legacy advertising
// snippets are intentionally no longer executed on public pages.
const placement = {
  top_banner_above_header: 'leaderboard_1', footer_top: 'leaderboard_2',
  sidebar_top: 'incontent_4', sidebar_middle: 'incontent_5', sidebar_bottom: 'incontent_6',
  article_below_excerpt: 'incontent_1', article_after_paragraph_1: 'incontent_2',
  article_after_paragraph_2: 'incontent_3', article_before_related: 'incontent_2', article_after_related: 'incontent_3',
  listing_after_card_5: 'incontent_1', listing_after_card_10: 'incontent_2', listing_after_card_15: 'incontent_3',
};
export default function DynamicAdSlot({ slotKey }) { return <FreestarSlot name={placement[slotKey]} />; }
