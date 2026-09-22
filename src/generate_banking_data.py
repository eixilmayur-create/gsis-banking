# ============================================================
# GSIS - STAGE 1
# MULTI-SOURCE RETAIL BANKING DATA GENERATOR
# ============================================================
#
# Purpose:
# --------
# This script simulates several independent banking systems.
#
# Each system uses slightly different terminology for similar
# business concepts. This reproduces a common enterprise problem:
#
# Core Banking -> Customer
# CRM          -> Client
# Cards        -> Card Holder
# Fraud        -> Subject
#
# Later stages of GSIS will determine whether these terms should:
#
#   1. REUSE an existing ontology concept
#   2. MAP to another concept
#   3. CREATE a genuinely new ontology concept
#   4. Be escalated for HUMAN REVIEW
#
# ============================================================


from pathlib import Path
import random
from typing import Any

import numpy as np
import pandas as pd
from faker import Faker


# ============================================================
# 1. RANDOM SEED
# ============================================================
#
# Setting a fixed seed means that every time we run the script
# we get the same dataset.
#
# This is important for reproducible experiments.
# ============================================================

SEED = 42

random.seed(SEED)
np.random.seed(SEED)

fake = Faker("en_IN")
Faker.seed(SEED)


# ============================================================
# 2. PROJECT PATHS
# ============================================================
#
# __file__ points to:
#
# gsis-banking/src/generate_banking_data.py
#
# parents[1] therefore gives:
#
# gsis-banking/
#
# This avoids hardcoding Windows paths.
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = PROJECT_ROOT / "data" / "raw"

CORE_BANKING_DIR = RAW_DIR / "core_banking"
CRM_DIR = RAW_DIR / "crm"
CARDS_DIR = RAW_DIR / "cards"
PAYMENTS_DIR = RAW_DIR / "payments"
FRAUD_DIR = RAW_DIR / "fraud"

SCHEMA_DIR = PROJECT_ROOT / "data" / "schemas"


# ============================================================
# 3. ENSURE DIRECTORIES EXIST
# ============================================================

for directory in [
    CORE_BANKING_DIR,
    CRM_DIR,
    CARDS_DIR,
    PAYMENTS_DIR,
    FRAUD_DIR,
    SCHEMA_DIR,
]:
    directory.mkdir(parents=True, exist_ok=True)


# ============================================================
# 4. DATASET SIZE
# ============================================================
#
# We deliberately keep the dataset small enough for learning.
#
# The complexity of GSIS comes from schema meaning,
# not from millions of rows.
# ============================================================

NUM_CUSTOMERS = 500
NUM_ACCOUNTS = 700
NUM_CARDS = 450
NUM_TRANSACTIONS = 2000
NUM_RISK_EVENTS = 250
NUM_CRM_RECORDS = 550


# ============================================================
# 5. REFERENCE VALUES
# ============================================================

CUSTOMER_SEGMENTS = [
    "Retail",
    "Premium",
    "Salary",
    "Student",
    "Senior Citizen",
]

ACCOUNT_TYPES = [
    "Savings",
    "Current",
    "Salary",
]

ACCOUNT_STATUS = [
    "ACTIVE",
    "DORMANT",
    "BLOCKED",
]

CARD_TYPES = [
    "Debit",
    "Credit",
]

CARD_NETWORKS = [
    "Visa",
    "Mastercard",
    "RuPay",
]

TRANSACTION_TYPES = [
    "UPI",
    "NEFT",
    "IMPS",
    "CARD_PURCHASE",
    "ATM_WITHDRAWAL",
]

CHANNELS = [
    "MOBILE",
    "WEB",
    "ATM",
    "POS",
    "BRANCH",
]

CURRENCIES = [
    "INR",
    "USD",
    "EUR",
]

MERCHANT_CATEGORIES = [
    "GROCERY",
    "ELECTRONICS",
    "TRAVEL",
    "RESTAURANT",
    "PHARMACY",
    "FUEL",
]

RISK_TYPES = [
    "HIGH_VALUE_TRANSACTION",
    "VELOCITY_ALERT",
    "UNUSUAL_LOCATION",
    "DEVICE_MISMATCH",
    "SUSPICIOUS_MERCHANT",
]

RISK_LEVELS = [
    "LOW",
    "MEDIUM",
    "HIGH",
    "CRITICAL",
]


