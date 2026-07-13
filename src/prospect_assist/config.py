"""Deterministic Phase-1 configuration (spec §13.3, §15.4, §19)."""
from datetime import datetime

# Fixed anchor so synthetic data, recency decay, and evals are reproducible.
ANCHOR_DATE = datetime(2026, 7, 1)

MAX_RECURSION_DEPTH_PER_LEAD = 3
SCORING_TIMEOUT_S = 30

PRODUCTS = ("personal_loan", "home_loan", "mortgage_lap", "auto_loan")

# Spec §13.3 product-specific eligibility rules
PRODUCT_RULES = {
    "personal_loan": {"min_eligibility": 50, "min_income": 25000, "max_foir": 0.50},
    "home_loan":     {"min_eligibility": 60, "min_income": 40000, "max_foir": 0.45},
    "auto_loan":     {"min_eligibility": 55, "min_income": 30000, "max_foir": 0.50},
    "mortgage_lap":  {"min_eligibility": 65, "min_income": 50000, "max_foir": 0.40},
}

# Spec §19 industry margin reference table (static config, versioned)
INDUSTRY_MARGINS = {"retail": 0.18, "services": 0.45, "manufacturing": 0.25,
                    "default": 0.30}

# Spec §9.1.3: gig income conservative discount (platform fees, irregularity)
GIG_DISCOUNT_FACTOR = 0.75

# Spec §10.2 segment adjustment factors
SEGMENT_ADJUSTMENT = {"salaried": 1.00, "gig_self_employed": 0.85,
                      "new_to_credit": 0.90}

TIER_SERIOUS = 0.70
TIER_INTERESTED = 0.50
TIER_QUALITY_WATCH = 0.30
DELINQUENCY_FLAG_THRESHOLD = 0.60
NTC_CONFIDENCE_FLOOR = 0.60
