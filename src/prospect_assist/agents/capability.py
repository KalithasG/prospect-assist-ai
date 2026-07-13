"""CapabilityAgent (Layer 3, spec §9 + §19): "Can they repay?"

Segment-specific income estimation with explicit confidence, surplus math per
§9.2, and NTC alt-data fallback. Never guesses past its confidence floor —
the orchestrator's gate handles low-confidence routing.
"""
from __future__ import annotations

from ..config import GIG_DISCOUNT_FACTOR, INDUSTRY_MARGINS


class InsufficientSignal(Exception):
    """Thin file with no proxy data — API surfaces HTTP 422."""


# NTC alt-data regression, calibrated on Phase-1 synthetic personas (§19):
# income ≈ ELEC_COEF·electricity_units + FUEL_COEF·fuel_spend
ELEC_COEF = 90.0
FUEL_COEF = 2.2


class CapabilityAgent:
    def assess(self, segment: str, features: dict, gst: dict | None,
               alt_data: dict | None) -> dict:
        if segment == "salaried" and features["monthly_salary_median"] > 0:
            return self._salaried(features)
        if segment == "gig_self_employed" and (
                features["monthly_gig_income_avg"] > 0 or gst):
            return self._gig(features, gst)
        return self._ntc(features, alt_data)

    # -- strategies ---------------------------------------------------------
    def _salaried(self, f: dict) -> dict:
        income = f["monthly_salary_median"]
        confident = f["salary_regularity"] >= 0.5 and f["salary_day_consistent"]
        conf = 0.9 if confident else 0.65
        out = self._finish("salaried", income, f, conf,
                           "High" if confident else "Medium")
        out["signals"].insert(0, (
            f"Stable salary credits of ₹{income:,.0f}/month "
            f"({f['salary_regularity']:.0%} of months, consistent credit date)"))
        return out

    def _gig(self, f: dict, gst: dict | None) -> dict:
        upi_estimate = f["monthly_gig_income_avg"] * GIG_DISCOUNT_FACTOR
        gst_estimate = 0.0
        if gst and gst.get("gst_turnover_annual"):
            margin = INDUSTRY_MARGINS.get(gst.get("industry_code", "default"),
                                          INDUSTRY_MARGINS["default"])
            gst_estimate = gst["gst_turnover_annual"] / 12 * margin
        income = max(upi_estimate, gst_estimate)
        if income <= 0:
            raise InsufficientSignal("No gig/GST income signal")
        out = self._finish("gig_self_employed", income, f, 0.65, "Medium")
        out["signals"].insert(0, (
            f"Gig/UPI platform credits averaging ₹{f['monthly_gig_income_avg']:,.0f}"
            f"/month across {f['gig_platform_diversity']} platform(s); conservative "
            f"{GIG_DISCOUNT_FACTOR:.0%} discount applied"))
        if gst_estimate:
            out["signals"].append(
                f"GST turnover ₹{gst['gst_turnover_annual']:,.0f}/yr × industry "
                f"margin cross-check: ₹{gst_estimate:,.0f}/month")
        return out

    def _ntc(self, f: dict, alt_data: dict | None) -> dict:
        has_alt = alt_data and (alt_data.get("electricity_avg_monthly_units")
                                or alt_data.get("fuel_spend_monthly"))
        if not has_alt and not f["has_transactions"]:
            raise InsufficientSignal(
                "Insufficient signal to score — thin-file, no proxy data available")
        elec = (alt_data or {}).get("electricity_avg_monthly_units") or 0
        fuel = (alt_data or {}).get("fuel_spend_monthly") or 0
        income = ELEC_COEF * elec + FUEL_COEF * fuel
        if income <= 0 and f["monthly_income_avg"] > 0:
            income = f["monthly_income_avg"] * 0.7
        if income <= 0:
            raise InsufficientSignal(
                "Insufficient signal to score — thin-file, no proxy data available")
        out = self._finish("new_to_credit", income, f, 0.45, "Low",
                           essential_ratio_fallback=0.60)
        out["signals"].insert(0, (
            f"Alt-data proxy estimation: electricity {elec:,.0f} units/mo, fuel "
            f"₹{fuel:,.0f}/mo → inferred income ₹{income:,.0f}/month (low confidence)"))
        return out

    # -- shared surplus math (spec §9.2) -------------------------------------
    def _finish(self, strategy: str, income: float, f: dict, conf: float,
                conf_label: str, essential_ratio_fallback: float = 0.0) -> dict:
        essentials = f["avg_essential"]
        savings_commit = f["avg_investment"]
        if essentials == 0 and essential_ratio_fallback:
            essentials = income * essential_ratio_fallback
        surplus = max(0.0, income - essentials - savings_commit)
        safe_emi = surplus * 0.60
        foir = ((f["avg_rent"] + f["avg_emi"] + f["avg_insurance"]
                 + f["avg_utilities"]) / income) if income else 1.0
        retained = ((savings_commit) / income) if income else None
        # PVAF at 8.5% for 20y for headline max-loan figure (spec §9.2 example)
        r, n = 0.085 / 12, 240
        pvaf = (1 - (1 + r) ** -n) / r
        return {
            "strategy": strategy,
            "estimated_income": round(income, 2),
            "disposable_surplus": round(surplus, 2),
            "safe_emi_capacity": round(safe_emi, 2),
            "max_loan_eligibility": round(safe_emi * pvaf, -3),
            "foir": round(min(foir, 1.0), 3),
            "income_stability": f["income_stability"],
            "savings_discipline_score": round(f["sip_consistency"], 2),
            "retained_money_ratio": (round(retained, 3)
                                     if retained is not None else None),
            "confidence": conf,
            "income_confidence": conf_label,
            "signals": [],
            "affordability_breakdown": {
                "estimated_monthly_income": round(income, 2),
                "existing_emi": round(f["avg_emi"], 2),
                "rent": round(f["avg_rent"], 2),
                "insurance": round(f["avg_insurance"], 2),
                "utilities": round(f["avg_utilities"], 2),
                "minimum_living": round(f["avg_living"] + f["avg_fuel"], 2),
                "medical_education": round(
                    max(0.0, f["avg_essential"] - f["avg_rent"] - f["avg_emi"]
                        - f["avg_insurance"] - f["avg_utilities"]
                        - f["avg_living"] - f["avg_fuel"]), 2),
                "mandatory_savings": round(savings_commit, 2),
                "monthly_surplus": round(surplus, 2),
                "safe_emi_capacity": round(safe_emi, 2),
            },
        }
