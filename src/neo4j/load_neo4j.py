from pathlib import Path
import os
from typing import Any

import pandas as pd
from neo4j import GraphDatabase


PROJECT_ROOT = Path(__file__).resolve().parents[2]

CUSTOMERS_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "core_banking"
    / "customers.csv"
)

ACCOUNTS_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "core_banking"
    / "accounts.csv"
)

TRANSACTIONS_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "payments"
    / "transactions.csv"
)


URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USER") or os.getenv("NEO4J_USERNAME") or "neo4j"
PASSWORD = os.getenv("NEO4J_PASSWORD")
DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")
CLEAR_DATABASE = os.getenv("NEO4J_CLEAR_DATABASE", "false").lower() == "true"


def validate_configuration() -> None:
    missing = [
        name
        for name, value in {
            "NEO4J_URI": URI,
            "NEO4J_PASSWORD": PASSWORD,
        }.items()
        if not value
    ]
    if missing:
        names = ", ".join(missing)
        raise SystemExit(
            f"Missing Neo4j configuration: {names}.\n"
            "Set NEO4J_URI (for example neo4j://localhost:7687), "
            "NEO4J_USER/NEO4J_USERNAME, and NEO4J_PASSWORD before running."
        )


def load_csv(path: Path, required_columns: set[str]) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required input file not found: {path}")

    frame = pd.read_csv(path)
    missing_columns = required_columns.difference(frame.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"{path.name} is missing required columns: {missing}")
    return frame


def load_customer(tx: Any, row: pd.Series) -> None:

    tx.run(
        """
        MERGE (c:Customer {customer_id: $customer_id})
        SET c.name = $name,
            c.segment = $segment
        """,
        customer_id=row["customer_id"],
        name=row["customer_name"],
        segment=row["customer_segment"],
    )


def load_account(tx: Any, row: pd.Series) -> None:

    tx.run(
        """
        MERGE (a:Account {account_id: $account_id})
        SET a.type = $account_type,
            a.balance = $balance

        WITH a

        MATCH (c:Customer {customer_id: $customer_id})

        MERGE (c)-[:OWNS]->(a)
        """,
        account_id=row["account_id"],
        account_type=row["account_type"],
        balance=float(row["balance"]),
        customer_id=row["customer_id"],
    )


def load_transaction(tx: Any, row: pd.Series) -> None:

    tx.run(
        """
        MERGE (t:Transaction {
            transaction_id: $transaction_id
        })

        SET t.amount = $amount,
            t.type = $transaction_type,
            t.currency = $currency

        WITH t

        MATCH (a:Account {
            account_id: $account_id
        })

        MERGE (a)-[:HAS_TRANSACTION]->(t)

        WITH t

        MATCH (c:Customer {
            customer_id: $customer_id
        })

        MERGE (c)-[:INITIATED]->(t)
        """,
        transaction_id=row["transaction_id"],
        amount=float(row["transaction_amount"]),
        transaction_type=row["transaction_type"],
        currency=row["currency"],
        account_id=row["account_ref"],
        customer_id=row["customer_ref"],
    )


def main() -> None:
    validate_configuration()

    customers_df = load_csv(
        CUSTOMERS_FILE,
        {"customer_id", "customer_name", "customer_segment"},
    )
    accounts_df = load_csv(
        ACCOUNTS_FILE,
        {"account_id", "customer_id", "account_type", "balance"},
    )
    transactions_df = load_csv(
        TRANSACTIONS_FILE,
        {
            "transaction_id",
            "transaction_amount",
            "transaction_type",
            "currency",
            "account_ref",
            "customer_ref",
        },
    )

    driver = GraphDatabase.driver(
        URI,
        auth=(USER, PASSWORD),
    )

    try:
        driver.verify_connectivity()
        with driver.session(database=DATABASE) as session:
            if CLEAR_DATABASE:
                session.run("MATCH (n) DETACH DELETE n").consume()

            for _, row in customers_df.iterrows():
                session.execute_write(load_customer, row)

            for _, row in accounts_df.iterrows():
                session.execute_write(load_account, row)

            for _, row in transactions_df.iterrows():
                session.execute_write(load_transaction, row)
    except Exception as exc:
        raise SystemExit(f"Neo4j load failed: {exc}") from exc
    finally:
        driver.close()

    print(
        "Neo4j graph loaded successfully: "
        f"{len(customers_df)} customers, "
        f"{len(accounts_df)} accounts, and "
        f"{len(transactions_df)} transactions processed."
    )


if __name__ == "__main__":
    main()
