# ============================================================
# GSIS - STAGE 2
# AUTOMATED MULTI-SOURCE SCHEMA PROFILER
# ============================================================
#
# Purpose:
# --------
# Analyse every source CSV and generate field-level metadata.
#
# The output will later be used by:
#
#   - Ontology mapping
#   - Embeddings
#   - Vector Search
#   - Gemini
#   - Semantic collision detection
#
# Instead of sending raw CSV columns directly to an LLM,
# GSIS first creates a structured semantic profile.
#
# ============================================================


from pathlib import Path
import json
import re
from typing import Any

import pandas as pd


# ============================================================
# 1. PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

PROCESSED_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# 2. NORMALIZE COLUMN NAME
# ============================================================
#
# Example:
#
# customer_id
# CustomerID
# customer-id
#
# become approximately:
#
# customer id
#
# This helps later semantic comparison.
# ============================================================

def normalize_name(column_name: str) -> str:

    name = column_name.strip()

    # Convert CamelCase into separate words.
    name = re.sub(
        r"([a-z0-9])([A-Z])",
        r"\1 \2",
        name,
    )

    # Replace underscore and dash.
    name = name.replace("_", " ")
    name = name.replace("-", " ")

    # Collapse repeated spaces.
    name = re.sub(
        r"\s+",
        " ",
        name,
    )

    return name.lower().strip()


# ============================================================
# 3. IDENTIFIER DETECTION
# ============================================================
#
# We use a simple heuristic.
#
# Fields containing words such as:
#
# id
# identifier
# ref
# code
#
# may represent identifiers.
#
# This is only metadata.
#
# We do NOT assume that every "code" column is an entity ID.
# ============================================================

IDENTIFIER_WORDS = {
    "id",
    "identifier",
    "ref",
    "reference",
    "code",
}


def detect_identifier(column_name: str) -> bool:

    normalized = normalize_name(column_name)

    words = set(
        normalized.split()
    )

    return bool(
        words.intersection(
            IDENTIFIER_WORDS
        )
    )


# ============================================================
# 4. INFER SEMANTIC DATATYPE
# ============================================================
#
# Pandas dtype is useful but incomplete.
#
# For example:
#
# customer_id
#
# is technically a string.
#
# But:
#
# date_of_birth
#
# may also initially arrive as a string.
#
# We therefore create a higher-level semantic datatype.
# ============================================================

def infer_semantic_type(
    series: pd.Series,
    column_name: str,
) -> str:

    normalized = normalize_name(
        column_name
    )

    # --------------------------------------------------------
    # Explicit name-based detection
    # --------------------------------------------------------

    if "date" in normalized:
        return "date"

    if "time" in normalized:
        return "datetime"

    if any(
        keyword in normalized
        for keyword in [
            "amount",
            "balance",
            "score",
        ]
    ):
        return "numeric"

    if any(
        keyword in normalized
        for keyword in [
            "year",
            "count",
        ]
    ):
        return "integer"

    # --------------------------------------------------------
    # Native pandas type detection
    # --------------------------------------------------------

    if pd.api.types.is_bool_dtype(
        series
    ):
        return "boolean"

    if pd.api.types.is_integer_dtype(
        series
    ):
        return "integer"

    if pd.api.types.is_float_dtype(
        series
    ):
        return "numeric"

    if pd.api.types.is_datetime64_any_dtype(
        series
    ):
        return "datetime"

    # --------------------------------------------------------
    # Attempt date detection on strings
    # --------------------------------------------------------

    non_null = series.dropna()

    if len(non_null) > 0:

        sample = non_null.head(50)

        try:

            converted = pd.to_datetime(
                sample,
                errors="coerce",
            )

            valid_ratio = (
                converted.notna().mean()
            )

            if valid_ratio >= 0.90:
                return "date_or_datetime"

        except Exception:
            pass

    return "string"


# ============================================================
# 5. GET SAMPLE VALUES
# ============================================================

def get_sample_values(
    series: pd.Series,
    max_values: int = 5,
) -> list[str]:

    values = (
        series
        .dropna()
        .astype(str)
        .drop_duplicates()
        .head(max_values)
        .tolist()
    )

    return values


# ============================================================
# 6. CALCULATE MIN / MAX
# ============================================================

