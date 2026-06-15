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

from __future__ import annotations

import os
import re
from typing import Any

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


def _chat_completion(prompt: str, temperature: float = 0.7) -> str:
    """Helper for Groq chat completions."""
    client = _get_groq_client()
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are FitFindr, a stylistic assistant for secondhand fashion. "
                    "Be specific, helpful, and concise."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
        max_tokens=350,
    )
    return response.choices[0].message.content.strip()


def _tokenize(text: str) -> set[str]:
    """Normalize text into a set of lowercase word tokens."""
    return set(re.findall(r"[a-z0-9]+", (text or "").lower()))


_STOPWORDS = {
    "looking", "for", "a", "an", "the", "i", "im", "i'm", "want", "need",
    "to", "find", "search", "under", "below", "max", "maximum", "size",
    "with", "and", "or", "out", "there", "what", "is", "are", "me", "my",
}

_SYNONYMS = {
    "tee": {"tee", "tshirt", "t-shirt", "shirt", "t shirt"},
    "tshirt": {"tee", "tshirt", "t-shirt", "shirt", "t shirt"},
    "jacket": {"jacket", "coat", "blazer", "outerwear"},
    "denim": {"denim", "jeans", "jacket"},
    "jeans": {"jeans", "denim", "pants"},
    "skirt": {"skirt", "mini", "midi"},
    "dress": {"dress", "gown", "maxi", "mini", "midi"},
    "sneakers": {"sneakers", "shoes", "trainers"},
    "boots": {"boots", "shoes", "combat"},
}


def _normalize_query_terms(description: str) -> set[str]:
    tokens = _tokenize(description)
    cleaned = {t for t in tokens if t not in _STOPWORDS}

    expanded = set(cleaned)
    for token in cleaned:
        if token in _SYNONYMS:
            expanded.update(_SYNONYMS[token])

    return expanded


def _normalize_size(value: Any) -> str:
    return str(value).strip().lower() if value is not None else ""


def _size_matches(listing_size: Any, requested_size: str | None) -> bool:
    """
    Case-insensitive size matching with support for composite sizes like S/M.
    If requested_size is empty/None, always match.
    """
    req = _normalize_size(requested_size)
    if not req:
        return True

    ls = _normalize_size(listing_size)
    if not ls:
        return False

    if ls == req:
        return True

    # Support sizes like "S/M", "m-l", "28 30", etc.
    listing_parts = set(re.split(r"[\s,/|\-]+", ls))
    requested_parts = set(re.split(r"[\s,/|\-]+", req))
    return bool(listing_parts & requested_parts)


def _item_text_fields(item: dict) -> str:
    """Combine the searchable fields of a listing into one text blob."""
    parts: list[str] = []
    for key in [
        "title",
        "description",
        "category",
        "brand",
        "platform",
        "condition",
    ]:
        value = item.get(key)
        if value:
            parts.append(str(value))

    style_tags = item.get("style_tags", [])
    colors = item.get("colors", [])
    if isinstance(style_tags, list):
        parts.extend(str(x) for x in style_tags if x)
    if isinstance(colors, list):
        parts.extend(str(x) for x in colors if x)

    return " ".join(parts).lower()


def _term_matches_text(term: str, text: str, text_tokens: set[str]) -> bool:
    term = term.strip().lower()
    if not term:
        return False

    term_tokens = _tokenize(term)
    if len(term_tokens) == 1:
        return next(iter(term_tokens)) in text_tokens

    return term in text


def _score_listing(item: dict, description: str) -> int:
    """
    Score a listing based on keyword overlap, with title/description boosting.
    Returns 0 when there is no meaningful overlap.
    """
    query = (description or "").strip().lower()
    if not query:
        return 0

    haystack = _item_text_fields(item)
    haystack_tokens = _tokenize(haystack)
    query_terms = _normalize_query_terms(query)
    if not query_terms:
        return 0

    score = 0

    # Strong signal for exact phrase match.
    if query in haystack:
        score += 12

    # Token/synonym overlap across searchable fields.
    for token in query_terms:
        if _term_matches_text(token, haystack, haystack_tokens):
            score += 2

    # Extra boost for title overlap.
    title = str(item.get("title", "")).lower()
    title_tokens = _tokenize(title)
    for token in query_terms:
        if _term_matches_text(token, title, title_tokens):
            score += 1

    return score


def _format_wardrobe_items(wardrobe: dict) -> str:
    """Create a compact human-readable wardrobe summary for prompting."""
    items = wardrobe.get("items", []) if isinstance(wardrobe, dict) else []
    if not items:
        return "No wardrobe items provided."

    lines = []
    for idx, item in enumerate(items, start=1):
        if isinstance(item, dict):
            name = item.get("name") or item.get("title") or item.get("item") or "Unnamed item"
            category = item.get("category", "unknown category")
            colors = item.get("colors", [])
            style_tags = item.get("style_tags", [])
            notes = []
            if colors:
                notes.append(f"colors={colors}")
            if style_tags:
                notes.append(f"style_tags={style_tags}")
            note_text = f" ({', '.join(notes)})" if notes else ""
            lines.append(f"{idx}. {name} — {category}{note_text}")
        else:
            lines.append(f"{idx}. {item}")
    return "\n".join(lines)


