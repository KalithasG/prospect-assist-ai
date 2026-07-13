"""Phase-1 MockSandboxConnector (spec §18.1): serves the synthetic store.

`simulate_outage` supports the graceful-degradation BDD scenario; `call_count`
lets tests assert that no data is fetched when consent is invalid.
"""
from __future__ import annotations

from .base import BankDataConnector, ConnectorUnavailable
from ..store import InMemoryStore


class MockSandboxConnector(BankDataConnector):
    def __init__(self, store: InMemoryStore) -> None:
        self.store = store
        self.simulate_outage = False
        self.call_count = 0

    def _guard(self) -> None:
        if self.simulate_outage:
            raise ConnectorUnavailable("Upstream data connector unavailable")
        self.call_count += 1

    def get_account_transactions(self, customer_id, date_range=None):
        self._guard()
        return list(self.store.transactions.get(customer_id, []))

    def get_upi_transactions(self, customer_id, date_range=None):
        self._guard()
        return [t for t in self.store.transactions.get(customer_id, [])
                if t.get("channel") == "upi"]

    def get_secondary_bank_statements(self, customer_id):
        self._guard()
        return list(self.store.secondary_statements.get(customer_id, []))

    def get_gst_summary(self, business_id):
        self._guard()
        return self.store.gst.get(business_id)

    def get_bureau_summary(self, customer_id):
        self._guard()
        return self.store.bureau.get(customer_id)

    def get_digital_engagement_log(self, customer_id):
        self._guard()
        return list(self.store.engagement.get(customer_id, []))

    def get_alt_data_proxies(self, customer_id):
        self._guard()
        return self.store.alt_data.get(customer_id)
