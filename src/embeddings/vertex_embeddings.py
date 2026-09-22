from pathlib import Path
import os
import json
from typing import Any, cast

import pandas as pd
from google import genai
from google.genai import types


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

ONTOLOGY_TERMS_FILE = (
    PROJECT_ROOT
    / "data"
    / "schemas"
    / "existing_ontology_terms.csv"
)

INCOMING_TERMS_FILE = (
    PROJECT_ROOT
    / "data"
    / "schemas"
    / "incoming_schema_terms.csv"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "embeddings"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# VERTEX AI CONFIGURATION
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

MODEL_NAME = "gemini-embedding-001"

# Smaller vector for learning/demo.
# Production dimensionality can be tuned later.
EMBEDDING_DIMENSION = 768


# ============================================================
# EMBEDDING FUNCTION
# ============================================================

def create_embedding(
    text: str,
    task_type: str = "RETRIEVAL_DOCUMENT",
) -> list[float]:

    if client is None:
        raise RuntimeError(
            "Vertex AI is not configured. Set GOOGLE_CLOUD_PROJECT "
            "(or GOOGLE_CLOUD_PROJECT_ID) before running this script."
        )

    response: Any = cast(Any, client.models).embed_content( # type: ignore
        model=MODEL_NAME,
        contents=text,
        config=types.EmbedContentConfig(
            task_type=task_type,
            output_dimensionality=EMBEDDING_DIMENSION,
            auto_truncate=True,
        ),
    )

    embeddings: Any = getattr(response, "embeddings", None)
    if embeddings is None or len(embeddings) == 0:
        raise ValueError("Embedding response did not contain any vectors.")

    first_embedding: Any = embeddings[0]
    values: Any = getattr(first_embedding, "values", None)
    if values is None:
        raise ValueError("Embedding vector payload is empty.")

    return [float(value) for value in values]


def main() -> None:
    global client

    if not PROJECT_ID:
        raise SystemExit(
            "GOOGLE_CLOUD_PROJECT is not set. Run this command first:\n"
            "set GOOGLE_CLOUD_PROJECT=your-project-id\n"
            "or export GOOGLE_CLOUD_PROJECT=your-project-id"
        )

    client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location=LOCATION,
    )

    # ============================================================
    # ONTOLOGY TERM EMBEDDINGS
    # ============================================================

    ontology_df = pd.read_csv(
        ONTOLOGY_TERMS_FILE
    )

    ontology_records: list[dict[str, str]] = []

    print("\nCreating ontology embeddings...\n")

    for _, row in ontology_df.iterrows():

        text = (
            f"Ontology concept: {row['term']}. "
            f"Type: {row['term_type']}. "
            f"Definition: {row['description']}"
        )

        vector = create_embedding(
            text,
            task_type="RETRIEVAL_DOCUMENT",
        )

        ontology_records.append(
            {
                "term": row["term"],
                "term_type": row["term_type"],
                "description": row["description"],
                "embedding": json.dumps(vector),
            }
        )

        print(
            f"Embedded ontology term: {row['term']}"
        )

    ontology_output = pd.DataFrame(
        ontology_records
    )

    ontology_output.to_csv(
        OUTPUT_DIR
        / "ontology_embeddings.csv",
        index=False,
    )

    # ============================================================
    # INCOMING SCHEMA TERM EMBEDDINGS
    # ============================================================

    incoming_df = pd.read_csv(
        INCOMING_TERMS_FILE
    )

    incoming_records: list[dict[str, str]] = []

    print("\nCreating incoming schema embeddings...\n")

    for _, row in incoming_df.iterrows():

        text = (
            f"Incoming schema term: {row['incoming_term']}. "
            f"Source system: {row['source_system']}. "
            f"Description: {row['description']}"
        )

        vector = create_embedding(
            text,
            task_type="RETRIEVAL_QUERY",
        )

        incoming_records.append(
            {
                "source_system": row["source_system"],
                "incoming_term": row["incoming_term"],
                "description": row["description"],
                "embedding": json.dumps(vector),
            }
        )

        print(
            f"Embedded incoming term: {row['incoming_term']}"
        )

    incoming_output = pd.DataFrame(
        incoming_records
    )

    incoming_output.to_csv(
        OUTPUT_DIR
        / "incoming_term_embeddings.csv",
        index=False,
    )

    print("\n")
    print("=" * 60)
    print("GSIS STAGE 7 - EMBEDDINGS COMPLETE")
    print("=" * 60)

    print(
        f"Ontology terms embedded: {len(ontology_output)}"
    )

    print(
        f"Incoming terms embedded: {len(incoming_output)}"
    )

    print(
        f"Embedding dimension: {EMBEDDING_DIMENSION}"
    )


if __name__ == "__main__":
    main()