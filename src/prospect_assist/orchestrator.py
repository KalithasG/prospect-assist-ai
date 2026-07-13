"""ProspectAssistOrchestrator (spec §15).

Pattern: Goal → Plan → Execute (agents) → Reflect (contradiction /
low-confidence check) → Evaluate (threshold gate) → Publish or Recheck.
The system never guesses past its own confidence floor into an unqualified
"serious" label; consent is validated before any connector call.
"""
from __future__ import annotations

from datetime import datetime

from .config import (ANCHOR_DATE, DELINQUENCY_FLAG_THRESHOLD,
                     MAX_RECURSION_DEPTH_PER_LEAD, NTC_CONFIDENCE_FLOOR,
                     PRODUCTS)
from .connectors.base import BankDataConnector, ConnectorUnavailable
from .consent import ConsentService
from .agents.transaction_parser import TransactionParserAgent
from .agents.capability import CapabilityAgent, InsufficientSignal
from .agents.intent import IntentAgent
from .agents.scoring import (ConversionPropensityAgent, DelinquencyRiskAgent,
                             EligibilityEngine, EvidenceCompilerAgent)


class ConsentError(Exception):
    """Consent not granted or expired — API surfaces HTTP 403."""


class ProspectAssistOrchestrator:
    ConsentError = ConsentError
    ConnectorUnavailable = ConnectorUnavailable
    InsufficientSignal = InsufficientSignal

    def __init__(self, connector: BankDataConnector,
                 consent_service: ConsentService) -> None:
        self.connector = connector
        self.consent = consent_service
        self.parser = TransactionParserAgent()
        self.capability = CapabilityAgent()
        self.intent = IntentAgent()
        self.delinquency = DelinquencyRiskAgent()
        self.eligibility = EligibilityEngine()
        self.conversion = ConversionPropensityAgent()
        self.evidence = EvidenceCompilerAgent()

    # ------------------------------------------------------------------
    def score(self, customer_id: str, product: str,
              consent_token: str | None, segment: str | None = None) -> dict:
        if product not in PRODUCTS:
            raise ValueError(f"Unknown product '{product}'")
        # Gate 0 — consent BEFORE any data fetch (spec §20, §21.5)
        if not self.consent.validate(consent_token, customer_id):
            raise ConsentError("Consent not granted or expired")

        # Plan + Execute
        txns = self.connector.get_account_transactions(customer_id)
        bureau = self.connector.get_bureau_summary(customer_id)
        engagement = self.connector.get_digital_engagement_log(customer_id)
        gst = self.connector.get_gst_summary(customer_id)
        alt = self.connector.get_alt_data_proxies(customer_id)
        segment = segment or self._infer_segment(customer_id, txns, gst, bureau)

        features = self.parser.extract(txns)
        retries = 0
        cap = None
        while retries < MAX_RECURSION_DEPTH_PER_LEAD:
            cap = self.capability.assess(segment, features, gst, alt)
            # Recheck path (a): retry with NTC proxy strategy on very low
            # confidence for a non-NTC segment (spec §15.3)
            if cap["confidence"] < 0.4 and segment != "new_to_credit" and alt:
                segment, retries = "new_to_credit", retries + 1
                continue
            break

        intent = self.intent.detect(product, features, engagement, bureau)
        delinq = self.delinquency.score(bureau, features)
        elig = self.eligibility.score(segment, cap, bureau, product)
        conv = self.conversion.score(elig["eligibility_score"],
                                     intent["intent_score"],
                                     self._engagement_recency(engagement))

        # Reflect
        reflection = {"retries": retries, "contradiction_flag": False,
                      "ntc_low_confidence_gate": False,
                      "enhanced_review_flag": False,
                      "thin_file_promotion": False}
        risk = delinq["early_warning_risk_score"]
        if (intent["intent_score"] >= 0.6
                and elig["eligibility_score"] >= 60
                and risk > DELINQUENCY_FLAG_THRESHOLD):
            reflection["contradiction_flag"] = True
        if segment == "new_to_credit" and cap["confidence"] < NTC_CONFIDENCE_FLOOR:
            reflection["ntc_low_confidence_gate"] = True
        thin_file = (bureau is None or bureau.get("bureau_score") is None
                     or not gst)
        if thin_file and segment == "gig_self_employed":
            reflection["enhanced_review_flag"] = True
            retained = cap.get("retained_money_ratio")
            if (retained and retained > 0.25 and cap["disposable_surplus"] > 0
                    and not reflection["contradiction_flag"]
                    and risk <= DELINQUENCY_FLAG_THRESHOLD):
                # Spec §20 final scenario: strong retained savings promotes a
                # thin-file gig lead to "interested" with enhanced review.
                reflection["thin_file_promotion"] = True

        # Evaluate + Publish
        return self.evidence.compile(customer_id, product, segment, cap,
                                     intent, delinq, conv, elig, reflection)

    # ------------------------------------------------------------------
    @staticmethod
    def _infer_segment(customer_id: str, txns: list[dict], gst, bureau) -> str:
        from .agents.transaction_parser import categorize
        cats = {categorize(t) for t in txns if t["direction"] == "credit"}
        if "salary" in cats:
            return "salaried"
        if "gig_income" in cats or gst:
            return "gig_self_employed"
        return "new_to_credit"

    @staticmethod
    def _engagement_recency(engagement: list[dict]) -> float:
        best = 0.0
        for s in engagement:
            days = (ANCHOR_DATE
                    - datetime.fromisoformat(s["session_timestamp"])).days
            if days <= 7:
                best = max(best, 1.0)
            elif days <= 14:
                best = max(best, 0.5)
            elif days <= 30:
                best = max(best, 0.25)
        return best
