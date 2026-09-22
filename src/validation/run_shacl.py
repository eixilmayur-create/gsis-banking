from pathlib import Path
from typing import cast

from rdflib import Graph
from pyshacl import validate  # pyright: ignore[reportUnknownVariableType]

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_GRAPH = (
    PROJECT_ROOT
    / "outputs"
    / "rdf"
    / "banking_complete_graph.ttl"
)

SHAPES_GRAPH = (
    PROJECT_ROOT
    / "shapes"
    / "banking_shapes.ttl"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "validation"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

data_graph = Graph()

data_graph.parse(
    DATA_GRAPH,
    format="turtle",
)

shapes_graph = Graph()

shapes_graph.parse(
    SHAPES_GRAPH,
    format="turtle",
)

conforms, results_graph, results_text = cast(
    tuple[bool, Graph, str],
    validate(
        data_graph=data_graph,
        shacl_graph=shapes_graph,
        inference="none",
        abort_on_first=False,
        allow_infos=True,
        allow_warnings=True,
    ),
)

print("=" * 60)
print("GSIS STAGE 5 - SHACL VALIDATION")
print("=" * 60)

print(f"\nConforms: {conforms}")

print("\nValidation Report:\n")

print(results_text)

results_graph.serialize(
    destination=str(
        OUTPUT_DIR
        / "shacl_report.ttl"
    ),
    format="turtle",
)

with open(
    OUTPUT_DIR / "shacl_report.txt",
    "w",
    encoding="utf-8",
) as file:
    file.write(results_text)

print("\nReports saved under outputs/validation/")