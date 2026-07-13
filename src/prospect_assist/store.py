"""Phase-1 persistence: in-memory store seeded from JSON fixtures.

Mirrors the relational schema in spec Appendix A. Swapped for PostgreSQL 16 in
Phase 2 without touching agents (they only see the connector interface, §16).
"""
from __future__ import annotations

import uuid
from collections import defaultdict
from typing import Any


class InMemoryStore:
    def __init__(self) -> None:
        self.customers: dict[str, dict] = {}
        self.transactions: dict[str, list[dict]] = defaultdict(list)
        self.bureau: dict[str, dict] = {}
        self.engagement: dict[str, list[dict]] = defaultdict(list)
        self.alt_data: dict[str, dict] = {}
        self.gst: dict[str, dict] = {}
        self.secondary_statements: dict[str, list[dict]] = defaultdict(list)
        self.lead_scores: dict[str, list[dict]] = defaultdict(list)
        self.feedback: list[dict] = []
        self.batch_jobs: dict[str, dict] = {}

    # -- writes -----------------------------------------------------------
    def add_customer(self, row: dict) -> None:
        self.customers[row["customer_id"]] = row

    def add_transaction(self, row: dict) -> None:
        row.setdefault("txn_id", str(uuid.uuid4()))
        self.transactions[row["customer_id"]].append(row)

    def set_bureau(self, cid: str, row: dict) -> None:
        self.bureau[cid] = {"customer_id": cid, **row}

    def add_engagement(self, cid: str, row: dict) -> None:
        row.setdefault("session_id", str(uuid.uuid4()))
        self.engagement[cid].append({"customer_id": cid, **row})

    def set_alt_data(self, cid: str, row: dict) -> None:
        self.alt_data[cid] = {"customer_id": cid, **row}

    def set_gst(self, cid: str, row: dict) -> None:
        self.gst[cid] = {"customer_id": cid, **row}

    def add_secondary_statement(self, row: dict) -> None:
        row.setdefault("txn_id", str(uuid.uuid4()))
        self.secondary_statements[row["customer_id"]].append(row)

    def save_lead(self, cid: str, lead: dict) -> None:
        self.lead_scores[cid].append(lead)

    def record_feedback(self, row: dict) -> None:
        self.feedback.append(row)

    # -- reads ------------------------------------------------------------
    def get_leads(self, cid: str) -> list[dict]:
        return list(self.lead_scores.get(cid, []))

    def all_leads(self) -> list[dict]:
        return [l for leads in self.lead_scores.values() for l in leads]