# ============================================================
# 6. GENERATE CORE BANKING CUSTOMERS
# ============================================================
#
# Core Banking uses canonical-looking terminology:
#
# customer_id
# customer_name
# customer_segment
#
# Later CRM and Cards will use different names for the same
# underlying concept.
# ============================================================

customers: list[dict[str, Any]] = []

for i in range(1, NUM_CUSTOMERS + 1):

    customer_id = f"CUST{i:05d}"

    customers.append(
        {
            "customer_id": customer_id,
            "customer_name": fake.name(),
            "date_of_birth": fake.date_of_birth(
                minimum_age=18,
                maximum_age=80,
            ),
            "email": fake.email(),
            "mobile_number": fake.msisdn()[-10:],
            "customer_segment": random.choice(CUSTOMER_SEGMENTS),
            "city": fake.city(),
            "state": fake.state(),
            "kyc_status": random.choice(
                ["VERIFIED", "VERIFIED", "VERIFIED", "PENDING"]
            ),
        }
    )


customers_df = pd.DataFrame(customers)


# ============================================================
# 7. GENERATE BANK ACCOUNTS
# ============================================================
#
# Every account should normally belong to a customer.
#
# Later SHACL will enforce this.
# ============================================================

accounts: list[dict[str, Any]] = []

for i in range(1, NUM_ACCOUNTS + 1):

    customer = customers_df.sample(1).iloc[0]

    accounts.append(
        {
            "account_id": f"ACC{i:06d}",
            "customer_id": customer["customer_id"],
            "account_type": random.choice(ACCOUNT_TYPES),
            "account_status": random.choice(ACCOUNT_STATUS),
            "currency_code": "INR",
            "balance": round(random.uniform(500, 1_000_000), 2),
            "branch_code": f"BR{random.randint(1, 30):03d}",
            "opened_date": fake.date_between(
                start_date="-10y",
                end_date="today",
            ),
        }
    )


accounts_df = pd.DataFrame(accounts)


# ============================================================
# 8. GENERATE CRM CUSTOMER DATA
# ============================================================
#
# Here the same Customer concept is represented differently.
#
# customer_id      -> client_id
# customer_name    -> client_name
# customer_segment -> client_type
#
# Some CRM records represent prospects who do NOT yet exist
# in Core Banking.
#
# This makes the mapping problem more realistic.
# ============================================================

crm_records: list[dict[str, Any]] = []


# ------------------------------------------------------------
# Existing customers copied into CRM
# ------------------------------------------------------------

existing_crm_count = 475

crm_customer_sample = customers_df.sample(
    existing_crm_count,
    random_state=SEED,
)


for _, customer in crm_customer_sample.iterrows():

    crm_records.append(
        {
            "client_id": customer["customer_id"],
            "client_name": customer["customer_name"],
            "client_type": customer["customer_segment"],
            "contact_email": customer["email"],
            "relationship_status": random.choice(
                [
                    "ACTIVE",
                    "ACTIVE",
                    "ACTIVE",
                    "INACTIVE",
                ]
            ),
            "preferred_channel": random.choice(
                [
                    "EMAIL",
                    "PHONE",
                    "MOBILE_APP",
                    "BRANCH",
                ]
            ),
        }
    )


# ------------------------------------------------------------
# CRM-only prospects
# ------------------------------------------------------------

prospect_count = NUM_CRM_RECORDS - existing_crm_count

for i in range(1, prospect_count + 1):

    crm_records.append(
        {
            "client_id": f"PROSPECT{i:04d}",
            "client_name": fake.name(),
            "client_type": "Prospect",
            "contact_email": fake.email(),
            "relationship_status": "PROSPECT",
            "preferred_channel": random.choice(
                [
                    "EMAIL",
                    "PHONE",
                    "MOBILE_APP",
                ]
            ),
        }
    )


crm_df = pd.DataFrame(crm_records)


# ============================================================
# 9. GENERATE CARD SYSTEM DATA
# ============================================================
#
# Card system uses:
#
# card_holder_id
#
# instead of:
#
# customer_id
#
# Semantically they frequently refer to the same entity.
# ============================================================

cards: list[dict[str, Any]] = []

eligible_customers = customers_df.sample(
    NUM_CARDS,
    random_state=SEED,
)


