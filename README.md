# Steward x402 Recipe for CrewAI

A CrewAI agent that **buys from an x402 pay-per-call rail** — real micropayments, real receipts.

The agent connects to [`@brianbooms/steward-mcp`](https://github.com/brianbooms/steward-mcp) (v0.2.1, 19 tools) over MCP stdio, browses the paid catalog for free, then purchases one weather API call for Austin, TX — **$0.01 USDC on Base**, signed by your own wallet, verified before signing.

Built by Synthetic Universe LLC. Brian Booms is an AI-assisted artist and content creator.

## How payment works

1. Agent calls `steward_purchase_instructions` → gets the live 402 quote (price, USDC contract, payee wallet)
2. Steward MCP verifies scheme, network, payee, and price against your spend caps
3. Your key signs an EIP-3009 authorization — **only** for the quoted amount
4. Rail settles via x402 facilitator; the paid tool returns with a proof-of-payment receipt bound to the on-chain tx

Wrong payee, wrong price, over cap? Refused. No silent spending, ever.

**Spend guardrails** (enforced server-side, before any signature):
- `STEWARD_MAX_SPEND_USDC=0.05` — hard ceiling per single call
- `STEWARD_MAX_SPEND_DAY_USDC=5.00` — hard ceiling per rolling 24h

## Setup

```bash
pip install -r requirements.txt
```

You need **two** keys:

| Key | For | Required |
|---|---|---|
| `OPENAI_API_KEY` (or `ANTHROPIC_API_KEY`, etc.) | CrewAI's LLM | Yes — CrewAI needs a model |
| `STEWARD_PAYER_KEY` | Your Base wallet private key (`0x...`), funded with a few USDC | Yes — the MCP server will not start without it (v0.2.1) |

**Your key never leaves your machine.** It is passed as an environment variable to the local MCP subprocess only — never logged, stored, or transmitted.

## Run

```bash
STEWARD_PAYER_KEY=0x... OPENAI_API_KEY=sk-... python steward_crewai_recipe.py
```

The crew runs the free discovery first (catalog browse), then the $0.01 paid
weather purchase. Spend ceilings (`STEWARD_MAX_SPEND_USDC=0.05`,
`STEWARD_MAX_SPEND_DAY_USDC=5.00`) are enforced server-side before any signature.

## What the crew does

1. **Scout agent** (free): calls `steward_catalog`, then `steward_product` for the weather SKU — reports names, SKUs, prices
2. **Buyer agent** (paid, $0.01): confirms the price via `steward_purchase_instructions`, checks it against the $0.05 ceiling, then calls `steward_weather` for Austin, TX (30.2672, -97.7431) and reports the result + amount paid

## Files

- `steward_crewai_recipe.py` — the runnable recipe
- `requirements.txt` — Python dependencies
- `STATUS.md` — build/test status

## Links

- MCP server: https://github.com/brianbooms/steward-mcp
- npm: `@brianbooms/steward-mcp` v0.2.1
- Rail: https://pay.brianbooms.com
- Catalog: https://pay.brianbooms.com/api/v1/catalog/query
- Terms: https://brianbooms.com/fair-dealing/

## License

MIT — Synthetic Universe LLC.
