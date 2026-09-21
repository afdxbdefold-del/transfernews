"""Editorial eligibility is separate from the probability that a transfer happens."""
from urllib.parse import urlsplit

from pipeline_state import review_reason
from story_engine import SOURCE_WEIGHTS, PUBLISH_THRESHOLD_CONFIDENCE


PIPELINE_VERSION = "20260921_source_grounded_v2"
RECONSIDER_REASONS = (
    "unresolved_entities", "ambiguous_players", "ambiguous_clubs",
    "ambiguous_transfer_direction", "missing_transfer_context",
)

# A display name alone must never establish publisher provenance.
PUBLISHER_DOMAINS = {
    "BBC Sport": ("bbc.com", "bbc.co.uk"),
    "Sky Sports": ("skysports.com",),
    "CaughtOffside": ("caughtoffside.com",),
    "90min": ("90min.com",),
    "FootballTransfers": ("footballtransfers.com",),
    "Goal": ("goal.com",),
    "TEAMtalk": ("teamtalk.com",),
    "Marca": ("marca.com",),
    "AS": ("as.com",),
    "Mundo Deportivo": ("mundodeportivo.com",),
    "Gazzetta dello Sport": ("gazzetta.it",),
    "Corriere dello Sport": ("corrieredellosport.it",),
    "Tuttosport": ("tuttosport.com",),
    "L'Équipe": ("lequipe.fr",),
    "RMC Sport": ("rmcsport.bfmtv.com",),
    "Foot Mercato": ("footmercato.net",),
    "BILD": ("bild.de",),
    "kicker": ("kicker.de",),
    "Sport1": ("sport1.de",),
}


def editorial_eligibility(event, story):
    """Allow an attributed report, without upgrading its transfer likelihood."""
    if review_reason(event):
        return False, "source_not_fresh"
    if event.get("entity_confidence") != 1.0:
        return False, "unverified_entities"
    name = event.get("source_name", "")
    try:
        parsed = urlsplit(event.get("source_url", ""))
        host = (parsed.hostname or "").lower()
        if parsed.scheme not in {"https", "http"} or parsed.username or parsed.password:
            return False, "invalid_source_url"
    except (ValueError, TypeError):
        return False, "invalid_source_url"
    domains = PUBLISHER_DOMAINS.get(name, ())
    if not any(host == domain or host.endswith("." + domain) for domain in domains):
        return False, "unverified_publisher"
    if story.get("confidence_score", 0) >= PUBLISH_THRESHOLD_CONFIDENCE:
        return True, "qualified_transfer_report"
    if SOURCE_WEIGHTS.get(name, {}).get("trust", 0) >= 7.5:
        return True, "attributed_single_source_report"
    return False, "insufficient_source_support"


def can_publish_rewrite(article):
    """Only the current, explicitly eligible automatic draft can be promoted."""
    if article.get("status") != "draft" or article.get("duplicate_of") or article.get("review_reason"):
        return False
    if article.get("publication_policy_version") != PIPELINE_VERSION or not article.get("auto_publish_eligible"):
        return False
    if not article.get("source_grounded") or not article.get("source_headline"):
        return False
    eligible, _ = editorial_eligibility(article, article)
    return eligible
