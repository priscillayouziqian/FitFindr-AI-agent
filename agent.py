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
import re


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
        "fallback_message": None,    # message explaining relaxed constraints
        "error": None,               # set if the interaction ended early
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Main agent entry point. Runs the FitFindr planning loop for a single
    user interaction and returns the completed session dict.

    Args:
        query:    Natural language user request
                  (e.g., "vintage graphic tee under $30, size M")
        wardrobe: User's wardrobe dict — use get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py

    Returns:
        The session dict after the interaction completes. Check session["error"]
        first — if it is not None, the interaction ended early and the other
        output fields (outfit_suggestion, fit_card) will be None.

    TODO — implement this function using the planning loop you designed in planning.md:

        Step 1: Initialize the session with _new_session().

        Step 2: Parse the user's query to extract a description, size, and
                max_price. You can use regex, string splitting, or ask the LLM
                to parse it — document your choice in planning.md.
                Store the result in session["parsed"].

        Step 3: Call search_listings() with the parsed parameters.
                Store results in session["search_results"].
                If no results: set session["error"] to a helpful message and
                return the session early. Do NOT proceed to suggest_outfit
                with empty input.

        Step 4: Select the item to use (e.g., the top result).
                Store it in session["selected_item"].

        Step 5: Call suggest_outfit() with the selected item and wardrobe.
                Store the result in session["outfit_suggestion"].

        Step 6: Call create_fit_card() with the outfit suggestion and selected item.
                Store the result in session["fit_card"].

        Step 7: Return the session.

    Before writing code, complete the Planning Loop and State Management sections
    of planning.md — your implementation should match what you described there.
    """
    session = _new_session(query, wardrobe)

    # Step 2: 解析用户的查询 (Parse the user's query using Regular Expressions)
    # 提取最高价格 (Extract max_price, e.g., "$30", "under $30")
    max_price = None
    price_match = re.search(r'\$\s*(\d+(?:\.\d{2})?)', query)
    if price_match:
        max_price = float(price_match.group(1))

    # 提取尺寸 (Extract size, e.g., "size M", "size s/m")
    size = None
    size_match = re.search(r'size\s+([a-zA-Z0-9/]+)', query, re.IGNORECASE)
    if size_match:
        size = size_match.group(1).upper()

    # 清理查询字符串，留下纯净的衣服描述 (Clean up the query to use as the description)
    description = query.lower()
    description = re.sub(r'(under\s*)?\$\s*\d+(?:\.\d{2})?', '', description)
    description = re.sub(r'(in\s*)?size\s+[a-zA-Z0-9/]+', '', description)
    # 使用正则表达式安全地移除停用词 (Safely remove stop words using word boundaries)
    description = re.sub(r'\b(looking for|i want|i need|a|an|the)\b', '', description)
    # 将多个连续空格替换为单个空格 (Replace multiple spaces with a single space)
    description = re.sub(r'\s+', ' ', description).strip(' ,.')

    session["parsed"] = {
        "description": description,
        "size": size,
        "max_price": max_price
    }

    # Step 3: 调用 Tool 1 (Call search_listings with parsed parameters)
    results = search_listings(description=description, size=size, max_price=max_price)

    if not results:
        # 放宽条件重试逻辑 (Retry Logic with Fallback)
        if max_price is not None or size is not None:
            results = search_listings(description=description, size=None, max_price=None)
            if results:
                session["fallback_message"] = "I couldn't find an exact match for your price/size, but I removed those filters to find this for you!"

    if not results:
        # 如果放宽条件后依然没有匹配项，立刻停止并返回错误！(Halt interaction gracefully if still no results)
        session["error"] = "Sorry, I couldn't find any items matching your description. Try different keywords!"
        return session

    session["search_results"] = results

    # Step 4: 选出最佳匹配项 (Select the top item)
    session["selected_item"] = results[0]

    # Step 5 & 6: 依次调用后续工具 (Trigger the remaining tools using the session state)
    session["outfit_suggestion"] = suggest_outfit(session["selected_item"], session["wardrobe"])
    session["fit_card"] = create_fit_card(session["outfit_suggestion"], session["selected_item"])

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
        print(f"Parsed: {session['parsed']}")
        print(f"Found: {session['selected_item']['title']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session2['error']}")

    print("\n\n=== Retry with fallback path ===\n")
    session3 = run_agent(
        query="vintage graphic tee under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Fallback message: {session3.get('fallback_message')}")
    if session3.get("selected_item"):
        print(f"Found: {session3['selected_item']['title']} (Price: ${session3['selected_item']['price']})")
