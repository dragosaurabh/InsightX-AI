#!/usr/bin/env python3
"""
InsightX AI - Sample Data Generator

Generates a synthetic transaction dataset for development and testing.
Creates realistic payment transaction data with configurable size.

Usage:
    python ingest_sample_data.py                    # 50k rows (default)
    python ingest_sample_data.py --rows 250000      # 250k rows
    python ingest_sample_data.py --output custom.csv --rows 100000
"""

import argparse
import csv
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

# Seed for reproducibility
random.seed(42)

# =============================================================================
# Configuration
# =============================================================================

PAYMENT_METHODS = ["UPI", "Card", "NetBanking"]
DEVICES = ["Android", "iOS", "Web"]
NETWORKS = ["4G", "5G", "WiFi", "3G"]
AGE_GROUPS = ["<25", "25-34", "35-44", "45+"]
CATEGORIES = ["Food", "Entertainment", "Travel", "Utilities", "Others"]

# Indian states with approximate population weights
STATES = [
    ("Maharashtra", 0.12),
    ("Uttar Pradesh", 0.16),
    ("Karnataka", 0.08),
    ("Tamil Nadu", 0.07),
    ("Gujarat", 0.06),
    ("Rajasthan", 0.06),
    ("West Bengal", 0.08),
    ("Andhra Pradesh", 0.05),
    ("Madhya Pradesh", 0.06),
    ("Kerala", 0.04),
    ("Telangana", 0.04),
    ("Bihar", 0.05),
    ("Delhi", 0.03),
    ("Punjab", 0.02),
    ("Haryana", 0.02),
    ("Odisha", 0.02),
    ("Jharkhand", 0.02),
    ("Assam", 0.01),
    ("Chhattisgarh", 0.01),
]

FAILURE_CODES = [
    "TIMEOUT",
    "INSUFFICIENT_BALANCE",
    "BANK_DECLINED",
    "INVALID_OTP",
    "NETWORK_ERROR",
    "LIMIT_EXCEEDED",
    "CARD_EXPIRED",
    "FRAUD_SUSPECTED",
    "TECHNICAL_ERROR",
    "USER_CANCELLED",
]

# Base failure rates by segment (for realistic data patterns)
BASE_FAILURE_RATE = 0.03  # 3%
DEVICE_FAILURE_MULTIPLIER = {"Android": 1.2, "iOS": 0.8, "Web": 1.0}
NETWORK_FAILURE_MULTIPLIER = {"3G": 2.0, "4G": 1.0, "5G": 0.7, "WiFi": 0.9}

# Amount distribution by category
AMOUNT_RANGES = {
    "Food": (50, 2000),
    "Entertainment": (100, 5000),
    "Travel": (500, 50000),
    "Utilities": (200, 10000),
    "Others": (100, 20000),
}


def weighted_choice(choices: List[tuple]) -> str:
    """Make a weighted random choice."""
    items, weights = zip(*choices)
    return random.choices(items, weights=weights)[0]


def generate_transaction(
    timestamp: datetime,
    day_of_week: int,
    hour: int
) -> dict:
    """Generate a single transaction record."""
    
    # Basic attributes
    device = random.choice(DEVICES)
    network = random.choice(NETWORKS)
    payment_method = random.choice(PAYMENT_METHODS)
    age_group = random.choice(AGE_GROUPS)
    category = random.choice(CATEGORIES)
    state = weighted_choice(STATES)
    
    # Generate amount based on category
    min_amt, max_amt = AMOUNT_RANGES[category]
    # Log-normal-ish distribution for more realistic amounts
    amount = round(random.uniform(min_amt, max_amt) * random.random() + min_amt, 2)
    
    # Calculate failure probability
    failure_prob = BASE_FAILURE_RATE
    failure_prob *= DEVICE_FAILURE_MULTIPLIER.get(device, 1.0)
    failure_prob *= NETWORK_FAILURE_MULTIPLIER.get(network, 1.0)
    
    # Higher failure during peak hours
    if 9 <= hour <= 12 or 18 <= hour <= 21:
        failure_prob *= 1.3
    
    # Higher failure for high-value transactions
    if amount > 10000:
        failure_prob *= 1.5
    
    # Determine status
    is_failed = random.random() < failure_prob
    status = "Failed" if is_failed else "Success"
    failure_code = random.choice(FAILURE_CODES) if is_failed else None
    
    # Fraud and review flags
    # Higher fraud probability for:
    # - High amounts, especially late at night
    # - Certain failure codes
    fraud_prob = 0.001  # 0.1% base rate
    if amount > 20000:
        fraud_prob *= 5
    if 0 <= hour <= 5:
        fraud_prob *= 3
    if failure_code == "FRAUD_SUSPECTED":
        fraud_prob = 1.0
    
    fraud_flag = 1 if random.random() < fraud_prob else 0
    
    # Review flag - slightly higher than fraud
    review_prob = 0.01  # 1% base rate
    if fraud_flag:
        review_prob = 0.8
    if amount > 15000:
        review_prob *= 2
    
    review_flag = 1 if random.random() < review_prob else 0
    
    return {
        "transaction_id": str(uuid.uuid4()),
        "timestamp": timestamp.isoformat(),
        "amount": amount,
        "payment_method": payment_method,
        "device": device,
        "state": state,
        "age_group": age_group,
        "network": network,
        "category": category,
        "status": status,
        "failure_code": failure_code or "",
        "fraud_flag": fraud_flag,
        "review_flag": review_flag,
    }


