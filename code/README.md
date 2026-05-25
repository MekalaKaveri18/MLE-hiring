# Support Triage Agent — Setup & Run Instructions

## Prerequisites
- Python 3.11+
- An Anthropic API key

## Setup

```bash
# From repo root
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

pip install anthropic python-dotenv
```

## Run

```bash
cd code
python main.py
```

This will:
1. Read `support_tickets/support_tickets.csv`
2. Build the BM25 retrieval index from `data/` (first run takes ~5s)
3. Process each ticket via Claude claude-sonnet-4-20250514 with temperature=0
4. Write `support_tickets/output.csv`
5. Run format validation automatically

Expected runtime: ~3-4 minutes for 90 tickets (average ~2s/ticket at claude-sonnet-4-20250514 speed).

## Validate output only

```bash
python validate_output.py
```

## Architecture

See `ARCHITECTURE.md` for full design documentation.

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | Anthropic API key |

## Determinism

- LLM temperature is fixed at 0
- Retrieval is deterministic (BM25, no randomness)
- Running twice on the same input produces identical output