def _format_item(item: dict) -> str:
    """Render a listing dict for prompts."""
    title = item.get("title", "Unknown item")
    price = item.get("price", "unknown price")
    platform = item.get("platform", "unknown platform")
    size = item.get("size", "unknown size")
    condition = item.get("condition", "unknown condition")
    category = item.get("category", "unknown category")
    brand = item.get("brand", "unknown brand")
    colors = item.get("colors", [])
    style_tags = item.get("style_tags", [])
    desc = item.get("description", "")

    return (
        f"Title: {title}\n"
        f"Price: ${price}\n"
        f"Platform: {platform}\n"
        f"Size: {size}\n"
        f"Condition: {condition}\n"
        f"Category: {category}\n"
        f"Brand: {brand}\n"
        f"Colors: {colors}\n"
        f"Style tags: {style_tags}\n"
        f"Description: {desc}"
    )


# ── Tool 1: search_listings ───────────────────────────────────────────────────


def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """
    try:
        listings = load_listings()
    except Exception:
        return []

    if not description or not str(description).strip():
        return []

    filtered: list[tuple[int, dict]] = []
    for item in listings:
        try:
            price = item.get("price")
            if max_price is not None:
                if price is None or float(price) > float(max_price):
                    continue

            if not _size_matches(item.get("size"), size):
                continue

            score = _score_listing(item, description)
            if score <= 0:
                continue

            filtered.append((score, item))
        except Exception:
            # Skip malformed items rather than crashing the search.
            continue

    # Sort by score descending, then by lower price as a tie-breaker.
    filtered.sort(
        key=lambda pair: (
            -pair[0],
            float(pair[1].get("price", 10**9)) if pair[1].get("price") is not None else 10**9,
        )
    )

    return [item for _, item in filtered]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────


def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """
    items = []
    if isinstance(wardrobe, dict):
        items = wardrobe.get("items", []) or []

    item_text = _format_item(new_item or {})

    if not items:
        prompt = f"""
You are styling a thrifted item with no known wardrobe.

Thrifted item:
{item_text}

Write 2 short outfit ideas or styling directions that do NOT depend on specific wardrobe pieces.
Requirements:
- Be practical and specific.
- Mention what kinds of bottoms, shoes, or layers would pair well.
- Keep the tone friendly and useful.
- Return plain text only.
"""
    else:
        wardrobe_text = _format_wardrobe_items(wardrobe)
        prompt = f"""
You are a fashion stylist helping a user build outfits around a secondhand item.

Thrifted item:
{item_text}

User wardrobe:
{wardrobe_text}

Write 1–2 complete outfit ideas that specifically use the user's wardrobe items when possible.
Requirements:
- Name the wardrobe pieces you would combine.
- Explain why each outfit works.
- Keep it concise but concrete.
- If the wardrobe lacks a perfect match, give the closest alternative and explain it.
- Return plain text only.
"""

    try:
        return _chat_completion(prompt, temperature=0.8)
    except Exception as exc:
        if not items:
            return (
                "I found the item, but I can only give general styling guidance right now. "
                "Try pairing it with a simple base layer, a matching bottom, and clean shoes. "
                f"(Styling tool error: {exc})"
            )
        return (
            "I found the item, but I couldn't generate a specific outfit from the wardrobe "
            f"provided. Please add a few more wardrobe items and try again. (Styling tool error: {exc})"
        )


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────


def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """
    if not outfit or not str(outfit).strip():
        title = (new_item or {}).get("title", "the item")
        return (
            f"Cannot create a fit card yet because the outfit is missing or incomplete for {title}. "
            "Please provide a full outfit suggestion first."
        )

    item_text = _format_item(new_item or {})
    prompt = f"""
Write a short thrift-fit caption for social media.

Thrifted item:
{item_text}

Outfit:
{outfit}

Caption requirements:
- 2 to 4 sentences.
- Casual, authentic, and post-ready.
- Mention the item name, price, and platform naturally exactly once each.
- Make the vibe specific to the outfit.
- Do not sound like a product listing.
- Return plain text only.
"""

    try:
        # Slightly higher temperature to encourage variation across runs.
        return _chat_completion(prompt, temperature=1.0)
    except Exception as exc:
        title = (new_item or {}).get("title", "the item")
        return (
            f"Could not generate a fit card for {title} because the caption tool failed. "
            f"Error: {exc}"
        )