def generate_dataset(
    num_rows: int,
    output_path: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> None:
    """
    Generate a complete transaction dataset.
    
    Args:
        num_rows: Number of transactions to generate.
        output_path: Path to output CSV file.
        start_date: Start of date range (default: 90 days ago).
        end_date: End of date range (default: today).
    """
    if start_date is None:
        start_date = datetime.now() - timedelta(days=90)
    if end_date is None:
        end_date = datetime.now()
    
    # Create output directory if needed
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Calculate time range
    total_seconds = (end_date - start_date).total_seconds()
    
    print(f"Generating {num_rows:,} transactions...")
    print(f"Date range: {start_date.date()} to {end_date.date()}")
    
    fieldnames = [
        "transaction_id", "timestamp", "amount", "payment_method",
        "device", "state", "age_group", "network", "category",
        "status", "failure_code", "fraud_flag", "review_flag"
    ]
    
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for i in range(num_rows):
            # Random timestamp within range
            random_seconds = random.uniform(0, total_seconds)
            timestamp = start_date + timedelta(seconds=random_seconds)
            
            # Generate transaction
            transaction = generate_transaction(
                timestamp=timestamp,
                day_of_week=timestamp.weekday(),
                hour=timestamp.hour
            )
            writer.writerow(transaction)
            
            # Progress indicator
            if (i + 1) % 10000 == 0:
                print(f"  Generated {i + 1:,} / {num_rows:,} transactions...")
    
    print(f"\n✓ Dataset saved to: {output_path}")
    print(f"  File size: {output_path.stat().st_size / 1024 / 1024:.2f} MB")
    
    # Print summary statistics
    print("\n--- Dataset Summary ---")
    import pandas as pd
    df = pd.read_csv(output_path)
    print(f"Total transactions: {len(df):,}")
    print(f"Failed transactions: {(df['status'] == 'Failed').sum():,} ({(df['status'] == 'Failed').mean()*100:.2f}%)")
    print(f"Fraud flags: {df['fraud_flag'].sum():,} ({df['fraud_flag'].mean()*100:.3f}%)")
    print(f"Review flags: {df['review_flag'].sum():,} ({df['review_flag'].mean()*100:.2f}%)")
    print(f"Avg transaction amount: ₹{df['amount'].mean():,.2f}")
    print(f"Total volume: ₹{df['amount'].sum():,.2f}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate synthetic transaction data for InsightX AI"
    )
    parser.add_argument(
        "--rows", "-n",
        type=int,
        default=50000,
        help="Number of transactions to generate (default: 50000)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="./data/sample_transactions_50k.csv",
        help="Output file path (default: ./data/sample_transactions_50k.csv)"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=90,
        help="Number of days of data to generate (default: 90)"
    )
    
    args = parser.parse_args()
    
    # Adjust output filename if rows specified
    if args.rows != 50000 and args.output == "./data/sample_transactions_50k.csv":
        if args.rows >= 1000000:
            suffix = f"{args.rows // 1000000}m"
        elif args.rows >= 1000:
            suffix = f"{args.rows // 1000}k"
        else:
            suffix = str(args.rows)
        args.output = f"./data/sample_transactions_{suffix}.csv"
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=args.days)
    
    generate_dataset(
        num_rows=args.rows,
        output_path=args.output,
        start_date=start_date,
        end_date=end_date
    )


if __name__ == "__main__":
    main()
