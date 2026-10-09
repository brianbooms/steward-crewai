"""
Steward x402 Recipe for CrewAI
==============================
A CrewAI agent that buys from Brian Booms' x402 pay-per-call rail
via the Steward MCP server.

What this does:
  1. Connects to @brianbooms/steward-mcp over stdio via MCPServerAdapter
  2. A "scout" agent discovers the paid catalog (FREE — no wallet needed)
  3. A "buyer" agent purchases a data API call — steward_weather for Austin, TX
     ($0.01 USDC on Base, signed by your own wallet, verified before signing)

Prerequisites:
  pip install crewai crewai-tools mcp

  For the paid purchase step you also need:
  - A Base wallet private key with a few USDC  ->  STEWARD_PAYER_KEY
  - An LLM API key (CrewAI uses litellm under the hood):
    OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.

  STEWARD_PAYER_KEY is required — the MCP server will not start without it
  (v0.2.1 hard-requires the key at startup, even for free discovery tools).
  The spend ceilings below keep every call inside your budget.

Run:
  STEWARD_PAYER_KEY=0x... OPENAI_API_KEY=sk-... python steward_crewai_recipe.py

Brian Booms is an AI-assisted artist and content creator.
Rail: https://pay.brianbooms.com  |  Terms: https://brianbooms.com/fair-dealing/
"""

import os
import sys

# ---------------------------------------------------------------------------
# 1. Connect to Steward over MCP
# ---------------------------------------------------------------------------
from mcp import StdioServerParameters
from crewai_tools import MCPServerAdapter

PAYER_KEY = os.environ.get("STEWARD_PAYER_KEY", "")
if not PAYER_KEY:
    sys.exit(
        "STEWARD_PAYER_KEY is required — the MCP server will not start without it.\n"
        "Set it to your Base wallet private key (0x...), funded with a few USDC."
    )

server_params = StdioServerParameters(
    command="npx",
    args=["-y", "@brianbooms/steward-mcp"],
    env={
        "STEWARD_PAYER_KEY": PAYER_KEY,
        # Hard spend ceilings (server-side, enforced before any signature):
        "STEWARD_MAX_SPEND_USDC": "0.05",      # max per single call
        "STEWARD_MAX_SPEND_DAY_USDC": "5.00",  # max per rolling 24h
        "PATH": os.environ.get("PATH", ""),
    },
)

adapter = MCPServerAdapter(server_params)
tools = adapter.tools  # list of CrewAI BaseTool, 1:1 with the MCP server's tools

print(f"[steward] Connected — {len(tools)} tools available:")
for t in tools:
    print(f"  - {t.name}")

# ---------------------------------------------------------------------------
# 2. Free discovery: browse the catalog (no wallet, no payment)
# ---------------------------------------------------------------------------
from crewai import Agent, Task, Crew, Process

scout = Agent(
    role="Catalog Scout",
    goal="Discover what paid APIs are available on the Steward x402 rail and report their prices.",
    backstory=(
        "You are a careful researcher. You browse the Steward product catalog "
        "(a free, read-only tool) and report exactly what each product costs. "
        "You never spend money — discovery only."
    ),
    tools=tools,
    verbose=True,
)

scout_task = Task(
    description=(
        "Use steward_catalog to list the available paid products. "
        "Then use steward_product to get full details (price, delivery, buy URL) "
        "for the weather product. Report: product names, SKU, and USDC price each."
    ),
    expected_output=(
        "A short list of products with SKU and price, plus full details for the weather product."
    ),
    agent=scout,
)

# ---------------------------------------------------------------------------
# 3. Paid purchase: buy one weather API call (needs STEWARD_PAYER_KEY)
# ---------------------------------------------------------------------------
buyer = Agent(
    role="API Buyer",
    goal="Purchase exactly one weather API call for Austin, TX and report the result.",
    backstory=(
        "You are a frugal buyer. Before every purchase you check the price with "
        "steward_purchase_instructions, confirm it is within the $0.05/call ceiling, "
        "and only then call the paid tool. You buy exactly what the task asks for — "
        "never more, never a different product."
    ),
    tools=tools,
    verbose=True,
)

buyer_task = Task(
    description=(
        "1. Use steward_purchase_instructions for the weather product to confirm the price. "
        "2. If the price is $0.05 USDC or less, call steward_weather with "
        "latitude=30.2672 and longitude=-97.7431 (Austin, TX). "
        "3. Report the weather result and the amount paid."
    ),
    expected_output=(
        "The current weather for Austin, TX plus the USDC amount paid for the call."
    ),
    agent=buyer,
)

# ---------------------------------------------------------------------------
# 4. Run
# ---------------------------------------------------------------------------
def main() -> int:
    print("[steward] STEWARD_PAYER_KEY set — running full demo (free discovery + $0.01 paid purchase).")
    crew = Crew(
        agents=[scout, buyer],
        tasks=[scout_task, buyer_task],
        process=Process.sequential,
        verbose=True,
    )
    try:
        result = crew.kickoff()
    finally:
        # Always close the MCP connection (stops the npx subprocess).
        adapter.stop()

    print("\n" + "=" * 60)
    print("RESULT")
    print("=" * 60)
    print(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