for i, (_, customer) in enumerate(
    eligible_customers.iterrows(),
    start=1,
):

    customer_account_ids = [
        account["account_id"]
        for account in accounts
        if account["customer_id"] == customer["customer_id"]
    ]

    if customer_account_ids:

        account_id = customer_account_ids[0]

    else:

        account_id = random.choice(
            accounts_df["account_id"].tolist()
        )

    cards.append(
        {
            "card_id": f"CARD{i:06d}",
            "card_holder_id": customer["customer_id"],
            "holder_name": customer["customer_name"],
            "linked_account_ref": account_id,
            "card_type": random.choice(CARD_TYPES),
            "card_network": random.choice(CARD_NETWORKS),
            "card_status": random.choice(
                [
                    "ACTIVE",
                    "ACTIVE",
                    "ACTIVE",
                    "BLOCKED",
                ]
            ),
            "expiry_year": random.randint(2027, 2032),
        }
    )


cards_df = pd.DataFrame(cards)


# ============================================================
# 10. GENERATE TRANSACTIONS
# ============================================================
#
# Transaction records reference bank accounts.
#
# Merchant information is included because later we will use
# Merchant vs Customer as an example of semantic collision.
# ============================================================

transactions: list[dict[str, Any]] = []

for i in range(1, NUM_TRANSACTIONS + 1):

    account = accounts_df.sample(1).iloc[0]

    transaction_type = random.choice(TRANSACTION_TYPES)

    amount = round(
        random.uniform(10, 250_000),
        2,
    )

    transactions.append(
        {
            "transaction_id": f"TXN{i:07d}",
            "account_ref": account["account_id"],
            "customer_ref": account["customer_id"],
            "transaction_type": transaction_type,
            "transaction_amount": amount,
            "currency": random.choices(
                CURRENCIES,
                weights=[0.96, 0.025, 0.015],
            )[0],
            "transaction_channel": random.choice(CHANNELS),
            "merchant_ref": f"MERCH{random.randint(1, 120):04d}",
            "merchant_category": random.choice(
                MERCHANT_CATEGORIES
            ),
            "transaction_date": fake.date_time_between(
                start_date="-1y",
                end_date="now",
            ),
        }
    )


transactions_df = pd.DataFrame(transactions)


# ============================================================
# 11. GENERATE FRAUD / RISK EVENTS
# ============================================================
#
# Fraud systems often use generic terminology such as:
#
# subject_id
#
# rather than:
#
# customer_id
#
# This creates another semantic mapping challenge.
# ============================================================

risk_events: list[dict[str, Any]] = []

sample_transactions = transactions_df.sample(
    NUM_RISK_EVENTS,
    random_state=SEED,
)


for i, (_, transaction) in enumerate(
    sample_transactions.iterrows(),
    start=1,
):

    risk_score = round(
        random.uniform(0.20, 0.99),
        3,
    )

    if risk_score >= 0.90:
        risk_level = "CRITICAL"

    elif risk_score >= 0.75:
        risk_level = "HIGH"

    elif risk_score >= 0.50:
        risk_level = "MEDIUM"

    else:
        risk_level = "LOW"

    risk_events.append(
        {
            "risk_event_id": f"RISK{i:05d}",
            "subject_id": transaction["customer_ref"],
            "subject_type": "PERSON",
            "transaction_ref": transaction["transaction_id"],
            "risk_type": random.choice(RISK_TYPES),
            "risk_score": risk_score,
            "risk_level": risk_level,
            "investigation_status": random.choice(
                [
                    "OPEN",
                    "UNDER_REVIEW",
                    "CLOSED",
                ]
            ),
        }
    )


risk_df = pd.DataFrame(risk_events)


# ============================================================
# 12. INTRODUCE CONTROLLED DATA DEFECTS
# ============================================================
#
# IMPORTANT:
#
# These defects are deliberate.
#
# Later SHACL and SPARQL validation should discover them.
#
# We keep them small so we know exactly what the expected
# validation behaviour should be.
# ============================================================


# ------------------------------------------------------------
# DEFECT 1:
# Account refers to a customer that does not exist.
# ------------------------------------------------------------

accounts_df.loc[
    0,
    "customer_id",
] = "CUST99999"


# ------------------------------------------------------------
# DEFECT 2:
# Invalid currency code.
# ------------------------------------------------------------

transactions_df.loc[
    1,
    "currency",
] = "XYZ"


# ------------------------------------------------------------
# DEFECT 3:
# Negative transaction amount.
# ------------------------------------------------------------

transactions_df.loc[
    2,
    "transaction_amount",
] = -5000.00


