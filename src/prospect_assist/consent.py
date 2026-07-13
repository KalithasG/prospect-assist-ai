"""Consent tokens: server-side scope + expiry enforcement.

Scoring is blocked (HTTP 403 at the API layer) before any connector call is
made if the token is missing, expired, or lacks a *base* scope. Optional
scopes (upi, gst, alt_data) practice consent minimization: the orchestrator
simply skips those data sources instead of failing the whole request.
"""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

CONSENT_TTL_HOURS = 24
# Base scopes without which scoring cannot proceed at all.
REQUIRED_SCOPES = {"transactions", "bureau"}
# Scopes that unlock optional data sources; absence degrades gracefully.
OPTIONAL_SCOPES = {"upi", "gst", "alt_data"}


class ConsentService:
    def __init__(self) -> None:
        self._tokens: dict[str, dict] = {}

    def grant(self, customer_id: str, scope: list[str],
              ttl_hours: float = CONSENT_TTL_HOURS) -> dict:
        token = secrets.token_urlsafe(24)
        expires = datetime.now(timezone.utc) + timedelta(hours=ttl_hours)
        self._tokens[token] = {"customer_id": customer_id, "scope": set(scope),
                               "expires_at": expires}
        return {"consent_token": token, "expires_at": expires.isoformat()}

    def revoke(self, token: str) -> bool:
        return self._tokens.pop(token, None) is not None

    def validate(self, token: str | None, customer_id: str,
                 required: set[str] = REQUIRED_SCOPES) -> bool:
        if not token or token not in self._tokens:
            return False
        rec = self._tokens[token]
        if rec["customer_id"] != customer_id:
            return False
        if datetime.now(timezone.utc) >= rec["expires_at"]:
            self._tokens.pop(token, None)
            return False
        return required.issubset(rec["scope"])

    def scopes(self, token: str | None) -> set[str]:
        """Granted scopes for a live token (empty set if unknown/expired)."""
        rec = self._tokens.get(token or "")
        if not rec or datetime.now(timezone.utc) >= rec["expires_at"]:
            return set()
        return set(rec["scope"])
