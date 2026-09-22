# ============================================================
# GSIS - STAGE 4
# CSV -> RDF KNOWLEDGE GRAPH
# ============================================================
#
# Purpose:
# --------
# Convert multi-source banking CSV data into RDF triples.
#
# Stage 3 created the ontology (TBox).
# Stage 4 creates instance data (ABox).
#
# The final graph will contain:
#
# Customer
# Account
# Card
# Transaction
# Merchant
# Branch
# PaymentChannel
# RiskEvent
#
# plus relationships between them.
# ============================================================


from pathlib import Path
from decimal import Decimal
from typing import Any

import pandas as pd

from rdflib import (
    Graph,
    Namespace,
    URIRef,
    Literal,
)

from rdflib.namespace import (
    RDF,
    RDFS,
    XSD,
)


# ============================================================
# 1. PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = PROJECT_ROOT / "data" / "raw"

ONTOLOGY_FILE = (
    PROJECT_ROOT
    / "ontology"
    / "banking_ontology.ttl"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "rdf"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# 2. SOURCE FILES
# ============================================================

CUSTOMERS_FILE = (
    RAW_DIR
    / "core_banking"
    / "customers.csv"
)

ACCOUNTS_FILE = (
    RAW_DIR
    / "core_banking"
    / "accounts.csv"
)

CARDS_FILE = (
    RAW_DIR
    / "cards"
    / "cards.csv"
)

TRANSACTIONS_FILE = (
    RAW_DIR
    / "payments"
    / "transactions.csv"
)

RISK_FILE = (
    RAW_DIR
    / "fraud"
    / "risk_events.csv"
)


# ============================================================
# 3. NAMESPACES
# ============================================================
#
# Ontology namespace
# ============================================================

EX = Namespace(
    "http://example.org/gsis/banking#"
)

DATA = Namespace(
    "http://example.org/gsis/banking/data/"
)


# ============================================================
# 4. CREATE GRAPH
# ============================================================

graph = Graph()

graph.bind(
    "ex",
    EX,
)

graph.bind(
    "data",
    DATA,
)

graph.bind(
    "rdf",
    RDF,
)

graph.bind(
    "rdfs",
    RDFS,
)

graph.bind(
    "xsd",
    XSD,
)


# ============================================================
# 5. HELPER FUNCTIONS
# ============================================================


def clean_string(value: Any) -> str | None:
    """
    Convert a value into a clean string.

    Missing values become None.
    """

    if pd.isna(value):
        return None

    return str(value).strip()


def make_uri(entity_type: Any, identifier: Any) -> URIRef:
    """
    Build a stable URI for an entity.

    Example:

    entity_type = Customer
    identifier  = CUST00001

    URI:

    http://example.org/gsis/banking/data/Customer/CUST00001
    """

    identifier = str(identifier).strip()

    identifier = (
        identifier
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
    )

    return URIRef(
        f"{DATA}{entity_type}/{identifier}"
    )


def add_string(
    subject: Any,
    predicate: Any,
    value: Any,
) -> None:
    """
    Add string literal only when value exists.
    """

    value = clean_string(
        value
    )

    if value is not None:

        graph.add(
            (
                subject,
                predicate,
                Literal(
                    value,
                    datatype=XSD.string,
                ),
            )
        )


def add_decimal(
    subject: Any,
    predicate: Any,
    value: Any,
) -> None:
    """
    Add decimal value safely.
    """

    if pd.isna(value):
        return

    try:

        decimal_value = Decimal(
            str(value)
        )

        graph.add(
            (
                subject,
                predicate,
                Literal(
                    decimal_value,
                    datatype=XSD.decimal,
                ),
            )
        )

    except Exception:

        # Invalid numeric values are skipped here.
        #
        # Later semantic validation will focus on
        # values successfully transformed into RDF.
        pass


def add_integer(
    subject: Any,
    predicate: Any,
    value: Any,
) -> None:

    if pd.isna(value):
        return

    try:

        integer_value = int(
            value
        )

        graph.add(
            (
                subject,
                predicate,
                Literal(
                    integer_value,
                    datatype=XSD.integer,
                ),
            )
        )

    except Exception:
        pass


def add_date(
    subject: Any,
    predicate: Any,
    value: Any,
) -> None:

    if pd.isna(value):
        return

    try:

        parsed = str(
            pd.to_datetime(
                str(value)
            )
        ).split(" ")[0]

        graph.add(
            (
                subject,
                predicate,
                Literal(
                    parsed,
                    datatype=XSD.date,
                ),
            )
        )

    except Exception:
        pass


def add_datetime(
    subject: Any,
    predicate: Any,
    value: Any,
) -> None:

    if pd.isna(value):
        return

    try:

        parsed = str(
            pd.to_datetime(
                str(value)
            )
        )

        graph.add(
            (
                subject,
                predicate,
                Literal(
                    parsed,
                    datatype=XSD.dateTime,
                ),
            )
        )

    except Exception:
        pass


# ============================================================
# 6. LOAD CSV FILES
# ============================================================

customers_df = pd.read_csv(
    CUSTOMERS_FILE
)

accounts_df = pd.read_csv(
    ACCOUNTS_FILE
)

cards_df = pd.read_csv(
    CARDS_FILE
)

transactions_df = pd.read_csv(
    TRANSACTIONS_FILE
)

risk_df = pd.read_csv(
    RISK_FILE
)


# ============================================================
# 7. CUSTOMER ENTITIES
# ============================================================

print(
    "Creating Customer entities..."
)

for _, row in customers_df.iterrows():

    customer_uri = make_uri(
        "Customer",
        row["customer_id"],
    )

    # --------------------------------------------------------
    # Type
    # --------------------------------------------------------

    graph.add(
        (
            customer_uri,
            RDF.type,
            EX.Customer,
        )
    )

    # --------------------------------------------------------
    # Attributes
    # --------------------------------------------------------

    add_string(
        customer_uri,
        EX.customerId,
        row["customer_id"],
    )

    add_string(
        customer_uri,
        EX.customerName,
        row["customer_name"],
    )

    add_date(
        customer_uri,
        EX.dateOfBirth,
        row["date_of_birth"],
    )

    add_string(
        customer_uri,
        EX.email,
        row["email"],
    )

    add_string(
        customer_uri,
        EX.mobileNumber,
        row["mobile_number"],
    )

    add_string(
        customer_uri,
        EX.customerSegment,
        row["customer_segment"],
    )

    add_string(
        customer_uri,
        EX.kycStatus,
        row["kyc_status"],
    )


# ============================================================
# 8. BRANCH ENTITIES
# ============================================================
#
# Branches do not have a separate CSV.
#
# They are derived from:
#
# accounts.branch_code
#
# This is a normal graph modelling technique:
#
# a repeated categorical reference becomes an entity.
# ============================================================

print(
    "Creating Branch entities..."
)

branch_codes = (
    accounts_df["branch_code"]
    .dropna()
    .unique()
)

for branch_code in branch_codes:

    branch_uri = make_uri(
        "Branch",
        branch_code,
    )

    graph.add(
        (
            branch_uri,
            RDF.type,
            EX.Branch,
        )
    )

    add_string(
        branch_uri,
        EX.branchCode,
        branch_code,
    )


# ============================================================
# 9. ACCOUNT ENTITIES
# ============================================================

print(
    "Creating Account entities..."
)

for _, row in accounts_df.iterrows():

    account_uri = make_uri(
        "Account",
        row["account_id"],
    )

    graph.add(
        (
            account_uri,
            RDF.type,
            EX.Account,
        )
    )

    add_string(
        account_uri,
        EX.accountId,
        row["account_id"],
    )

    add_string(
        account_uri,
        EX.accountType,
        row["account_type"],
    )

    add_string(
        account_uri,
        EX.accountStatus,
        row["account_status"],
    )

    add_string(
        account_uri,
        EX.currencyCode,
        row["currency_code"],
    )

    add_decimal(
        account_uri,
        EX.accountBalance,
        row["balance"],
    )

    add_date(
        account_uri,
        EX.openedDate,
        row["opened_date"],
    )

    # --------------------------------------------------------
    # Account -> Customer
    # --------------------------------------------------------
    #
    # Important:
    #
    # If customer_id is CUST99999,
    # we STILL create the relationship URI.
    #
    # But CUST99999 does not exist as a Customer instance.
    #
    # That gives later SPARQL validation something to detect.
    # --------------------------------------------------------

    customer_uri = make_uri(
        "Customer",
        row["customer_id"],
    )

    graph.add(
        (
            account_uri,
            EX.heldBy,
            customer_uri,
        )
    )

    graph.add(
        (
            customer_uri,
            EX.ownsAccount,
            account_uri,
        )
    )

    # --------------------------------------------------------
    # Account -> Branch
    # --------------------------------------------------------

    branch_uri = make_uri(
        "Branch",
        row["branch_code"],
    )

    graph.add(
        (
            account_uri,
            EX.servicedByBranch,
            branch_uri,
        )
    )


# ============================================================
# 10. CARD ENTITIES
# ============================================================

print(
    "Creating Card entities..."
)

for _, row in cards_df.iterrows():

    card_uri = make_uri(
        "Card",
        row["card_id"],
    )

    graph.add(
        (
            card_uri,
            RDF.type,
            EX.Card,
        )
    )

    add_string(
        card_uri,
        EX.cardId,
        row["card_id"],
    )

    add_string(
        card_uri,
        EX.cardType,
        row["card_type"],
    )

    add_string(
        card_uri,
        EX.cardNetwork,
        row["card_network"],
    )

    add_string(
        card_uri,
        EX.cardStatus,
        row["card_status"],
    )

    add_integer(
        card_uri,
        EX.expiryYear,
        row["expiry_year"],
    )

    # --------------------------------------------------------
    # Customer -> Card
    # --------------------------------------------------------

    customer_uri = make_uri(
        "Customer",
        row["card_holder_id"],
    )

    graph.add(
        (
            customer_uri,
            EX.holdsCard,
            card_uri,
        )
    )

    # --------------------------------------------------------
    # Card -> Account
    # --------------------------------------------------------

    account_uri = make_uri(
        "Account",
        row["linked_account_ref"],
    )

    graph.add(
        (
            card_uri,
            EX.linkedToAccount,
            account_uri,
        )
    )


# ============================================================
# 11. PAYMENT CHANNEL ENTITIES
# ============================================================

print(
    "Creating PaymentChannel entities..."
)

channels = (
    transactions_df[
        "transaction_channel"
    ]
    .dropna()
    .unique()
)

for channel in channels:

    channel_uri = make_uri(
        "PaymentChannel",
        channel,
    )

    graph.add(
        (
            channel_uri,
            RDF.type,
            EX.PaymentChannel,
        )
    )

    add_string(
        channel_uri,
        EX.channelName,
        channel,
    )


# ============================================================
# 12. MERCHANT ENTITIES
# ============================================================
#
# Merchant entities are derived from transaction data.
#
# Multiple transactions may point to the same merchant.
# ============================================================

print(
    "Creating Merchant entities..."
)

merchant_rows = (
    transactions_df[
        [
            "merchant_ref",
            "merchant_category",
        ]
    ]
    .drop_duplicates(
        subset=[
            "merchant_ref"
        ]
    )
)


for _, row in merchant_rows.iterrows():

    merchant_uri = make_uri(
        "Merchant",
        row["merchant_ref"],
    )

    graph.add(
        (
            merchant_uri,
            RDF.type,
            EX.Merchant,
        )
    )

    add_string(
        merchant_uri,
        EX.merchantId,
        row["merchant_ref"],
    )

    add_string(
        merchant_uri,
        EX.merchantCategory,
        row["merchant_category"],
    )


# ============================================================
# 13. TRANSACTION ENTITIES
# ============================================================

print(
    "Creating Transaction entities..."
)

for _, row in transactions_df.iterrows():

    transaction_uri = make_uri(
        "Transaction",
        row["transaction_id"],
    )

    # --------------------------------------------------------
    # Determine subclass
    # --------------------------------------------------------

    transaction_type = str(
        row["transaction_type"]
    )

    if transaction_type == "CARD_PURCHASE":

        transaction_class = (
            EX.CardTransaction
        )

    elif transaction_type in {
        "NEFT",
        "IMPS",
        "UPI",
    }:

        transaction_class = (
            EX.BankTransfer
        )

    elif transaction_type == "ATM_WITHDRAWAL":

        transaction_class = (
            EX.CashWithdrawal
        )

    else:

        transaction_class = (
            EX.Transaction
        )

    graph.add(
        (
            transaction_uri,
            RDF.type,
            transaction_class,
        )
    )

    # --------------------------------------------------------
    # Also explicitly type every subtype as Transaction.
    #
    # This makes downstream querying easier even without an
    # OWL reasoner.
    # --------------------------------------------------------

    graph.add(
        (
            transaction_uri,
            RDF.type,
            EX.Transaction,
        )
    )

    # --------------------------------------------------------
    # Attributes
    # --------------------------------------------------------

    add_string(
        transaction_uri,
        EX.transactionId,
        row["transaction_id"],
    )

    add_string(
        transaction_uri,
        EX.transactionType,
        row["transaction_type"],
    )

    add_decimal(
        transaction_uri,
        EX.transactionAmount,
        row["transaction_amount"],
    )

    add_string(
        transaction_uri,
        EX.transactionCurrency,
        row["currency"],
    )

    add_datetime(
        transaction_uri,
        EX.transactionDate,
        row["transaction_date"],
    )

    # --------------------------------------------------------
    # Transaction -> Account
    # --------------------------------------------------------

    account_uri = make_uri(
        "Account",
        row["account_ref"],
    )

    graph.add(
        (
            transaction_uri,
            EX.usesAccount,
            account_uri,
        )
    )

    # --------------------------------------------------------
    # Transaction -> Customer
    # --------------------------------------------------------

    customer_uri = make_uri(
        "Customer",
        row["customer_ref"],
    )

    graph.add(
        (
            transaction_uri,
            EX.initiatedBy,
            customer_uri,
        )
    )

    graph.add(
        (
            customer_uri,
            EX.initiatesTransaction,
            transaction_uri,
        )
    )

    # --------------------------------------------------------
    # Transaction -> Merchant
    # --------------------------------------------------------

    merchant_uri = make_uri(
        "Merchant",
        row["merchant_ref"],
    )

    graph.add(
        (
            transaction_uri,
            EX.paidTo,
            merchant_uri,
        )
    )

    # --------------------------------------------------------
    # Transaction -> PaymentChannel
    # --------------------------------------------------------

    channel_uri = make_uri(
        "PaymentChannel",
        row["transaction_channel"],
    )

    graph.add(
        (
            transaction_uri,
            EX.usesChannel,
            channel_uri,
        )
    )


# ============================================================
# 14. RISK EVENT ENTITIES
# ============================================================

print(
    "Creating RiskEvent entities..."
)

for _, row in risk_df.iterrows():

    risk_uri = make_uri(
        "RiskEvent",
        row["risk_event_id"],
    )

    # --------------------------------------------------------
    # Fraud-oriented source data becomes FraudAlert.
    # --------------------------------------------------------

    graph.add(
        (
            risk_uri,
            RDF.type,
            EX.FraudAlert,
        )
    )

    graph.add(
        (
            risk_uri,
            RDF.type,
            EX.RiskEvent,
        )
    )

    add_string(
        risk_uri,
        EX.riskEventId,
        row["risk_event_id"],
    )

    add_string(
        risk_uri,
        EX.riskType,
        row["risk_type"],
    )

    add_decimal(
        risk_uri,
        EX.riskScore,
        row["risk_score"],
    )

    add_string(
        risk_uri,
        EX.riskLevel,
        row["risk_level"],
    )

    add_string(
        risk_uri,
        EX.investigationStatus,
        row["investigation_status"],
    )

    # --------------------------------------------------------
    # Risk Event -> Customer
    # --------------------------------------------------------

    customer_uri = make_uri(
        "Customer",
        row["subject_id"],
    )

    graph.add(
        (
            risk_uri,
            EX.concernsCustomer,
            customer_uri,
        )
    )

    # --------------------------------------------------------
    # Risk Event -> Transaction
    #
    # Deliberate missing reference from Stage 1 is retained.
    # --------------------------------------------------------

    transaction_uri = make_uri(
        "Transaction",
        row["transaction_ref"],
    )

    graph.add(
        (
            risk_uri,
            EX.concernsTransaction,
            transaction_uri,
        )
    )

    graph.add(
        (
            transaction_uri,
            EX.triggeredRiskEvent,
            risk_uri,
        )
    )


# ============================================================
# 15. SAVE ABOX GRAPH
# ============================================================

ABOX_FILE = (
    OUTPUT_DIR
    / "banking_knowledge_graph.ttl"
)

graph.serialize(
    destination=str(
        ABOX_FILE
    ),
    format="turtle",
)


# ============================================================
# 16. CREATE COMPLETE GRAPH
# ============================================================
#
# Complete Graph =
#
# ontology TBox
# +
# instance ABox
# ============================================================

complete_graph = Graph()

complete_graph.parse(
    ONTOLOGY_FILE,
    format="turtle",
)

for triple in graph:

    complete_graph.add(
        triple
    )


COMPLETE_FILE = (
    OUTPUT_DIR
    / "banking_complete_graph.ttl"
)

complete_graph.serialize(
    destination=str(
        COMPLETE_FILE
    ),
    format="turtle",
)


# ============================================================
# 17. ENTITY COUNTER
# ============================================================

def count_entities(
    rdf_class: Any,
) -> int:

    return len(
        set(
            graph.subjects(
                RDF.type,
                rdf_class,
            )
        )
    )


# ============================================================
# 18. PRINT SUMMARY
# ============================================================

print("\n")

print("=" * 70)

print(
    "GSIS STAGE 4 - RDF KNOWLEDGE GRAPH COMPLETE"
)

print("=" * 70)

print(
    f"Customers:        {count_entities(EX.Customer):,}"
)

print(
    f"Accounts:         {count_entities(EX.Account):,}"
)

print(
    f"Cards:            {count_entities(EX.Card):,}"
)

print(
    f"Transactions:     {count_entities(EX.Transaction):,}"
)

print(
    f"Merchants:        {count_entities(EX.Merchant):,}"
)

print(
    f"Branches:         {count_entities(EX.Branch):,}"
)

print(
    f"Payment Channels: {count_entities(EX.PaymentChannel):,}"
)

print(
    f"Risk Events:      {count_entities(EX.RiskEvent):,}"
)

print("-" * 70)

print(
    f"ABox triples:     {len(graph):,}"
)

print(
    f"Complete triples: {len(complete_graph):,}"
)

print("-" * 70)

print(
    f"\nABox graph:\n{ABOX_FILE}"
)

print(
    f"\nComplete graph:\n{COMPLETE_FILE}"
)

print("\n")

print(
    "Controlled broken references have intentionally been retained."
)

print(
    "Stage 5 SHACL and Stage 6 SPARQL will detect them."
)

print("=" * 70)