from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "mappings"
    / "confidence_routing.csv"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "review"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# LOAD ROUTING RESULTS
# ============================================================

df = pd.read_csv(INPUT_FILE)


# ============================================================
# CREATE REVIEW QUEUE
# ============================================================
#
# Only SOFT_REVIEW and HUMAN_ESCALATION
# need reviewer attention.
# ============================================================

review_df = df[
    df["routing_decision"].isin(
        [
            "SOFT_REVIEW",
            "HUMAN_ESCALATION",
        ]
    )
].copy()


# ============================================================
# ADD REVIEW FIELDS
# ============================================================

review_df["review_decision"] = ""
review_df["reviewed_concept"] = ""
review_df["reviewer_reason"] = ""
review_df["review_status"] = "PENDING"


# ============================================================
# SAVE REVIEW QUEUE
# ============================================================

queue_file = (
    OUTPUT_DIR
    / "review_queue.csv"
)

review_df.to_csv(
    queue_file,
    index=False,
)


# ============================================================
# AUTO-APPROVED RECORDS
# ============================================================

auto_df = df[
    df["routing_decision"]
    == "AUTO_APPROVE"
].copy()

auto_df["review_decision"] = "SYSTEM_APPROVED"
auto_df["reviewed_concept"] = (
    auto_df["recommended_concept"]
)

auto_df["reviewer_reason"] = (
    "High-confidence mapping passed governance checks."
)

auto_df["review_status"] = "COMPLETED"


auto_file = (
    OUTPUT_DIR
    / "auto_approved.csv"
)

auto_df.to_csv(
    auto_file,
    index=False,
)


print("=" * 60)
print("GSIS STAGE 12 - HUMAN REVIEW WORKFLOW")
print("=" * 60)

print(
    f"\nAuto approved: {len(auto_df)}"
)

print(
    f"Sent for review: {len(review_df)}"
)

print(
    f"\nReview queue:\n{queue_file}"
)

print(
    f"\nAuto approvals:\n{auto_file}"
)