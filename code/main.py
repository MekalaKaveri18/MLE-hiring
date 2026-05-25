#!/usr/bin/env python3
"""
MLE Hiring Challenge — Main Entry Point

Modes:
  python code/main.py              → process all 89 tickets fresh
  python code/main.py --resume     → skip already-done rows, fill missing ones
  python code/main.py --merge OLD  → keep good rows from OLD csv, reprocess fallback rows

Example to combine two runs:
  python code/main.py --merge support_tickets/output_run1.csv
"""

import csv
import json
import os
import sys
import time
from pathlib import Path

# Load .env
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

if not os.environ.get("GROQ_API_KEY"):
    print("ERROR: GROQ_API_KEY not set. Add it to .env or export it.", file=sys.stderr)
    sys.exit(1)

sys.path.insert(0, str(Path(__file__).parent))
from agent import process_ticket

REPO_ROOT   = Path(__file__).parent.parent
INPUT_PATH  = REPO_ROOT / "support_tickets" / "support_tickets.csv"
OUTPUT_PATH = REPO_ROOT / "support_tickets" / "output.csv"

OUTPUT_HEADERS = [
    "issue", "subject", "company",
    "response", "product_area", "status", "request_type", "justification",
    "confidence_score", "source_documents", "risk_level", "pii_detected",
    "language", "actions_taken",
]


def is_fallback_row(row: dict) -> bool:
    """Detect rows that used the rule-based fallback (low quality)."""
    justification = row.get("justification", "")
    response = row.get("response", "")
    fallback_signals = [
        "rule-based response",
        "api rate limit reached",
        "deterministic fallback",
        "agent error",
        # Generic fallback responses
        "we encountered an issue",
        "based on the information provided, a member of our support team",
        "thank you for reaching out. your case has been flagged",
    ]
    text = (justification + " " + response).lower()
    return any(s in text for s in fallback_signals)


def load_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_csv(rows: list[dict], path: Path):
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_HEADERS)
        writer.writeheader()
        writer.writerows(rows)


def build_row(ticket: dict, result: dict) -> dict:
    return {
        "issue":            ticket.get("Issue", ticket.get("issue", "")),
        "subject":          ticket.get("Subject", ticket.get("subject", "")),
        "company":          ticket.get("Company", ticket.get("company", "")),
        "response":         result["response"],
        "product_area":     result["product_area"],
        "status":           result["status"],
        "request_type":     result["request_type"],
        "justification":    result["justification"],
        "confidence_score": result["confidence_score"],
        "source_documents": result.get("source_documents", ""),
        "risk_level":       result["risk_level"],
        "pii_detected":     str(result["pii_detected"]).lower(),
        "language":         result.get("language", "en"),
        "actions_taken":    json.dumps(result.get("actions_taken", []), ensure_ascii=False),
    }


def process_one(ticket: dict, index: int, total: int) -> dict:
    issue_raw = ticket.get("Issue", ticket.get("issue", ""))
    subject   = ticket.get("Subject", ticket.get("subject", ""))
    company   = ticket.get("Company", ticket.get("company", ""))

    print(f"[{index:02d}/{total}] {(subject or '(no subject)')[:55]:<55}", end=" ", flush=True)
    t0 = time.time()

    try:
        result = process_ticket(issue_raw, subject, company)
    except Exception as e:
        print(f"ERROR: {e}")
        result = {
            "status": "escalated",
            "product_area": "General",
            "response": "We encountered an issue processing your request. A human agent will follow up shortly.",
            "justification": f"Agent error: {str(e)[:200]}",
            "request_type": "product_issue",
            "confidence_score": 0.3,
            "source_documents": "",
            "risk_level": "medium",
            "pii_detected": False,
            "language": "en",
            "actions_taken": [],
        }

    elapsed = time.time() - t0
    quality = "fallback" if is_fallback_row({"justification": result["justification"], "response": result["response"]}) else "llm"
    print(f"→ {result['status']:<9} | {result['risk_level']:<8} | {quality:<8} | {elapsed:.1f}s")
    return result


def main():
    args = sys.argv[1:]

    with open(INPUT_PATH, encoding="utf-8") as f:
        tickets = list(csv.DictReader(f))
    total = len(tickets)

    # --- MODE: --merge OLD_CSV ---
    if "--merge" in args:
        merge_idx = args.index("--merge")
        old_path = Path(args[merge_idx + 1]) if merge_idx + 1 < len(args) else None
        if not old_path or not old_path.exists():
            print(f"ERROR: --merge requires a valid path to an existing CSV.", file=sys.stderr)
            sys.exit(1)

        old_rows = load_csv(old_path)
        if len(old_rows) != total:
            print(f"WARNING: old CSV has {len(old_rows)} rows, input has {total}. Will reprocess mismatched rows.")

        print(f"Merging from {old_path} — reprocessing fallback rows...\n")
        rows = []
        reprocess_count = sum(1 for r in old_rows if is_fallback_row(r))
        print(f"Found {reprocess_count} fallback rows to reprocess, {total - reprocess_count} good rows to keep.\n")

        start = time.time()
        reprocessed = 0
        kept = 0

        for i, ticket in enumerate(tickets, 1):
            old_row = old_rows[i - 1] if i - 1 < len(old_rows) else None

            if old_row and not is_fallback_row(old_row):
                # Keep the good LLM response
                rows.append(old_row)
                kept += 1
                subject = ticket.get("Subject", ticket.get("subject", "(no subject)")) or "(no subject)"
                print(f"[{i:02d}/{total}] {subject[:55]:<55} → KEPT      | {old_row.get('risk_level','?'):<8} | llm")
            else:
                # Reprocess this ticket
                result = process_one(ticket, i, total)
                rows.append(build_row(ticket, result))
                reprocessed += 1

            # Save after every ticket
            save_csv(rows, OUTPUT_PATH)

        total_time = time.time() - start
        print(f"\nDone. Kept {kept} rows, reprocessed {reprocessed} rows in {total_time:.1f}s")

    # --- MODE: --resume (skip already-done rows) ---
    elif "--resume" in args:
        existing = load_csv(OUTPUT_PATH)
        start_from = len(existing)

        if start_from == 0:
            print("No existing output found, starting fresh.")
        else:
            print(f"Resuming from ticket {start_from + 1} ({start_from} already done)\n")

        rows = existing
        start = time.time()

        for i, ticket in enumerate(tickets[start_from:], start_from + 1):
            result = process_one(ticket, i, total)
            rows.append(build_row(ticket, result))
            save_csv(rows, OUTPUT_PATH)

        total_time = time.time() - start
        print(f"\nDone. {len(rows)} tickets in {total_time:.1f}s")

    # --- MODE: fresh run ---
    else:
        print(f"Processing all {total} tickets...\n")
        rows = []
        start = time.time()

        for i, ticket in enumerate(tickets, 1):
            result = process_one(ticket, i, total)
            rows.append(build_row(ticket, result))
            save_csv(rows, OUTPUT_PATH)

        total_time = time.time() - start
        print(f"\nDone. {len(rows)} tickets in {total_time:.1f}s")

    print(f"\nOutput → {OUTPUT_PATH}")
    print("\nValidating format...")
    os.system(f"{sys.executable} {REPO_ROOT / 'code' / 'validate_output.py'}")


if __name__ == "__main__":
    main()