# ------------------------------------------------------------
# DEFECT 4:
# Card points to a non-existing account.
# ------------------------------------------------------------

cards_df.loc[
    3,
    "linked_account_ref",
] = "ACC999999"


# ------------------------------------------------------------
# DEFECT 5:
# Risk event references missing transaction.
# ------------------------------------------------------------

risk_df.loc[
    4,
    "transaction_ref",
] = "TXN9999999"


# ============================================================
# 13. SAVE RAW DATA
# ============================================================

customers_df.to_csv(
    CORE_BANKING_DIR / "customers.csv",
    index=False,
)

accounts_df.to_csv(
    CORE_BANKING_DIR / "accounts.csv",
    index=False,
)

crm_df.to_csv(
    CRM_DIR / "crm_customers.csv",
    index=False,
)

cards_df.to_csv(
    CARDS_DIR / "cards.csv",
    index=False,
)

transactions_df.to_csv(
    PAYMENTS_DIR / "transactions.csv",
    index=False,
)

risk_df.to_csv(
    FRAUD_DIR / "risk_events.csv",
    index=False,
)


# ============================================================
# 14. EXISTING ONTOLOGY TERMS
# ============================================================
#
# These represent concepts that supposedly already exist in
# the bank's enterprise ontology.
#
# Later we will convert these into RDF/OWL.
# ============================================================

existing_ontology_terms = [
    {
        "term": "Customer",
        "term_type": "Class",
        "description":
            "Individual maintaining a banking relationship with the bank.",
    },
    {
        "term": "Party",
        "term_type": "Class",
        "description":
            "Generic person or organisation participating in a business relationship.",
    },
    {
        "term": "Merchant",
        "term_type": "Class",
        "description":
            "Business entity receiving payment for goods or services.",
    },
    {
        "term": "Account",
        "term_type": "Class",
        "description":
            "Financial account maintained for a customer.",
    },
    {
        "term": "Card",
        "term_type": "Class",
        "description":
            "Payment card issued to a customer and linked to an account.",
    },
    {
        "term": "Transaction",
        "term_type": "Class",
        "description":
            "Financial movement of value associated with an account.",
    },
    {
        "term": "RiskEvent",
        "term_type": "Class",
        "description":
            "Risk or fraud event associated with banking activity.",
    },
    {
        "term": "Branch",
        "term_type": "Class",
        "description":
            "Physical bank location serving customers.",
    },
    {
        "term": "PaymentChannel",
        "term_type": "Class",
        "description":
            "Channel through which a financial transaction is initiated.",
    },
]


ontology_terms_df = pd.DataFrame(
    existing_ontology_terms
)

ontology_terms_df.to_csv(
    SCHEMA_DIR / "existing_ontology_terms.csv",
    index=False,
)


# ============================================================
# 15. INCOMING SCHEMA TERMS
# ============================================================
#
# Imagine these are terms discovered from newly integrated
# source systems.
#
# GSIS must determine whether they should map to existing
# concepts or become new ontology elements.
# ============================================================

incoming_terms = [
    {
        "source_system": "CRM",
        "incoming_term": "client",
        "description":
            "Person maintaining or potentially establishing a relationship with the bank.",
    },
    {
        "source_system": "CRM",
        "incoming_term": "client_id",
        "description":
            "Unique identifier assigned to a banking client.",
    },
    {
        "source_system": "Cards",
        "incoming_term": "card_holder",
        "description":
            "Customer to whom a payment card has been issued.",
    },
    {
        "source_system": "Cards",
        "incoming_term": "card_holder_id",
        "description":
            "Identifier of the customer holding the card.",
    },
    {
        "source_system": "Payments",
        "incoming_term": "account_ref",
        "description":
            "Reference to the financial account used in a transaction.",
    },
    {
        "source_system": "Payments",
        "incoming_term": "merchant_ref",
        "description":
            "Identifier of a merchant receiving payment.",
    },
    {
        "source_system": "Payments",
        "incoming_term": "payment_event",
        "description":
            "Financial event representing transfer or movement of money.",
    },
    {
        "source_system": "Fraud",
        "incoming_term": "subject",
        "description":
            "Person being evaluated in a fraud or risk investigation.",
    },
    {
        "source_system": "Fraud",
        "incoming_term": "fraud_case",
        "description":
            "Risk investigation event generated from suspicious banking activity.",
    },
    {
        "source_system": "DigitalBanking",
        "incoming_term": "mobile_wallet",
        "description":
            "Digital wallet allowing customers to store value and initiate payments.",
    },
    {
        "source_system": "Lending",
        "incoming_term": "borrower",
        "description":
            "Customer who has obtained a loan from the bank.",
    },
    {
        "source_system": "ATM",
        "incoming_term": "terminal",
        "description":
            "Physical or electronic terminal where banking transactions occur.",
    },
]