def get_min_max(
    series: pd.Series,
    semantic_type: str,
):

    clean = series.dropna()

    if len(clean) == 0:
        return None, None

    # --------------------------------------------------------
    # Numeric columns
    # --------------------------------------------------------

    if semantic_type in {
        "numeric",
        "integer",
    }:

        numeric = pd.to_numeric(
            clean,
            errors="coerce",
        ).dropna()

        if len(numeric) == 0:
            return None, None

        return (
            float(numeric.min()),
            float(numeric.max()),
        )

    # --------------------------------------------------------
    # Date columns
    # --------------------------------------------------------

    if semantic_type in {
        "date",
        "datetime",
        "date_or_datetime",
    }:

        dates = pd.to_datetime(
            clean,
            errors="coerce",
        ).dropna()

        if len(dates) == 0:
            return None, None

        return (
            str(dates.min()),
            str(dates.max()),
        )

    return None, None


# ============================================================
# 7. GENERATE SEMANTIC DESCRIPTION
# ============================================================
#
# This creates machine-readable natural language.
#
# Later the embedding model will embed THIS description,
# instead of embedding only:
#
# "customer_id"
#
# Richer context usually produces better semantic retrieval.
# ============================================================

def build_semantic_description(
    source_system: str,
    source_file: str,
    column_name: str,
    semantic_type: str,
    likely_identifier: bool,
    samples: list[str],
) -> str:

    normalized = normalize_name(
        column_name
    )

    identifier_text = (
        "The field appears to represent an identifier or reference."
        if likely_identifier
        else
        "The field appears to represent an attribute or descriptive value."
    )

    sample_text = ", ".join(
        samples[:3]
    )

    description = (
        f"Source system: {source_system}. "
        f"Source file: {source_file}. "
        f"Field: {column_name}. "
        f"Normalized field meaning: {normalized}. "
        f"Semantic datatype: {semantic_type}. "
        f"{identifier_text} "
        f"Example values: {sample_text}."
    )

    return description


# ============================================================
# 8. PROFILE ONE DATAFRAME
# ============================================================

def profile_dataframe(
    dataframe: pd.DataFrame,
    source_system: str,
    source_file: str,
) -> list[dict[str, Any]]:

    profiles: list[dict[str, Any]] = []

    total_rows = len(
        dataframe
    )

    for column in dataframe.columns:

        series = dataframe[column]

        null_count = int(
            series.isna().sum()
        )

        unique_count = int(
            series.nunique(
                dropna=True
            )
        )

        null_ratio = (
            null_count / total_rows
            if total_rows
            else 0
        )

        unique_ratio = (
            unique_count / total_rows
            if total_rows
            else 0
        )

        semantic_type = (
            infer_semantic_type(
                series,
                column,
            )
        )

        likely_identifier = (
            detect_identifier(
                column
            )
        )

        samples = get_sample_values(
            series
        )

        min_value, max_value = (
            get_min_max(
                series,
                semantic_type,
            )
        )

        semantic_description = (
            build_semantic_description(
                source_system=source_system,
                source_file=source_file,
                column_name=column,
                semantic_type=semantic_type,
                likely_identifier=likely_identifier,
                samples=samples,
            )
        )

        profile: dict[str, Any] = {
            "source_system":
                source_system,

            "source_file":
                source_file,

            "column_name":
                column,

            "normalized_name":
                normalize_name(
                    column
                ),

            "pandas_type":
                str(series.dtype),

            "inferred_type":
                semantic_type,

            "row_count":
                total_rows,

            "null_count":
                null_count,

            "null_ratio":
                round(
                    null_ratio,
                    4,
                ),

            "unique_count":
                unique_count,

            "unique_ratio":
                round(
                    unique_ratio,
                    4,
                ),

            "likely_identifier":
                likely_identifier,

            "min_value":
                min_value,

            "max_value":
                max_value,

            "sample_values":
                json.dumps(
                    samples,
                    ensure_ascii=False,
                ),

            "semantic_description":
                semantic_description,
        }

        profiles.append(
            profile
        )

    return profiles


# ============================================================
# 9. SOURCE SYSTEM NAME
# ============================================================
#
# Folder:
#
# core_banking/
#
# becomes:
#
# Core Banking
# ============================================================

def get_source_system(
    csv_path: Path,
) -> str:

    relative_path = (
        csv_path.relative_to(
            RAW_DIR
        )
    )

    source_folder = (
        relative_path.parts[0]
    )

    return (
        source_folder
        .replace("_", " ")
        .title()
    )


# ============================================================
# 10. LOAD AND PROFILE ALL CSV FILES
# ============================================================

