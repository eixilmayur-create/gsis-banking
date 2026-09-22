from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

AUTO_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "review"
    / "auto_approved.csv"
)

REVIEW_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "review"
    / "review_queue.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "review"
    / "feedback_store.csv"
)


# ============================================================
# LOAD AUTO-APPROVED MAPPINGS
# ============================================================

auto_df = pd.read_csv(AUTO_FILE)

auto_feedback = auto_df[
    [
        "incoming_term",
        "recommended_concept",
        "review_decision",
        "reviewer_reason",
    ]
].copy()

auto_feedback = auto_feedback.rename(
    columns={
        "recommended_concept":
            "final_concept"
    }
)


# ============================================================
# LOAD HUMAN-REVIEWED MAPPINGS
# ============================================================

review_df = pd.read_csv(REVIEW_FILE)

# Only use completed reviews.
review_df = review_df[
    review_df["review_status"]
    == "COMPLETED"
].copy()


if len(review_df) > 0:

    human_feedback = review_df[
        [
            "incoming_term",
            "reviewed_concept",
            "review_decision",
            "reviewer_reason",
        ]
    ].copy()

    human_feedback = human_feedback.rename(
        columns={
            "reviewed_concept":
                "final_concept"
        }
    )

else:

    human_feedback = pd.DataFrame(
        columns=[
            "incoming_term",
            "final_concept",
            "review_decision",
            "reviewer_reason",
        ]
    )


# ============================================================
# COMBINE FEEDBACK
# ============================================================

feedback_df = pd.concat(
    [
        auto_feedback,
        human_feedback,
    ],
    ignore_index=True,
)


feedback_df.to_csv(
    OUTPUT_FILE,
    index=False,
)


print("=" * 60)
print("GSIS STAGE 15A - FEEDBACK STORE")
print("=" * 60)

print(
    f"\nApproved historical mappings: {len(feedback_df)}"
)

print(
    f"\nSaved to:\n{OUTPUT_FILE}"
)