"""Validate and apply exact source spans selected by the offline evidence gate."""
from copy import deepcopy
from source_rewrite_checks import confirmed_french_renewal


def apply_evidence_scope(event, evidence):
    """Return a local source copy; original imported records are never rewritten.

    Claim extraction may isolate complete statements from surrounding RSS context.
    Only byte-for-byte source substrings can enter the downstream story and rewrite.
    """
    scoped = dict(event)
    # Imported/legacy fields are not a proof produced by this invocation.
    for key in ("verified_stage", "evidence_spans", "original_source_headline"):
        scoped.pop(key, None)
    scope = evidence.get("evidence_scope", "full")
    scoped["evidence_scope"] = scope
    if scope == "claim":
        sources = {"headline": event.get("title", ""), "summary": event.get("summary", "")}
        spans = evidence.get("evidence_spans")
        if not isinstance(spans, list) or not 1 <= len(spans) <= 3:
            raise ValueError("invalid_source_claim_spans")
        selected = []
        for span in spans:
            if not isinstance(span, dict):
                raise ValueError("invalid_source_claim_span")
            field, start, end, text = (span.get(key) for key in ("field", "start", "end", "text"))
            original = sources.get(field) if isinstance(field, str) else None
            if (not isinstance(original, str) or type(start) is not int or type(end) is not int
                    or not 0 <= start < end <= len(original) or original[start:end] != text):
                raise ValueError("unverifiable_source_claim_span")
            selected.append(text)
        claim = "\n".join(selected)
        if claim != evidence.get("evidence_headline") or not claim.strip():
            raise ValueError("unverifiable_source_claim_text")
        scoped["original_source_headline"] = event.get("title", "")
        scoped["evidence_spans"] = deepcopy(spans)
        scoped["title"] = scoped["headline_raw"] = claim
        stage = evidence.get("verified_stage")
        if stage is not None:
            if stage not in {"rumor", "advanced", "near_done", "done", "official"}:
                raise ValueError("invalid_source_claim_stage")
            scoped["verified_stage"] = stage
    elif scope not in {"full", "headline"}:
        raise ValueError("invalid_source_evidence_scope")
    elif (scope == "full" and evidence.get("transfer_type") == "extension"
          and confirmed_french_renewal(event.get("title"), event.get("summary"),
                                       evidence.get("player"), evidence.get("club"))):
        scoped["verified_stage"] = "official"
    if scope in {"headline", "claim"}:
        scoped.update(summary="", body_raw="", summary_raw="")
    return scoped
