from pathlib import Path
from typing import Any, cast

import pandas as pd
from rdflib import Graph

PROJECT_ROOT = Path(__file__).resolve().parents[2]

GRAPH_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "rdf"
    / "banking_complete_graph.ttl"
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

graph = Graph()

graph.parse(
    GRAPH_FILE,
    format="turtle",
)


# ============================================================
# SPARQL QUALITY RULES
# ============================================================

CHECKS = {

    "orphan_account_customer": """
    PREFIX ex: <http://example.org/gsis/banking#>

    SELECT ?account ?customer
    WHERE {
        ?account a ex:Account ;
                 ex:heldBy ?customer .

        FILTER NOT EXISTS {
            ?customer a ex:Customer .
        }
    }
    """,

    "card_missing_account": """
    PREFIX ex: <http://example.org/gsis/banking#>

    SELECT ?card ?account
    WHERE {
        ?card a ex:Card ;
              ex:linkedToAccount ?account .

        FILTER NOT EXISTS {
            ?account a ex:Account .
        }
    }
    """,

    "risk_missing_transaction": """
    PREFIX ex: <http://example.org/gsis/banking#>

    SELECT ?risk ?transaction
    WHERE {
        ?risk a ex:RiskEvent ;
              ex:concernsTransaction ?transaction .

        FILTER NOT EXISTS {
            ?transaction a ex:Transaction .
        }
    }
    """,

    "transaction_missing_customer": """
    PREFIX ex: <http://example.org/gsis/banking#>

    SELECT ?transaction ?customer
    WHERE {
        ?transaction a ex:Transaction ;
                     ex:initiatedBy ?customer .

        FILTER NOT EXISTS {
            ?customer a ex:Customer .
        }
    }
    """,

    "transaction_missing_account": """
    PREFIX ex: <http://example.org/gsis/banking#>

    SELECT ?transaction ?account
    WHERE {
        ?transaction a ex:Transaction ;
                     ex:usesAccount ?account .

        FILTER NOT EXISTS {
            ?account a ex:Account .
        }
    }
    """,

    "duplicate_customer_id": """
    PREFIX ex: <http://example.org/gsis/banking#>

    SELECT ?customerId (COUNT(?customer) AS ?count)
    WHERE {
        ?customer a ex:Customer ;
                  ex:customerId ?customerId .
    }
    GROUP BY ?customerId
    HAVING (COUNT(?customer) > 1)
    """,

    "duplicate_account_id": """
    PREFIX ex: <http://example.org/gsis/banking#>

    SELECT ?accountId (COUNT(?account) AS ?count)
    WHERE {
        ?account a ex:Account ;
                 ex:accountId ?accountId .
    }
    GROUP BY ?accountId
    HAVING (COUNT(?account) > 1)
    """
}


# ============================================================
# RUN CHECKS
# ============================================================

summary: list[dict[str, Any]] = []

for rule_name, query in CHECKS.items():

    results = graph.query(query)

    rows: list[dict[str, str]] = []

    variables = cast(
        list[Any],
        results.vars or [],
    )

    for result in results:

        values = cast(
            list[Any],
            result,
        )

        rows.append(
            {
                str(var): str(value)
                for var, value in zip(
                    variables,
                    values,
                )
            }
        )

    df = pd.DataFrame(rows)

    output_file = (
        OUTPUT_DIR
        / f"{rule_name}.csv"
    )

    df.to_csv(
        output_file,
        index=False,
    )

    violation_count = len(df)

    summary.append(
        {
            "rule_name": rule_name,
            "violations": violation_count,
            "status": (
                "FAIL"
                if violation_count > 0
                else "PASS"
            ),
        }
    )

    print(
        f"{rule_name}: {violation_count} violation(s)"
    )


# ============================================================
# SAVE SUMMARY
# ============================================================

summary_df = pd.DataFrame(summary)

summary_file = (
    OUTPUT_DIR
    / "sparql_validation_summary.csv"
)

summary_df.to_csv(
    summary_file,
    index=False,
)


print("\n")
print("=" * 60)
print("GSIS STAGE 6 - SPARQL VALIDATION COMPLETE")
print("=" * 60)

print(
    summary_df.to_string(
        index=False
    )
)

print(
    f"\nSummary saved to:\n{summary_file}"
)