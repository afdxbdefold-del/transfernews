"""Allowlisted OpenAI failures and persistent, operator-released rewrite stops.

Never retain exception messages, response bodies, request headers or API keys.
See https://developers.openai.com/api/docs/guides/error-codes.
"""
from dataclasses import dataclass
from datetime import timedelta
from email.utils import parsedate_to_datetime
import math
import random
from uuid import uuid4

from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
from pipeline_state import parse_source_time, utcnow


PROVIDER_ID = "openai_rewrite"
BILLING_CODES = frozenset({
    "credit_balance_exhausted", "organization_spend_limit_exceeded",
    "project_spend_limit_exceeded", "organization_usage_limit_exceeded",
    "insufficient_quota", "usage_limit_exceeded",
})
AUTH_CODES = frozenset({"invalid_api_key", "authentication_error", "permission_denied",
                        "ip_not_authorized", "account_deactivated"})
TRANSIENT_CODES = frozenset({"rate_limit_exceeded", "slow_down", "server_is_overloaded",
                             "server_overloaded", "server_error"})


@dataclass(frozen=True)
class RewriteFailure:
    code: str
    kind: str
    blocked: bool
    http_status: int | None = None
    retry_after: float = 0


class RewriteProviderError(Exception):
    def __init__(self, state):
        self.state = state
        super().__init__(state["error_code"])


def _retry_after(exc, now):
    headers = getattr(getattr(exc, "response", None), "headers", {}) or {}
    value = headers.get("retry-after")
    try:
        delay = float(value)
    except (TypeError, ValueError):
        try:
            when = parse_source_time(parsedate_to_datetime(value))
            delay = (when - now).total_seconds()
        except (TypeError, ValueError, OverflowError, AttributeError):
            return 0
    # Absurd/unrepresentable delays are never scheduled; they require review.
    return delay if math.isfinite(delay) and delay > 0 else 0


def classify_rewrite_error(exc, now=None):
    """Read only the SDK's structured code/type/status and Retry-After header."""
    now = now or utcnow()
    status = getattr(exc, "status_code", None)
    status = status if type(status) is int and 100 <= status <= 599 else None
    code = getattr(exc, "code", None)
    code = code if isinstance(code, str) else None
    if code in BILLING_CODES or getattr(exc, "type", None) == "insufficient_quota":
        return RewriteFailure(code if code in BILLING_CODES else "insufficient_quota", "billing", True, status)
    if code in AUTH_CODES or status in (401, 403):
        return RewriteFailure(code if code in AUTH_CODES else "provider_access_denied", "authentication", True, status)
    delay = _retry_after(exc, now)
    if delay > 365 * 86400:
        return RewriteFailure("invalid_retry_after", "configuration", True, status)
    if status == 429 or code in {"rate_limit_exceeded", "slow_down"}:
        # A 429 without a recognized subtype cannot safely be assumed transient.
        if code not in TRANSIENT_CODES:
            return RewriteFailure("unclassified_rate_limit", "rate_limit", True, status)
        return RewriteFailure(code, "rate_limit", False, status, delay)
    if status is not None and (status >= 500 or status in (408, 409)):
        return RewriteFailure(code if code in TRANSIENT_CODES else "provider_unavailable", "upstream", False, status, delay)
    name = type(exc).__name__
    if isinstance(exc, TimeoutError) or name in {"APITimeoutError", "ReadTimeout", "ConnectTimeout"}:
        return RewriteFailure("provider_timeout", "timeout", False, status, delay)
    if name in {"APIConnectionError", "ConnectError", "ReadError"}:
        return RewriteFailure("provider_connection_error", "connection", False, status, delay)
    if status is not None and 400 <= status < 500:
        return RewriteFailure("provider_request_rejected", "configuration", True, status)
    return None


