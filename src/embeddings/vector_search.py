from pathlib import Path
import json
from typing import Any

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

ONTOLOGY_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "embeddings"
    / "ontology_embeddings.csv"
)

INCOMING_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "embeddings"
    / "incoming_term_embeddings.csv"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "mappings"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


TOP_K = 3


# ============================================================
# COSINE SIMILARITY
# ============================================================

def cosine_similarity(
    vector_a: list[float] | np.ndarray,
    vector_b: list[float] | np.ndarray,
) -> float:

    a = np.array(vector_a, dtype=float)
    b = np.array(vector_b, dtype=float)

    denominator = (
        np.linalg.norm(a)
        * np.linalg.norm(b)
    )

    if denominator == 0:
        return 0.0

    return float(
        np.dot(a, b)
        / denominator
    )


# ============================================================
# LOAD EMBEDDINGS
# ============================================================

if not ONTOLOGY_FILE.exists():
    raise FileNotFoundError(f"Ontology embedding file not found: {ONTOLOGY_FILE}")

if not INCOMING_FILE.exists():
    raise FileNotFoundError(f"Incoming embedding file not found: {INCOMING_FILE}")

ontology_df = pd.read_csv(
    ONTOLOGY_FILE
)

incoming_df = pd.read_csv(
    INCOMING_FILE
)


# Convert JSON strings back into Python vectors.

ontology_df["vector"] = (
    ontology_df["embedding"]
    .apply(json.loads)
)

incoming_df["vector"] = (
    incoming_df["embedding"]
    .apply(json.loads)
)


# ============================================================
# CANDIDATE RETRIEVAL
# ============================================================

results: list[dict[str, Any]] = []


for _, incoming in incoming_df.iterrows():

    candidates: list[dict[str, Any]] = []

    for _, ontology in ontology_df.iterrows():

        similarity = cosine_similarity(
            incoming["vector"],
            ontology["vector"],
        )

        candidates.append(
            {
                "ontology_term":
                    ontology["term"],

                "ontology_description":
                    ontology["description"],

                "similarity":
                    similarity,
            }
        )


    # Highest similarity first
    candidates = sorted(
        candidates,
        key=lambda item: item["similarity"],
        reverse=True,
    )


    # Keep top K candidates
    top_candidates = candidates[:TOP_K]


    for rank, candidate in enumerate(
        top_candidates,
        start=1,
    ):

        results.append(
            {
                "source_system":
                    incoming["source_system"],

                "incoming_term":
                    incoming["incoming_term"],

                "incoming_description":
                    incoming["description"],

                "candidate_rank":
                    rank,

                "ontology_candidate":
                    candidate["ontology_term"],

                "similarity_score":
                    round(
                        candidate["similarity"],
                        4,
                    ),

                "ontology_description":
                    candidate[
                        "ontology_description"
                    ],
            }
        )


# ============================================================
# SAVE RESULTS
# ============================================================

results_df: Any = pd.DataFrame(
    results
)

output_file = (
    OUTPUT_DIR
    / "vector_candidates.csv"
)

results_df.to_csv(
    output_file,
    index=False,
)


# ============================================================
# PRINT RESULTS
# ============================================================

print("\n")
print("=" * 65)
print("GSIS STAGE 8 - VECTOR CANDIDATE RETRIEVAL")
print("=" * 65)


for incoming_term in (
    results_df["incoming_term"].unique()
):

    subset: Any = results_df[
        results_df["incoming_term"]
        == incoming_term
    ]

    print(
        f"\nIncoming term: {incoming_term}"
    )

    for _, row in subset.iterrows():

        print(
            f"  {row['candidate_rank']}. "
            f"{row['ontology_candidate']} "
            f"-> {row['similarity_score']}"
        )


print("\n")
print(
    f"Candidate file saved to:\n{output_file}"
)