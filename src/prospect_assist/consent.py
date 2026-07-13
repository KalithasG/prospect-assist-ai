"""Consent tokens: server-side scope + expiry enforcement (spec §21.5, §15.4).

Scoring is blocked (HTTP 403 at the API layer) before any connector call is
made if the token is missing, expired, or lacks a required scope.
"""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

CONSENT_TTL_HOURS = 24
REQUIRED_SCOPES = {"transactions", "upi", "bureau"}


class ConsentService:
    def __init__(self) -> None:
        self._tokens: dict[str, dict] = {}

    def grant(self, customer_id: str, scope: list[str]) -> dict:
        token = secrets.token_urlsafe(24)
        expires = datetime.now(timezone.utc) + timedelta(hours=CONSENT_TTL_HOURS)
        self._tokens[token] = {"customer_id": customer_id, "scope": set(scope),
                               "expires_at": expires}
        return {"consent_token": token, "expires_at": expires.isoformat()}

    def revoke(self, token: str) -> None:
        self._tokens.pop(token, None)

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
