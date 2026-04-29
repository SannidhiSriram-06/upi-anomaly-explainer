import pandas as pd
from datetime import datetime

# --- Thresholds (tune these without touching agent logic) ---
VELOCITY_WINDOW_SECONDS = 300   # 5-minute window
VELOCITY_MAX_TXN = 3            # max transactions allowed per window
LARGE_AMOUNT_THRESHOLD = 10000  # anything above this is "large"
ODD_HOUR_START = 1              # 1am
ODD_HOUR_END = 5                # 5am


def load_transactions(csv_path: str) -> pd.DataFrame:
    """Load CSV and parse timestamps."""
    df = pd.read_csv(csv_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp').reset_index(drop=True)
    return df


def check_velocity(df: pd.DataFrame) -> list[dict]:
    """
    Flag senders who make more than VELOCITY_MAX_TXN transactions
    within any VELOCITY_WINDOW_SECONDS rolling window.
    """
    flagged = []
    for sender, group in df.groupby('sender_upi'):
        group = group.sort_values('timestamp')
        times = group['timestamp'].tolist()
        for i in range(len(times)):
            window = [t for t in times if 0 <= (t - times[i]).total_seconds() <= VELOCITY_WINDOW_SECONDS]
            if len(window) > VELOCITY_MAX_TXN:
                txn_ids = group[group['timestamp'].isin(window)]['txn_id'].tolist()
                flagged.append({
                    "rule": "velocity_abuse",
                    "sender": sender,
                    "txn_ids": txn_ids,
                    "detail": f"{len(window)} transactions in {VELOCITY_WINDOW_SECONDS}s window"
                })
                break  # one flag per sender is enough
    return flagged


def check_large_amount(df: pd.DataFrame) -> list[dict]:
    """Flag any single transaction above LARGE_AMOUNT_THRESHOLD."""
    flagged = []
    large = df[df['amount'] > LARGE_AMOUNT_THRESHOLD]
    for _, row in large.iterrows():
        flagged.append({
            "rule": "large_amount",
            "sender": row['sender_upi'],
            "txn_ids": [row['txn_id']],
            "detail": f"Amount ₹{row['amount']:,.2f} exceeds threshold ₹{LARGE_AMOUNT_THRESHOLD:,}"
        })
    return flagged


def check_odd_hours(df: pd.DataFrame) -> list[dict]:
    """Flag transactions made between ODD_HOUR_START and ODD_HOUR_END."""
    flagged = []
    odd = df[df['timestamp'].dt.hour.between(ODD_HOUR_START, ODD_HOUR_END)]
    for _, row in odd.iterrows():
        flagged.append({
            "rule": "odd_hour_transaction",
            "sender": row['sender_upi'],
            "txn_ids": [row['txn_id']],
            "detail": f"Transaction at {row['timestamp'].strftime('%H:%M:%S')} (between {ODD_HOUR_START}am–{ODD_HOUR_END}am)"
        })
    return flagged


def run_all_heuristics(csv_path: str) -> dict:
    """
    Master function — runs all rules, deduplicates by txn_id,
    returns a clean summary dict that agents will consume.
    """
    df = load_transactions(csv_path)
    
    all_flags = (
        check_velocity(df) +
        check_large_amount(df) +
        check_odd_hours(df)
    )
    
    # Deduplicate: if same txn_id appears in multiple rules, keep all rules for it
    txn_map = {}
    for flag in all_flags:
        for txn_id in flag['txn_ids']:
            if txn_id not in txn_map:
                txn_map[txn_id] = []
            txn_map[txn_id].append({
                "rule": flag['rule'],
                "sender": flag['sender'],
                "detail": flag['detail']
            })
    
    return {
        "total_transactions": len(df),
        "flagged_count": len(txn_map),
        "flags": txn_map  # { "TXN001": [{"rule":..., "detail":...}], ... }
    }
