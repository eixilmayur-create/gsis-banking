from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

GROUND_TRUTH_FILE = (
    PROJECT_ROOT
    / "data"
    / "schemas"
    / "mapping_ground_truth.csv"
)

ROUTING_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "mappings"
    / "confidence_routing.csv"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "evaluation"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# LOAD DATA
# ============================================================

truth_df = pd.read_csv(
    GROUND_TRUTH_FILE
)

pred_df = pd.read_csv(
    ROUTING_FILE
)


# ============================================================
# JOIN PREDICTIONS WITH GROUND TRUTH
# ============================================================

df = pred_df.merge(
    truth_df,
    on="incoming_term",
    how="inner",
)


# ============================================================
# MAPPING CORRECTNESS
# ============================================================

df["mapping_correct"] = (
    df["recommended_concept"]
    == df["expected_mapping"]
)


df["action_correct"] = (
    df["action"]
    == df["expected_action"]
)


# ============================================================
# OVERALL MAPPING ACCURACY
# ============================================================

mapping_accuracy = (
    df["mapping_correct"].mean()
    if len(df)
    else 0
)


# ============================================================
# AUTO APPROVAL PRECISION
# ============================================================

auto_df = df[
    df["routing_decision"]
    == "AUTO_APPROVE"
]

if len(auto_df) > 0:

    auto_precision = (
        auto_df[
            "mapping_correct"
        ].mean()
    )

else:

    auto_precision = 0


# ============================================================
# AUTO APPROVAL COVERAGE
# ============================================================

auto_coverage = (
    len(auto_df) / len(df)
    if len(df)
    else 0
)


# ============================================================
# HUMAN INTERVENTION RATE
# ============================================================

human_df = df[
    df["routing_decision"].isin(
        [
            "SOFT_REVIEW",
            "HUMAN_ESCALATION",
        ]
    )
]

human_intervention_rate = (
    len(human_df) / len(df)
    if len(df)
    else 0
)


# ============================================================
# FALSE AUTO-APPROVAL RATE
# ============================================================

if len(auto_df) > 0:

    false_auto_rate = (
        (~auto_df["mapping_correct"])
        .mean()
    )

else:

    false_auto_rate = 0


# ============================================================
# COLLISION CHECK
# ============================================================
#
# Here we treat incorrect REUSE mappings as cases that should
# ideally be caught before automatic approval.
# ============================================================

incorrect_reuse = df[
    (
        df["expected_action"]
        == "REUSE"
    )
    &
    (
        ~df["mapping_correct"]
    )
]


if len(incorrect_reuse) > 0:

    collision_recall = (
        incorrect_reuse[
            "collision"
        ]
        .astype(bool)
        .mean()
    )

else:

    collision_recall = 1.0


# ============================================================
# SAVE DETAILED RESULTS
# ============================================================

details_file = (
    OUTPUT_DIR
    / "mapping_evaluation.csv"
)

df.to_csv(
    details_file,
    index=False,
)


# ============================================================
# SAVE SUMMARY
# ============================================================

summary = pd.DataFrame(
    [
        {
            "total_mappings":
                len(df),

            "mapping_accuracy":
                round(
                    mapping_accuracy,
                    4,
                ),

            "auto_approval_precision":
                round(
                    auto_precision,
                    4,
                ),

            "auto_approval_coverage":
                round(
                    auto_coverage,
                    4,
                ),

            "human_intervention_rate":
                round(
                    human_intervention_rate,
                    4,
                ),

            "false_auto_approval_rate":
                round(
                    false_auto_rate,
                    4,
                ),

            "collision_recall":
                round(
                    collision_recall,
                    4,
                ),
        }
    ]
)


summary_file = (
    OUTPUT_DIR
    / "pipeline_metrics.csv"
)

summary.to_csv(
    summary_file,
    index=False,
)


print("=" * 65)
print("GSIS STAGE 15 - FINAL EVALUATION")
print("=" * 65)

print(
    f"\nTotal mappings: {len(df)}"
)

print(
    f"Mapping accuracy: "
    f"{mapping_accuracy:.2%}"
)

print(
    f"Auto approval precision: "
    f"{auto_precision:.2%}"
)

print(
    f"Auto approval coverage: "
    f"{auto_coverage:.2%}"
)

print(
    f"Human intervention rate: "
    f"{human_intervention_rate:.2%}"
)

print(
    f"False auto approval rate: "
    f"{false_auto_rate:.2%}"
)

print(
    f"Collision recall: "
    f"{collision_recall:.2%}"
)

print(
    f"\nMetrics saved to:\n{summary_file}"
)