from pathlib import Path
from typing import Any

import pandas as pd
from rdflib import Graph, Namespace
from rdflib.namespace import RDF, RDFS, OWL


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

ONTOLOGY_FILE = (
    PROJECT_ROOT
    / "ontology"
    / "banking_ontology.ttl"
)

MAPPING_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "mappings"
    / "gemini_mappings.csv"
)

GROUND_TRUTH_FILE = (
    PROJECT_ROOT
    / "data"
    / "schemas"
    / "mapping_ground_truth.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "mappings"
    / "collision_results.csv"
)


EX = Namespace(
    "http://example.org/gsis/banking#"
)


# ============================================================
# LOAD ONTOLOGY
# ============================================================

graph = Graph()

graph.parse(
    ONTOLOGY_FILE,
    format="turtle",
)


# ============================================================
# LOAD DATA
# ============================================================

if not MAPPING_FILE.exists():
    raise FileNotFoundError(f"Mapping file not found: {MAPPING_FILE}")

if not GROUND_TRUTH_FILE.exists():
    raise FileNotFoundError(f"Ground truth file not found: {GROUND_TRUTH_FILE}")

mappings_df: Any = pd.read_csv(
    MAPPING_FILE
)

ground_truth_df: Any = pd.read_csv(
    GROUND_TRUTH_FILE
)


# ============================================================
# HELPER: CHECK CLASS EXISTS
# ============================================================

def class_exists(class_name: str) -> bool:

    class_uri = EX[class_name]

    return (
        class_uri,
        RDF.type,
        OWL.Class,
    ) in graph


# ============================================================
# HELPER: CHECK DISJOINT CLASSES
# ============================================================

def are_disjoint(
    class_a: str,
    class_b: str,
) -> bool:

    uri_a = EX[class_a]
    uri_b = EX[class_b]

    return (
        (
            uri_a,
            OWL.disjointWith,
            uri_b,
        ) in graph
        or
        (
            uri_b,
            OWL.disjointWith,
            uri_a,
        ) in graph
    )


# ============================================================
# HELPER: GET PARENT CLASS
# ============================================================

def get_parent_classes(
    class_name: str,
) -> list[str]:

    class_uri = EX[class_name]

    parents: list[str] = []

    for parent in graph.objects(
        class_uri,
        RDFS.subClassOf,
    ):

        parents.append(
            str(parent).split("#")[-1]
        )

    return parents


# ============================================================
# COLLISION DETECTION
# ============================================================

results: list[dict[str, Any]] = []


for _, row in mappings_df.iterrows():

    incoming_term = row[
        "incoming_term"
    ]

    recommended = str(
        row["recommended_concept"]
    ).strip()

    action = row["action"]

    collision = False
    collision_type = ""
    reason = ""

    # --------------------------------------------------------
    # CREATE_NEW
    # --------------------------------------------------------

    if action == "CREATE_NEW":

        reason = (
            "No existing ontology mapping selected. "
            "Candidate should follow ontology review."
        )

    # --------------------------------------------------------
    # REVIEW
    # --------------------------------------------------------

    elif action == "REVIEW":

        reason = (
            "Gemini already marked this mapping for review."
        )

    # --------------------------------------------------------
    # REUSE
    # --------------------------------------------------------

    elif action == "REUSE":

        # Check that recommended class exists.

        if not class_exists(
            recommended
        ):

            collision = True

            collision_type = (
                "UNKNOWN_ONTOLOGY_CLASS"
            )

            reason = (
                f"{recommended} does not exist "
                "as an OWL class."
            )

        else:

            # -----------------------------------------------
            # Compare with labeled expected class.
            #
            # In the real production system this ground truth
            # would not be available.
            #
            # Here we use it as an evaluation safety check.
            # -----------------------------------------------

            truth: Any = ground_truth_df[
                ground_truth_df[
                    "incoming_term"
                ]
                == incoming_term
            ]

            if len(truth) > 0:

                row_data: Any = truth.iloc[0]
                expected_action = str(
                    row_data["expected_action"]
                )

                expected_mapping = str(
                    row_data["expected_mapping"]
                )

                if (
                    expected_action
                    == "REUSE"
                    and recommended
                    != expected_mapping
                ):

                    # ---------------------------------------
                    # Check if wrong classes are explicitly
                    # disjoint in the ontology.
                    # ---------------------------------------

                    if are_disjoint(
                        recommended,
                        expected_mapping,
                    ):

                        collision = True

                        collision_type = (
                            "DISJOINT_CLASS_COLLISION"
                        )

                        reason = (
                            f"{recommended} is disjoint "
                            f"with expected concept "
                            f"{expected_mapping}."
                        )

                    else:

                        collision = True

                        collision_type = (
                            "SEMANTIC_MAPPING_MISMATCH"
                        )

                        reason = (
                            f"Recommended concept "
                            f"{recommended} differs from "
                            f"expected semantic concept "
                            f"{expected_mapping}."
                        )

                else:

                    reason = (
                        "Mapping is compatible with "
                        "the ontology and expected concept."
                    )

    results.append(
        {
            "incoming_term":
                incoming_term,

            "recommended_concept":
                recommended,

            "action":
                action,

            "semantic_score":
                row["semantic_score"],

            "top_vector_score":
                row["top_vector_score"],

            "collision":
                collision,

            "collision_type":
                collision_type,

            "collision_reason":
                reason,

            "parent_classes":
                ", ".join(
                    get_parent_classes(
                        recommended
                    )
                )
                if class_exists(
                    recommended
                )
                else "",
        }
    )


# ============================================================
# SAVE RESULTS
# ============================================================

results_df: Any = pd.DataFrame(
    results
)

results_df.to_csv(
    OUTPUT_FILE,
    index=False,
)


# ============================================================
# SUMMARY
# ============================================================

collision_count = int(
    results_df["collision"].sum()
)

print("\n")
print("=" * 65)
print("GSIS STAGE 10 - SEMANTIC COLLISION DETECTOR")
print("=" * 65)

print(
    results_df[
        [
            "incoming_term",
            "recommended_concept",
            "action",
            "collision",
            "collision_type",
        ]
    ].to_string(
        index=False
    )
)

print("\n")
print(
    f"Total mappings: {len(results_df)}"
)

print(
    f"Collisions detected: {collision_count}"
)

print(
    f"\nSaved to:\n{OUTPUT_FILE}"
)