def profile_all_sources():

    all_profiles: list[dict[str, Any]] = []

    csv_files = sorted(
        RAW_DIR.rglob(
            "*.csv"
        )
    )

    if not csv_files:

        raise FileNotFoundError(
            f"No CSV files found under {RAW_DIR}"
        )

    print("\nProfiling source files...\n")

    for csv_path in csv_files:

        source_system = (
            get_source_system(
                csv_path
            )
        )

        print(
            f"Reading: {csv_path.name}"
        )

        dataframe = pd.read_csv(
            csv_path
        )

        profiles = (
            profile_dataframe(
                dataframe,
                source_system,
                csv_path.name,
            )
        )

        all_profiles.extend(
            profiles
        )

    return pd.DataFrame(
        all_profiles
    )


# ============================================================
# 11. TOKENIZE COLUMN NAMES
# ============================================================
#
# Used for simple lexical overlap detection.
#
# Example:
#
# card_holder_id
#
# ->
#
# {"card", "holder", "id"}
# ============================================================

STOP_WORDS = {
    "id",
    "ref",
    "reference",
    "code",
    "number",
    "name",
    "type",
    "status",
}


def tokenize_column_name(
    name: str,
) -> set[str]:

    normalized = normalize_name(
        name
    )

    tokens = set(
        normalized.split()
    )

    meaningful_tokens = (
        tokens - STOP_WORDS
    )

    return meaningful_tokens


# ============================================================
# 12. LEXICAL SIMILARITY
# ============================================================
#
# Jaccard similarity:
#
# intersection / union
#
# Example:
#
# customer_id
# customer_ref
#
# Tokens after removing generic words:
#
# {"customer"}
# {"customer"}
#
# Similarity = 1.0
#
# This is intentionally simple.
#
# Later embeddings replace this with semantic similarity.
# ============================================================

def lexical_similarity(
    column_a: str,
    column_b: str,
) -> float:

    tokens_a = tokenize_column_name(
        column_a
    )

    tokens_b = tokenize_column_name(
        column_b
    )

    if not tokens_a or not tokens_b:
        return 0.0

    intersection = (
        tokens_a.intersection(
            tokens_b
        )
    )

    union = (
        tokens_a.union(
            tokens_b
        )
    )

    return len(intersection) / len(union)


# ============================================================
# 13. DOMAIN SYNONYM GROUPS
# ============================================================
#
# Simple domain dictionary.
#
# IMPORTANT:
#
# This is NOT the final ontology.
#
# It only helps Stage 2 identify likely cross-system overlap.
#
# Later OWL + embeddings + Gemini provide the proper semantic
# layer.
# ============================================================

SEMANTIC_GROUPS = {

    "customer": {
        "customer",
        "client",
        "holder",
        "subject",
        "borrower",
    },

    "account": {
        "account",
        "acct",
    },

    "transaction": {
        "transaction",
        "payment",
        "event",
    },

    "merchant": {
        "merchant",
        "seller",
        "payee",
    },

    "risk": {
        "risk",
        "fraud",
        "alert",
        "case",
    },

    "card": {
        "card",
        "plastic",
    },
}


# ============================================================
# 14. DETECT SEMANTIC GROUP
# ============================================================

def detect_semantic_group(
    column_name: str,
):

    tokens = tokenize_column_name(
        column_name
    )

    for group_name, keywords in (
        SEMANTIC_GROUPS.items()
    ):

        if tokens.intersection(
            keywords
        ):
            return group_name

    return None


# ============================================================
# 15. GENERATE CROSS-SYSTEM OVERLAP CANDIDATES
# ============================================================
#
# We compare fields across DIFFERENT source systems.
#
# We do not attempt to make a final semantic decision here.
#
# Output:
#
# customer_id
# client_id
#
# may become a candidate pair.
# ============================================================

