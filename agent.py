"""
agent.py

The FitFindr planning loop. Orchestrates the three tools in response to a
natural language user query, passing state between them via a session dict.

Complete tools.py and test each tool in isolation before implementing this file.

Usage (once implemented):
    from agent import run_agent
    from utils.data_loader import get_example_wardrobe

    result = run_agent(
        query="vintage graphic tee under $30, size M",
        wardrobe=get_example_wardrobe(),
    )
    print(result["fit_card"])
    print(result["error"])   # None on success
"""

from tools import search_listings, suggest_outfit, create_fit_card


# ── session state ─────────────────────────────────────────────────────────────

def _new_session(query: str, wardrobe: dict) -> dict:
    """
    Initialize and return a fresh session dict for one user interaction.

    The session dict is the single source of truth for everything that happens
    during a run — it stores the original query, parsed parameters, tool results,
    and any error that caused early termination.

    You may add fields to this dict as needed for your implementation.
    """
    return {
        "query": query,              # original user query
        "parsed": {},                # extracted description / size / max_price
        "search_results": [],        # list of matching listing dicts
        "selected_item": None,       # top result, passed into suggest_outfit
        "wardrobe": wardrobe,        # user's wardrobe dict
        "outfit_suggestion": None,   # string returned by suggest_outfit
        "fit_card": None,            # string returned by create_fit_card
        "error": None,               # set if the interaction ended early
    }


# ── planning loop ─────────────────────────────────────────────────────────────

import re

from tools import search_listings, suggest_outfit, create_fit_card


import re
from utils.data_loader import get_empty_wardrobe


def _parse_query(query: str) -> dict:
    """
    Simple deterministic parser (NO LLM to keep tests stable)
    """
    q = query.lower()

    size_match = re.search(r"\b(xs|s|m|l|xl|xxl)\b", q)
    price_match = re.search(r"\$(\d+)", q)

    size = size_match.group(1).upper() if size_match else None
    max_price = float(price_match.group(1)) if price_match else None

    # remove size/price words for description
    cleaned = re.sub(r"\$\d+", "", q)
    cleaned = re.sub(r"\b(xs|s|m|l|xl|xxl)\b", "", cleaned)

    description = cleaned.strip()

    return {
        "description": description,
        "size": size,
        "max_price": max_price,
    }


def run_agent(query: str, wardrobe: dict) -> dict:

    # STEP 1: init session
    session = _new_session(query, wardrobe)

    # STEP 2: parse query
    parsed = _parse_query(query)
    session["parsed"] = parsed

    # STEP 3: search listings
    results = search_listings(
        description=parsed["description"],
        size=parsed["size"],
        max_price=parsed["max_price"],
    )

    session["search_results"] = results

    # FAILURE: stop immediately
    if not results:
        session["error"] = (
            "No matching listings found. Try adjusting keywords, size, or price."
        )
        session["selected_item"] = None
        session["outfit_suggestion"] = None
        session["fit_card"] = None
        return session

    # STEP 4: select top item
    selected = results[0]
    session["selected_item"] = selected

    # STEP 5: outfit suggestion
    outfit = suggest_outfit(selected, wardrobe)
    session["outfit_suggestion"] = outfit

    # STEP 6: fit card
    fit_card = create_fit_card(outfit, selected)
    session["fit_card"] = fit_card

    # STEP 7: return
    return session

# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Found: {session['selected_item']['title']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session2['error']}")