def rewrite_provider_pause(state, now=None):
    now = now or utcnow()
    if not state:
        return None
    if state.get("status") == "blocked":
        return state
    retry_at = parse_source_time(state.get("retry_at"))
    if state.get("status") == "retry" and retry_at and retry_at > now:
        return state
    return None


async def get_rewrite_provider_pause(db, now=None):
    state = await db.rewrite_provider_state.find_one({"_id": PROVIDER_ID})
    return rewrite_provider_pause(state, now)


async def _compare_provider_state(db, current, update):
    """Unique insert or exact-state CAS; no upsert equality-field inference."""
    try:
        if current is None:
            initial = {"_id": PROVIDER_ID, **update["$set"], "state_revision": 1}
            await db.rewrite_provider_state.insert_one(initial)
            return initial
        selector = {"_id": PROVIDER_ID, "state_revision": current.get("state_revision"),
                    "status": current.get("status")}
        return await db.rewrite_provider_state.find_one_and_update(
            selector, {**update, "$inc": {"state_revision": 1}}, return_document=ReturnDocument.AFTER)
    except DuplicateKeyError:
        return None


async def record_rewrite_provider_success(db, expected_state):
    """A late response may only clear the state observed before its API call."""
    if expected_state and expected_state.get("status") == "blocked":
        return False
    updated = await _compare_provider_state(db, expected_state, {
        "$set": {"status": "ready", "consecutive_failures": 0, "updated_at": utcnow()},
        "$unset": {"retry_at": "", "error_code": "", "error_kind": "", "http_status": ""},
    })
    return updated is not None


async def record_rewrite_provider_failure(db, failure, now=None):
    """CAS also protects outer timeout/configuration writes without a lease."""
    now = now or utcnow()
    for _ in range(8):
        current = await db.rewrite_provider_state.find_one({"_id": PROVIDER_ID})
        if current and current.get("status") == "blocked":
            return current
        attempts = int((current or {}).get("consecutive_failures", 0)) + 1
        fields = {"error_code": failure.code, "error_kind": failure.kind,
                  "http_status": failure.http_status, "updated_at": now,
                  "consecutive_failures": attempts}
        if failure.blocked or attempts >= 5:
            fields.update(status="blocked", blocked_at=now, block_id=uuid4().hex)
            if not failure.blocked:
                fields["retry_exhausted"] = True
        else:
            delay = max(failure.retry_after, min(3600, 60 * 2 ** (attempts - 1)))
            retry_at = now + timedelta(seconds=delay + random.uniform(0, 15))
            existing_retry = parse_source_time((current or {}).get("retry_at"))
            fields.update(status="retry", retry_at=max(retry_at, existing_retry) if existing_retry else retry_at)
        update = {"$set": fields}
        if fields["status"] == "blocked":
            update["$unset"] = {"retry_at": ""}
        updated = await _compare_provider_state(db, current, update)
        if updated is not None:
            return updated
    raise RuntimeError("provider_state_conflict")


async def resume_rewrite_provider(db, *, expected_block_id, operator_confirmed=False):
    """Explicit compare-and-set release only; never requeue historical articles.

    The operator must first resolve billing/credentials and select fresh work
    through the existing editorial pipeline. No API probe is performed here.
    """
    if operator_confirmed is not True or not isinstance(expected_block_id, str) or not expected_block_id:
        raise ValueError("operator_confirmation_and_block_id_required")
    result = await db.rewrite_provider_state.update_one(
        {"_id": PROVIDER_ID, "status": "blocked", "block_id": expected_block_id},
        {"$set": {"status": "ready", "updated_at": utcnow(), "operator_released_at": utcnow(),
                  "consecutive_failures": 0},
         "$unset": {"error_code": "", "error_kind": "", "http_status": "", "blocked_at": "",
                    "block_id": "", "retry_at": "", "retry_exhausted": ""},
         "$inc": {"state_revision": 1}},
    )
    return {"resumed": bool(result.matched_count), "requeued_articles": 0}
