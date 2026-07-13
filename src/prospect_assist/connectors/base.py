"""Data Source Abstraction Layer (spec §16) — the scalability seam.

Every agent talks to BankDataConnector, never to a concrete data source.
Phase 1 → 2 → 3 is a connector swap chosen by config, with zero changes to
agent logic, scoring, or the public API contract.
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class ConnectorUnavailable(Exception):
    """Upstream data connector unreachable → API surfaces HTTP 503."""


class BankDataConnector(ABC):
    @abstractmethod
    def get_account_transactions(self, customer_id: str,
                                 date_range: tuple | None = None) -> list[dict]: ...

    @abstractmethod
    def get_upi_transactions(self, customer_id: str,
                             date_range: tuple | None = None) -> list[dict]: ...

    @abstractmethod
    def get_secondary_bank_statements(self, customer_id: str) -> list[dict]: ...

    @abstractmethod
    def get_gst_summary(self, business_id: str) -> dict | None: ...

    @abstractmethod
    def get_bureau_summary(self, customer_id: str) -> dict | None: ...

    @abstractmethod
    def get_digital_engagement_log(self, customer_id: str) -> list[dict]: ...

    @abstractmethod
    def get_alt_data_proxies(self, customer_id: str) -> dict | None: ...


def connector_factory(kind: str, **kwargs) -> BankDataConnector:
    """DATA_CONNECTOR=mock|bank_sandbox|bank_production (spec §16.1)."""
    if kind == "mock":
        from .mock import MockSandboxConnector
        return MockSandboxConnector(kwargs["store"])
    raise NotImplementedError(
        f"Connector '{kind}' is a Phase 2/3 implementation: build it against the "
        "real sandbox OpenAPI spec; agents require zero changes (spec §16.1).")
