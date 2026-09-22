from pathlib import Path
import os
import json
from typing import Any

import pandas as pd

from google import genai
from google.genai import types


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

CANDIDATE_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "mappings"
    / "vector_candidates.csv"
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


# ============================================================
# VERTEX AI CONFIG
# ============================================================

PROJECT_ID = (
    os.getenv("GOOGLE_CLOUD_PROJECT")
    or os.getenv("GOOGLE_CLOUD_PROJECT_ID")
    or os.getenv("GCLOUD_PROJECT")
)

LOCATION = os.getenv(
    "GOOGLE_CLOUD_LOCATION",
    "us-central1",
)

client: Any = None

if PROJECT_ID:
    client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location=LOCATION,
    )


MODEL_NAME = "gemini-2.5-flash"


# ============================================================
# RESPONSE SCHEMA
# ============================================================

RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "OBJECT",
    "properties": {
        "recommended_concept": {
            "type": "STRING"
        },
        "action": {
            "type": "STRING",
            "enum": [
                "REUSE",
                "CREATE_NEW",
                "REVIEW"
            ]
        },
        "semantic_score": {
            "type": "NUMBER"
        },
        "reason": {
            "type": "STRING"
        }
    },
    "required": [
        "recommended_concept",
        "action",
        "semantic_score",
        "reason"
    ]
}


# ============================================================
# LOAD VECTOR CANDIDATES
# ============================================================

if not CANDIDATE_FILE.exists():
    raise FileNotFoundError(f"Candidate file not found: {CANDIDATE_FILE}")

candidates_df = pd.read_csv(
    CANDIDATE_FILE
)


# ============================================================
# BUILD PROMPT
# ============================================================

def build_prompt(group: pd.DataFrame) -> str:

    first = group.iloc[0]

    candidate_text = ""

    for _, row in group.iterrows():

        candidate_text += (
            f"\nCandidate {row['candidate_rank']}:\n"
            f"Concept: {row['ontology_candidate']}\n"
            f"Description: {row['ontology_description']}\n"
            f"Vector similarity: {row['similarity_score']}\n"
        )

    prompt = f"""
You are an ontology schema-mapping assistant.

Your task is to map an incoming banking schema term
to the most appropriate existing ontology concept.

Incoming term:
{first['incoming_term']}

Source system:
{first['source_system']}

Incoming description:
{first['incoming_description']}

Candidate ontology concepts:
{candidate_text}

Rules:

1. Choose REUSE when an existing ontology concept
   represents the same business meaning.

2. Choose CREATE_NEW when none of the candidates
   represent the concept correctly.

3. Choose REVIEW when the meaning is ambiguous
   or insufficient information exists.

4. Semantic similarity alone is not enough.
   Consider the business meaning.

5. semantic_score must be between 0 and 1.

Return only the requested structured result.
"""

    return prompt


# ============================================================
# GEMINI MAPPING
# ============================================================

def map_term(group: pd.DataFrame) -> dict[str, Any]:

    if client is None:
        raise RuntimeError(
            "Vertex AI is not configured. Set GOOGLE_CLOUD_PROJECT "
            "(or GOOGLE_CLOUD_PROJECT_ID) before running this script."
        )

    prompt = build_prompt(group)

    response: Any = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0,
            response_mime_type="application/json",
            response_schema=RESPONSE_SCHEMA,
        ),
    )

    if response is None or response.text is None:
        raise ValueError("Gemini returned no structured response text.")

    return json.loads(response.text)


# ============================================================
# RUN MAPPING
# ============================================================

results: list[dict[str, Any]] = []

grouped = candidates_df.groupby(
    "incoming_term",
    sort=False,
)


for incoming_term, group in grouped:

    print(
        f"Mapping: {incoming_term}"
    )

    first = group.iloc[0]

    try:

        mapping = map_term(group)

        results.append(
            {
                "source_system":
                    first["source_system"],

                "incoming_term":
                    incoming_term,

                "recommended_concept":
                    mapping[
                        "recommended_concept"
                    ],

                "action":
                    mapping["action"],

                "semantic_score":
                    mapping["semantic_score"],

                "reason":
                    mapping["reason"],

                "top_vector_candidate":
                    first[
                        "ontology_candidate"
                    ],

                "top_vector_score":
                    first[
                        "similarity_score"
                    ],
            }
        )

    except Exception as error:

        results.append(
            {
                "source_system":
                    first["source_system"],

                "incoming_term":
                    incoming_term,

                "recommended_concept":
                    "",

                "action":
                    "REVIEW",

                "semantic_score":
                    0,

                "reason":
                    f"Gemini request failed: {error}",

                "top_vector_candidate":
                    first[
                        "ontology_candidate"
                    ],

                "top_vector_score":
                    first[
                        "similarity_score"
                    ],
            }
        )


# ============================================================
# SAVE RESULTS
# ============================================================

results_df = pd.DataFrame(
    results
)

output_file = (
    OUTPUT_DIR
    / "gemini_mappings.csv"
)

results_df.to_csv(
    output_file,
    index=False,
)


print("\n")
print("=" * 65)
print("GSIS STAGE 9 - GEMINI MAPPING COMPLETE")
print("=" * 65)

print(
    results_df[
        [
            "incoming_term",
            "recommended_concept",
            "action",
            "semantic_score",
        ]
    ].to_string(
        index=False
    )
)

print(
    f"\nSaved to:\n{output_file}"
)