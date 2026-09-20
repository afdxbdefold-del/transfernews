"""Authentication primitives. No embedded or automatically generated signing keys."""
import os
import hashlib
import time
from collections import OrderedDict, deque
from pathlib import Path
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from fastapi import HTTPException
from pydantic import BaseModel, Field, field_validator

ISSUER = "transfernews.de"
AUDIENCE = "transfernews-admin"
ALGORITHM = "HS256"


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=16, max_length=72)

    @field_validator("new_password")
    @classmethod
    def bcrypt_byte_limit(cls, value):
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Passwort darf höchstens 72 UTF-8-Bytes enthalten")
        return value


class LoginAttemptLimiter:
    """Bounded per-process account/IP protection; no credentials stored in the buckets."""
    def __init__(self, window=300, account_limit=10, ip_limit=120):
        self.window, self.account_limit, self.ip_limit = window, account_limit, ip_limit
        self.buckets = OrderedDict()

    def _account_key(self, email):
        return "account:" + hashlib.sha256(email.strip().lower().encode()).hexdigest()

    def check(self, email, peer, now=None):
        now = time.monotonic() if now is None else now
        for key, limit in ((self._account_key(email), self.account_limit), ("peer:" + peer, self.ip_limit)):
            bucket = self.buckets.setdefault(key, deque())
            self.buckets.move_to_end(key)
            while bucket and bucket[0] <= now - self.window:
                bucket.popleft()
            if len(bucket) >= limit:
                raise HTTPException(429, "Zu viele Anmeldeversuche. Bitte später erneut versuchen.", headers={"Retry-After": str(self.window)})
            bucket.append(now)
        while len(self.buckets) > 4096:
            self.buckets.popitem(last=False)

    def success(self, email):
        self.buckets.pop(self._account_key(email), None)


def load_jwt_secret(environ=None):
    environ = os.environ if environ is None else environ
    secret_file = environ.get("JWT_SECRET_FILE", "").strip()
    if secret_file:
        try:
            secret = Path(secret_file).read_text(encoding="utf-8").strip()
        except (OSError, UnicodeError) as exc:
            raise RuntimeError("JWT_SECRET_FILE must contain a readable signing key") from None
    else:
        secret = environ.get("JWT_SECRET_KEY", "").strip()
    if (len(secret.encode("utf-8")) < 32 or len(set(secret)) < 12
            or any(marker in secret.lower() for marker in ("change-me", "changeme", "your-secret", "placeholder"))):
        raise RuntimeError("A strong signing key is required via JWT_SECRET_FILE or JWT_SECRET_KEY")
    return secret


def issue_token(secret, user_id, email, role, lifetime_hours=24, auth_version=0):
    now = datetime.now(timezone.utc)
    return jwt.encode({
        "sub": user_id, "email": email, "role": role,
        "iat": now, "exp": now + timedelta(hours=lifetime_hours),
        "iss": ISSUER, "aud": AUDIENCE, "jti": str(uuid4()),
        "auth_version": auth_version,
    }, secret, algorithm=ALGORITHM)


async def authenticate_token(token, secret, database):
    try:
        payload = jwt.decode(token, secret, algorithms=[ALGORITHM], issuer=ISSUER,
                             audience=AUDIENCE, options={"require": ["sub", "exp", "iat", "iss", "aud", "jti", "auth_version"]})
        if not isinstance(payload["sub"], str) or not payload["sub"]:
            raise jwt.InvalidTokenError()
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Ungültige oder abgelaufene Sitzung", headers={"WWW-Authenticate": "Bearer"}) from None
    user = await database.users.find_one({"id": payload["sub"]}, {"_id": 0, "password_hash": 0})
    if not user or not user.get("is_active", False):
        raise HTTPException(401, "Sitzung nicht mehr gültig", headers={"WWW-Authenticate": "Bearer"})
    if payload["auth_version"] != user.get("auth_version", 0):
        raise HTTPException(401, "Sitzung wurde widerrufen", headers={"WWW-Authenticate": "Bearer"})
    role = user.get("role")
    if role not in {"admin", "editor", "author"}:
        raise HTTPException(403, "Keine redaktionelle Berechtigung")
    # Authorization comes from current DB state, never stale token role/email claims.
    return {"sub": user["id"], "email": user.get("email", ""), "role": role, "auth_version": user.get("auth_version", 0)}
