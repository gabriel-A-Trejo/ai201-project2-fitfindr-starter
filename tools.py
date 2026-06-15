"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.
    """

    # 1. Load all listings
    listings = load_listings()

    # Convert search query into lowercase keywords
    keywords = description.lower().split()

    scored_results = []

    for listing in listings:

        # 2. Filter by max_price
        if max_price is not None and listing["price"] > max_price:
            continue

        # 2. Filter by size (case-insensitive)
        if size is not None:
            if size.lower() not in listing["size"].lower():
                continue

        # 3. Score keyword overlap
        score = 0

        title = listing["title"].lower()
        desc = listing["description"].lower()
        style_tags = [tag.lower() for tag in listing["style_tags"]]

        for keyword in keywords:

            # Strong match in title
            if keyword in title:
                score += 3

            # Medium match in style tags
            if any(keyword in tag for tag in style_tags):
                score += 2

            # Weak match in description
            if keyword in desc:
                score += 1

        # 4. Keep only relevant listings
        if score > 0:
            scored_results.append((score, listing))

    # 5. Sort highest score first
    scored_results.sort(key=lambda x: x[0], reverse=True)

    return [listing for score, listing in scored_results]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.
    """

    client = _get_groq_client()

    wardrobe_items = wardrobe.get("items", [])

    # Case 1: Empty wardrobe
    if len(wardrobe_items) == 0:

        prompt = f"""
        A user is considering buying this thrifted item:

        Title: {new_item.get("title")}
        Category: {new_item.get("category")}
        Style Tags: {", ".join(new_item.get("style_tags", []))}
        Colors: {", ".join(new_item.get("colors", []))}

        The user has not added any wardrobe items yet.

        Suggest 1-2 general outfit ideas for this item.
        Explain:
        - what pieces pair well with it
        - what shoes work best
        - what overall aesthetic or vibe it fits

        Keep the response practical and conversational.
        """

    # Case 2: Wardrobe contains items
    else:

        wardrobe_text = "\n".join(
            [
                f"- {item['name']} "
                f"(category: {item['category']}, "
                f"colors: {', '.join(item['colors'])})"
                for item in wardrobe_items
            ]
        )

        prompt = f"""
        A user is considering buying this thrifted item:

        Title: {new_item.get("title")}
        Category: {new_item.get("category")}
        Style Tags: {", ".join(new_item.get("style_tags", []))}
        Colors: {", ".join(new_item.get("colors", []))}

        The user's wardrobe contains:

        {wardrobe_text}

        Create 1-2 complete outfits using the thrifted item
        and specific pieces from the wardrobe.

        Mention the wardrobe items by name and explain why
        the combination works stylistically.
        """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are an expert personal stylist."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.7,
    )

    return response.choices[0].message.content.strip()


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.
    """

    # Guard against missing outfit input
    if not outfit or not outfit.strip():
        return (
            "Unable to create fit card because outfit information is missing."
        )

    client = _get_groq_client()

    prompt = f"""
    Create a short Instagram/TikTok outfit caption.

    Thrifted Item:
    - Title: {new_item.get("title")}
    - Price: ${new_item.get("price")}
    - Platform: {new_item.get("platform")}

    Outfit Idea:
    {outfit}

    Requirements:
    - 2 to 4 sentences
    - Casual and authentic
    - Sound like a real outfit post
    - Mention the item title once
    - Mention the price once
    - Mention the platform once
    - Capture the outfit vibe
    - Do not sound like an advertisement
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": (
                    "You write engaging social-media captions for thrifted fashion finds."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=1.0,  # higher for variation
    )

    return response.choices[0].message.content.strip()