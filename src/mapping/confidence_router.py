from pathlib import Path
from typing import Any

import pandas as pd


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "mappings"
    / "collision_results.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "mappings"
    / "confidence_routing.csv"
)


# ============================================================
# THRESHOLDS
# ============================================================

AUTO_APPROVE_THRESHOLD = 0.90
HUMAN_ESCALATION_THRESHOLD = 0.70


# ============================================================
# WEIGHTS
# ============================================================
#
# Vector score = retrieval confidence
# Gemini score = semantic reasoning confidence
#
# Collision is treated as a hard governance signal.
# ============================================================

VECTOR_WEIGHT = 0.40
GEMINI_WEIGHT = 0.60


# ============================================================
# LOAD RESULTS
# ============================================================

if not INPUT_FILE.exists():
    raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")

df: Any = pd.read_csv(
    INPUT_FILE
)


# ============================================================
# CONFIDENCE FUNCTION
# ============================================================

def calculate_confidence(row: dict[str, Any]) -> float:

    vector_score = float(
        row["top_vector_score"]
    )

    gemini_score = float(
        row["semantic_score"]
    )

    base_score = (
        vector_score * VECTOR_WEIGHT
        +
        gemini_score * GEMINI_WEIGHT
    )

    # --------------------------------------------------------
    # Hard penalty for semantic collision
    # --------------------------------------------------------

    if bool(row["collision"]):
        return min(
            base_score,
            0.49
        )

    # --------------------------------------------------------
    # Gemini already requested REVIEW
    # --------------------------------------------------------

    if row["action"] == "REVIEW":
        return min(
            base_score,
            0.69
        )

    return round(
        base_score,
        4
    )


# ============================================================
# ROUTING FUNCTION
# ============================================================

def route_mapping(row: dict[str, Any]) -> str:

    score = row[
        "final_confidence"
    ]

    # Semantic collision always escalates.
    if bool(row["collision"]):

        return "HUMAN_ESCALATION"

    # New ontology concepts require human governance.
    if row["action"] == "CREATE_NEW":

        return "HUMAN_ESCALATION"

    if score >= AUTO_APPROVE_THRESHOLD:

        return "AUTO_APPROVE"

    elif score >= HUMAN_ESCALATION_THRESHOLD:

        return "SOFT_REVIEW"

    else:

        return "HUMAN_ESCALATION"


# ============================================================
# CALCULATE
# ============================================================

df["final_confidence"] = df.apply(
    calculate_confidence,
    axis=1,
)

df["routing_decision"] = df.apply(
    route_mapping,
    axis=1,
)


# ============================================================
# SAVE
# ============================================================

df.to_csv(
    OUTPUT_FILE,
    index=False,
)


# ============================================================
# SUMMARY
# ============================================================

summary = (
    df["routing_decision"]
    .value_counts()
)


print("\n")
print("=" * 65)
print("GSIS STAGE 11 - CONFIDENCE ROUTING")
print("=" * 65)

print(
    df[
        [
            "incoming_term",
            "recommended_concept",
            "top_vector_score",
            "semantic_score",
            "final_confidence",
            "routing_decision",
        ]
    ].to_string(
        index=False
    )
)

print("\nRouting Summary:")

for decision, count in summary.items():

    print(
        f"{decision}: {count}"
    )


print(
    f"\nSaved to:\n{OUTPUT_FILE}"
)