incoming_terms_df = pd.DataFrame(
    incoming_terms
)

incoming_terms_df.to_csv(
    SCHEMA_DIR / "incoming_schema_terms.csv",
    index=False,
)


# ============================================================
# 16. MAPPING GROUND TRUTH
# ============================================================
#
# This file is extremely important.
#
# It gives us known correct answers.
#
# Later:
#
# Gemini prediction
#       vs
# Ground truth
#
# lets us measure actual mapping accuracy.
#
# CREATE_NEW means the existing ontology does not yet contain
# an appropriate concept.
# ============================================================

ground_truth = [
    {
        "incoming_term": "client",
        "expected_mapping": "Customer",
        "expected_action": "REUSE",
    },
    {
        "incoming_term": "client_id",
        "expected_mapping": "Customer",
        "expected_action": "REUSE",
    },
    {
        "incoming_term": "card_holder",
        "expected_mapping": "Customer",
        "expected_action": "REUSE",
    },
    {
        "incoming_term": "card_holder_id",
        "expected_mapping": "Customer",
        "expected_action": "REUSE",
    },
    {
        "incoming_term": "account_ref",
        "expected_mapping": "Account",
        "expected_action": "REUSE",
    },
    {
        "incoming_term": "merchant_ref",
        "expected_mapping": "Merchant",
        "expected_action": "REUSE",
    },
    {
        "incoming_term": "payment_event",
        "expected_mapping": "Transaction",
        "expected_action": "REUSE",
    },
    {
        "incoming_term": "subject",
        "expected_mapping": "Customer",
        "expected_action": "REUSE",
    },
    {
        "incoming_term": "fraud_case",
        "expected_mapping": "RiskEvent",
        "expected_action": "REUSE",
    },
    {
        "incoming_term": "mobile_wallet",
        "expected_mapping": "DigitalWallet",
        "expected_action": "CREATE_NEW",
    },
    {
        "incoming_term": "borrower",
        "expected_mapping": "Customer",
        "expected_action": "REUSE",
    },
    {
        "incoming_term": "terminal",
        "expected_mapping": "TransactionTerminal",
        "expected_action": "CREATE_NEW",
    },
]


ground_truth_df = pd.DataFrame(
    ground_truth
)

ground_truth_df.to_csv(
    SCHEMA_DIR / "mapping_ground_truth.csv",
    index=False,
)


# ============================================================
# 17. PRINT DATASET SUMMARY
# ============================================================

print("\n")
print("=" * 65)
print("GSIS STAGE 1 - BANKING DATA GENERATION COMPLETE")
print("=" * 65)

print(
    f"Customers:              {len(customers_df):,}"
)

print(
    f"Accounts:               {len(accounts_df):,}"
)

print(
    f"CRM records:            {len(crm_df):,}"
)

print(
    f"Cards:                  {len(cards_df):,}"
)

print(
    f"Transactions:           {len(transactions_df):,}"
)

print(
    f"Risk events:            {len(risk_df):,}"
)

total_records = (
    len(customers_df)
    + len(accounts_df)
    + len(crm_df)
    + len(cards_df)
    + len(transactions_df)
    + len(risk_df)
)

print("-" * 65)

print(
    f"TOTAL SOURCE RECORDS:   {total_records:,}"
)

print("-" * 65)

print(
    f"Existing ontology terms: {len(ontology_terms_df)}"
)

print(
    f"Incoming schema terms:   {len(incoming_terms_df)}"
)

print(
    f"Ground truth mappings:   {len(ground_truth_df)}"
)

print("=" * 65)

print(
    "\nControlled defects inserted:"
)

print(
    "1. Account with missing customer"
)

print(
    "2. Invalid transaction currency"
)

print(
    "3. Negative transaction amount"
)

print(
    "4. Card with missing account"
)

print(
    "5. Risk event with missing transaction"
)

print(
    "\nStage 1 completed successfully."
)

print(
    "\nNext stage: Automated Schema Profiling."
)