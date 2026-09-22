# ============================================================
# GSIS - STAGE 3
# RDF / OWL ONTOLOGY INSPECTOR
# ============================================================

from pathlib import Path

from rdflib import Graph
from rdflib.namespace import RDF, RDFS, OWL


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

ONTOLOGY_FILE = (
    PROJECT_ROOT
    / "ontology"
    / "banking_ontology.ttl"
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
# BASIC GRAPH INFORMATION
# ============================================================

print("=" * 70)

print(
    "GSIS STAGE 3 - BANKING ONTOLOGY INSPECTION"
)

print("=" * 70)

print(
    f"\nOntology file: {ONTOLOGY_FILE}"
)

print(
    f"Total RDF triples: {len(graph):,}"
)


# ============================================================
# EXTRACT CLASSES
# ============================================================

classes = sorted(
    set(
        graph.subjects(
            RDF.type,
            OWL.Class,
        )
    ),
    key=str,
)


print("\n")
print("-" * 70)
print("OWL CLASSES")
print("-" * 70)

for cls in classes:

    label = graph.value(
        cls,
        RDFS.label,
    )

    print(
        f"{label if label else cls}"
    )


# ============================================================
# EXTRACT OBJECT PROPERTIES
# ============================================================

object_properties = sorted(
    set(
        graph.subjects(
            RDF.type,
            OWL.ObjectProperty,
        )
    ),
    key=str,
)


print("\n")
print("-" * 70)
print("OBJECT PROPERTIES")
print("-" * 70)

for prop in object_properties:

    label = graph.value(
        prop,
        RDFS.label,
    )

    domain = graph.value(
        prop,
        RDFS.domain,
    )

    range_value = graph.value(
        prop,
        RDFS.range,
    )

    print(
        f"{label} | "
        f"domain={domain} | "
        f"range={range_value}"
    )


# ============================================================
# EXTRACT DATATYPE PROPERTIES
# ============================================================

datatype_properties = sorted(
    set(
        graph.subjects(
            RDF.type,
            OWL.DatatypeProperty,
        )
    ),
    key=str,
)


print("\n")
print("-" * 70)
print("DATATYPE PROPERTIES")
print("-" * 70)

for prop in datatype_properties:

    label = graph.value(
        prop,
        RDFS.label,
    )

    domain = graph.value(
        prop,
        RDFS.domain,
    )

    range_value = graph.value(
        prop,
        RDFS.range,
    )

    print(
        f"{label} | "
        f"domain={domain} | "
        f"range={range_value}"
    )


# ============================================================
# SUMMARY
# ============================================================

print("\n")
print("=" * 70)

print(
    f"Classes:             {len(classes)}"
)

print(
    f"Object properties:   {len(object_properties)}"
)

print(
    f"Datatype properties: {len(datatype_properties)}"
)

print(
    f"Total triples:       {len(graph)}"
)

print("=" * 70)

print(
    "\nStage 3 ontology loaded successfully."
)

print(
    "\nNext Stage: CSV data to RDF Knowledge Graph."
)