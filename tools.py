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
    # 1. Load all listings with load_listings().
    # 加载所有二手商品数据 (Load all secondhand clothing data)
    listings = load_listings()

    # 提取搜索关键词并转为小写 (Extract keywords and convert to lowercase)
    # 将用户的输入切分成单词集合，方便后续进行比对 (Split user input into a set of words for matching)
    keywords = set(description.lower().split())

    matched_listings = []

    for item in listings:
        # 2. Filter by max_price and size (if provided).
        # 如果提供了 max_price，且商品价格高于该值，则跳过 (Skip if price exceeds max_price)
        if max_price is not None and item.get("price", float('inf')) > max_price:
            continue

        # 如果提供了 size，且商品尺寸不匹配（忽略大小写），则跳过 (Skip if size doesn't match, case-insensitive)
        if size is not None:
            item_size = item.get("size")
            if not item_size or item_size.lower() != size.lower():
                continue

        # 3. Score each remaining listing by keyword overlap with `description`.
        # 根据关键词重合度给剩下的商品打分 (Score by keyword overlap)
        # 将标题、描述和标签拼接在一起进行匹配 (Combine title, description, and style_tags to match)
        tags_str = " ".join(item.get("style_tags", []))
        item_text = f"{item.get('title', '')} {item.get('description', '')} {tags_str}".lower()
        item_words = set(item_text.split())

        # 计算匹配到的关键词数量 (Calculate the number of matched keywords)
        score = len(keywords.intersection(item_words))

        # 4. Drop any listings with a score of 0 (no relevant matches).
        # 剔除得分为 0 的商品 (Drop items with score 0)
        if score > 0:
            item_with_score = item.copy()
            item_with_score["_score"] = score
            matched_listings.append(item_with_score)

    # 5. Sort by score, highest first, and return the listing dicts.
    # 按得分从高到低排序 (Sort by score descending)
    matched_listings.sort(key=lambda x: x["_score"], reverse=True)

    # 返回前清理掉用于排序的临时 "_score" 字段 (Clean up the temporary "_score" key before returning)
    for item in matched_listings:
        del item["_score"]

    return matched_listings


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
    # 1. 检查用户的衣橱是否为空 (Check whether wardrobe['items'] is empty)
    items = wardrobe.get("items", [])
    
    # 准备新衣服的描述信息 (Prepare the description of the thrifted item)
    item_desc = f"{new_item.get('title')} ({new_item.get('description')})"

    # 2 & 3. 动态构建 LLM 提示词 (Dynamically build the prompt based on wardrobe status)
    if not items:
        prompt = (
            f"The user is thinking about buying this secondhand item: {item_desc}. "
            f"Their wardrobe is currently empty in the system. "
            f"Please give them 1-2 general styling ideas. What kind of vibe does it suit, and what general clothing pieces would pair well with it? Keep it friendly and conversational."
        )
    else:
        wardrobe_str = "\n".join([f"- {w.get('name')} (Style: {', '.join(w.get('style_tags', []))})" for w in items])
        prompt = (
            f"The user is thinking about buying this secondhand item: {item_desc}.\n\n"
            f"Here is their current wardrobe:\n{wardrobe_str}\n\n"
            f"Suggest 1-2 complete outfits combining the new item with specific pieces from their wardrobe. Be explicit about which of their items you are using. Keep it friendly and conversational."
        )

    client = _get_groq_client()

    # 4. 调用 LLM 并返回结果 (Call the LLM and return its response)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile", # 使用官方推荐的最强模型 (Use the recommended 70b versatile model)
        messages=[
            {"role": "system", "content": "You are a helpful and trendy personal fashion stylist."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=300
    )

    return response.choices[0].message.content


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
    # 1. 检查传入的搭配建议是否为空或只有空格 (Guard against an empty or whitespace-only outfit string)
    if not outfit or not outfit.strip():
        return "Unable to create fit card: outfit details missing."

    # 准备新衣服的详细信息供模型使用 (Prepare the item details for the prompt)
    item_title = new_item.get('title', 'this item')
    item_price = new_item.get('price', 'a great price')
    item_platform = new_item.get('platform', 'a secondhand shop')

    # 2. 构建提示词，明确社交媒体文案的要求 (Build the prompt for social media caption)
    prompt = (
        f"I just bought '{item_title}' for ${item_price} on {item_platform}.\n\n"
        f"Here is how I plan to style it: {outfit}\n\n"
        f"Write a short, catchy, 2-4 sentence social media caption for this outfit. "
        f"Make it feel casual and authentic. You MUST naturally mention the item name, price, and platform. "
        f"Capture the specific vibe of the outfit. Do not include quotes around the caption."
    )

    client = _get_groq_client()

    # 3. 调用 LLM 并返回结果 (Call the LLM and return its response)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile", # 使用官方推荐的最强模型
        messages=[
            {"role": "system", "content": "You are a trendy fashion influencer writing authentic OOTD (Outfit of the Day) captions."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.85, # 使用较高的温度，确保每次生成的文案都有不同的创意 (Higher temp for creative variance)
        max_tokens=150
    )

    return response.choices[0].message.content.strip()
