from pathlib import Path
from typing import Any, cast

import pandas as pd
from rdflib import Graph, Namespace


PROJECT_ROOT = Path(__file__).resolve().parents[2]

GRAPH_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "rdf"
    / "banking_complete_graph.ttl"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "migration"
    / "deprecation_impact.csv"
)


EX = Namespace(
    "http://example.org/gsis/banking#"
)


# ============================================================
# LOAD GRAPH
# ============================================================

graph = Graph()

graph.parse(
    GRAPH_FILE,
    format="turtle",
)


# ============================================================
# EXAMPLE DEPRECATION REQUEST
# ============================================================
#
# For demonstration we assume:
#
# Client should be replaced by Customer.
#
# In a real system this request would come from an approved
# reviewer/governance workflow.
# ============================================================

OLD_CLASS = "Client"
NEW_CLASS = "Customer"


# ============================================================
# COUNT INSTANCES
# ============================================================

def count_instances(class_name: str) -> int:

    query = f"""
    PREFIX ex: <http://example.org/gsis/banking#>

    SELECT (COUNT(?entity) AS ?count)
    WHERE {{
        ?entity a ex:{class_name} .
    }}
    """

    result = list(graph.query(query))
    if not result:
        return 0

    first_row: Any = cast(Any, result[0])
    row_values: list[Any] = list(first_row)
    value: Any = row_values[0]
    return int(str(value))


# ============================================================
# FIND PROPERTIES USED BY INSTANCES
# ============================================================

def find_property_usage(class_name: str) -> list[dict[str, Any]]:

    query = f"""
    PREFIX ex: <http://example.org/gsis/banking#>

    SELECT ?property (COUNT(*) AS ?usageCount)
    WHERE {{

        ?entity a ex:{class_name} ;
                ?property ?value .

        FILTER (
            ?property != rdf:type
        )

    }}
    GROUP BY ?property
    ORDER BY DESC(?usageCount)
    """

    query = (
        "PREFIX ex: <http://example.org/gsis/banking#>\n"
        "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\n"
        + query.split("PREFIX ex: <http://example.org/gsis/banking#>", 1)[1]
    )

    results: list[dict[str, Any]] = []

    for row in graph.query(query):
        row_obj: Any = cast(Any, row)
        row_values: list[Any] = list(row_obj)
        property_name = str(row_values[0])
        usage_count = int(str(row_values[1]))

        results.append(
            {
                "property": property_name,
                "usage_count": usage_count,
            }
        )

    return results


# ============================================================
# FIND INCOMING RELATIONSHIPS
# ============================================================
#
# Example:
#
# Something -> relationship -> Client instance
# ============================================================

def count_incoming_relationships(
    class_name: str,
) -> int:

    query = f"""
    PREFIX ex: <http://example.org/gsis/banking#>

    SELECT (COUNT(*) AS ?count)
    WHERE {{

        ?target a ex:{class_name} .

        ?source ?property ?target .
    }}
    """

    result = list(graph.query(query))
    if not result:
        return 0

    first_row: Any = cast(Any, result[0])
    row_values: list[Any] = list(first_row)
    value: Any = row_values[0]
    return int(str(value))


# ============================================================
# CALCULATE IMPACT
# ============================================================

old_instances = count_instances(
    OLD_CLASS
)

new_instances = count_instances(
    NEW_CLASS
)

incoming_relationships = (
    count_incoming_relationships(
        OLD_CLASS
    )
)

property_usage = (
    find_property_usage(
        OLD_CLASS
    )
)


# ============================================================
# SIMPLE MIGRATION RISK
# ============================================================

if old_instances == 0:

    migration_risk = "LOW"

elif (
    old_instances < 100
    and incoming_relationships < 100
):

    migration_risk = "MEDIUM"

else:

    migration_risk = "HIGH"


# ============================================================
# SAVE SUMMARY
# ============================================================

summary = pd.DataFrame(
    [
        {
            "deprecated_concept":
                OLD_CLASS,

            "replacement_concept":
                NEW_CLASS,

            "affected_instances":
                old_instances,

            "replacement_instances":
                new_instances,

            "incoming_relationships":
                incoming_relationships,

            "property_count":
                len(property_usage),

            "migration_risk":
                migration_risk,
        }
    ]
)

summary.to_csv(
    OUTPUT_FILE,
    index=False,
)


print("=" * 60)
print("GSIS STAGE 13 - DEPRECATION IMPACT ANALYSIS")
print("=" * 60)

print(
    f"\nDeprecated concept: {OLD_CLASS}"
)

print(
    f"Replacement concept: {NEW_CLASS}"
)

print(
    f"Affected instances: {old_instances}"
)

print(
    f"Incoming relationships: {incoming_relationships}"
)

print(
    f"Properties used: {len(property_usage)}"
)

print(
    f"Migration risk: {migration_risk}"
)

print(
    f"\nSaved to:\n{OUTPUT_FILE}"
)