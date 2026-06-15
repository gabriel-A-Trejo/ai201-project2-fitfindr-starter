from tools import search_listings, suggest_outfit, create_fit_card
from utils.data_loader import get_empty_wardrobe, get_example_wardrobe


# ─────────────────────────────────────────────
# TOOL 1: search_listings (your original tests)
# ─────────────────────────────────────────────

def test_search_returns_results():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert isinstance(results, list)
    assert len(results) > 0


def test_search_empty_results():
    results = search_listings("designer ballgown", size="XXS", max_price=5)
    assert results == []


def test_search_price_filter():
    results = search_listings("jacket", size=None, max_price=10)
    assert all(item["price"] <= 10 for item in results)


# ─────────────────────────────────────────────
# TOOL 1 ADDITIONAL FAILURE CASES
# ─────────────────────────────────────────────

def test_search_size_filter_no_match():
    """Failure mode: size filter eliminates all results"""
    results = search_listings("tee", size="ZZZ_INVALID_SIZE", max_price=100)
    assert results == []


def test_search_zero_score_filtered_out():
    """Failure mode: unrelated keyword should return empty list"""
    results = search_listings("completelyunrelatedwordxyz", size=None, max_price=100)
    assert results == []


def test_search_max_price_excludes_all():
    """Failure mode: max_price too low removes everything"""
    results = search_listings("vintage", size=None, max_price=0.01)
    assert results == []


# ─────────────────────────────────────────────
# TOOL 2: suggest_outfit failure modes
# ─────────────────────────────────────────────

def test_suggest_outfit_empty_wardrobe():
    result = suggest_outfit(
        {
            "title": "Graphic Tee",
            "category": "tops",
            "style_tags": ["streetwear"],
            "colors": ["black"]
        },
        get_empty_wardrobe()
    )

    assert isinstance(result, str)
    assert len(result) > 0


def test_suggest_outfit_missing_fields():
    """Failure mode: incomplete new_item input"""
    result = suggest_outfit(
        {"title": "Broken Item"},  # missing category/tags/colors
        get_empty_wardrobe()
    )

    assert isinstance(result, str)
    assert len(result) > 0


# ─────────────────────────────────────────────
# TOOL 3: create_fit_card failure modes
# ─────────────────────────────────────────────

def test_create_fit_card_missing_outfit():
    result = create_fit_card(
        "",
        {
            "title": "Graphic Tee",
            "price": 24,
            "platform": "depop"
        }
    )

    assert isinstance(result, str)
    assert "missing" in result.lower()


def test_create_fit_card_whitespace_outfit():
    """Failure mode: whitespace-only outfit should fail safely"""
    result = create_fit_card("   ", {
        "title": "Graphic Tee",
        "price": 24,
        "platform": "depop"
    })

    assert "missing" in result.lower()