def generate_overlap_candidates(
    profile_df: pd.DataFrame,
) -> pd.DataFrame:

    candidates: list[dict[str, Any]] = []

    records = (
        profile_df
        .to_dict(
            orient="records"
        )
    )

    for i in range(
        len(records)
    ):

        for j in range(
            i + 1,
            len(records)
        ):

            left = records[i]
            right = records[j]

            # Ignore fields from same source system.
            if (
                left["source_system"]
                == right["source_system"]
            ):
                continue

            lexical_score = (
                lexical_similarity(
                    left["column_name"],
                    right["column_name"],
                )
            )

            left_group = (
                detect_semantic_group(
                    left["column_name"]
                )
            )

            right_group = (
                detect_semantic_group(
                    right["column_name"]
                )
            )

            semantic_group_match = (
                left_group is not None
                and left_group
                == right_group
            )

            # ------------------------------------------------
            # Candidate logic
            #
            # Keep a pair when:
            #
            # lexical similarity is meaningful
            #
            # OR
            #
            # the fields belong to the same crude semantic
            # domain group.
            # ------------------------------------------------

            if (
                lexical_score >= 0.30
                or semantic_group_match
            ):

                candidates.append(
                    {
                        "left_system":
                            left["source_system"],

                        "left_column":
                            left["column_name"],

                        "right_system":
                            right["source_system"],

                        "right_column":
                            right["column_name"],

                        "lexical_similarity":
                            round(
                                lexical_score,
                                4,
                            ),

                        "semantic_group":
                            (
                                left_group
                                if semantic_group_match
                                else None
                            ),

                        "same_inferred_type":
                            (
                                left["inferred_type"]
                                == right["inferred_type"]
                            ),

                        "left_identifier":
                            left["likely_identifier"],

                        "right_identifier":
                            right["likely_identifier"],
                    }
                )

    candidate_df = pd.DataFrame(
        candidates
    )

    if len(candidate_df) > 0:

        candidate_df = (
            candidate_df
            .sort_values(
                by=[
                    "semantic_group",
                    "lexical_similarity",
                ],
                ascending=[
                    True,
                    False,
                ],
                na_position="last",
            )
        )

    return candidate_df


# ============================================================
# 16. DATASET-LEVEL SUMMARY
# ============================================================

def generate_dataset_summary(
    profile_df: pd.DataFrame,
):

    summary = (
        profile_df
        .groupby(
            [
                "source_system",
                "source_file",
            ]
        )
        .agg(
            columns=(
                "column_name",
                "count",
            ),
            rows=(
                "row_count",
                "max",
            ),
            identifier_fields=(
                "likely_identifier",
                "sum",
            ),
        )
        .reset_index()
    )

    return summary


# ============================================================
# 17. MAIN
# ============================================================

def main():

    print(
        "=" * 70
    )

    print(
        "GSIS STAGE 2 - AUTOMATED SCHEMA PROFILING"
    )

    print(
        "=" * 70
    )

    # --------------------------------------------------------
    # Profile every raw source.
    # --------------------------------------------------------

    profile_df = (
        profile_all_sources()
    )

    # --------------------------------------------------------
    # Save field-level schema profile.
    # --------------------------------------------------------

    profile_output = (
        PROCESSED_DIR
        / "schema_profile.csv"
    )

    profile_df.to_csv(
        profile_output,
        index=False,
    )

    # --------------------------------------------------------
    # Generate dataset summary.
    # --------------------------------------------------------

    summary_df = (
        generate_dataset_summary(
            profile_df
        )
    )

    summary_output = (
        PROCESSED_DIR
        / "dataset_summary.csv"
    )

    summary_df.to_csv(
        summary_output,
        index=False,
    )

    # --------------------------------------------------------
    # Generate potential cross-system overlaps.
    # --------------------------------------------------------

    overlap_df = (
        generate_overlap_candidates(
            profile_df
        )
    )

    overlap_output = (
        PROCESSED_DIR
        / "schema_overlap_candidates.csv"
    )

    overlap_df.to_csv(
        overlap_output,
        index=False,
    )

    # --------------------------------------------------------
    # Console summary.
    # --------------------------------------------------------

    print("\n")
    print("-" * 70)
    print("DATASET SUMMARY")
    print("-" * 70)

    print(
        summary_df.to_string(
            index=False
        )
    )

    print("\n")
    print("-" * 70)

    print(
        f"Total source columns profiled: {len(profile_df)}"
    )

    print(
        f"Potential overlap pairs: {len(overlap_df)}"
    )

    print("-" * 70)

    print(
        "\nGenerated files:"
    )

    print(
        f"1. {profile_output}"
    )

    print(
        f"2. {summary_output}"
    )

    print(
        f"3. {overlap_output}"
    )

    print("\n")
    print("=" * 70)

    print(
        "STAGE 2 COMPLETED SUCCESSFULLY"
    )

    print("=" * 70)

    print(
        "\nNext Stage:"
    )

    print(
        "Build the RDF/OWL banking ontology."
    )


if __name__ == "__main__":
    main()