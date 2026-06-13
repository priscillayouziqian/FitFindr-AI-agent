import sys
import os
# 将项目根目录添加到系统路径中，以便能够找到 tools 和 utils (Add root directory to system path)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools import search_listings, suggest_outfit, create_fit_card
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

# ── Tool 1 Tests ───────────────────────────────────────────────────────────

def test_search_returns_results():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert isinstance(results, list)
    assert len(results) > 0

def test_search_empty_results():
    results = search_listings("designer ballgown", size="XXS", max_price=5)
    assert results == []   # empty list, no exception

def test_search_price_filter():
    results = search_listings("jacket", size=None, max_price=10)
    # Ensure that if anything is returned, it respects the price ceiling
    assert all(item["price"] <= 10 for item in results)

# ── Tool 2 Tests ───────────────────────────────────────────────────────────

def test_suggest_outfit_with_wardrobe():
    # Mock item
    new_item = {"title": "Vintage Graphic Tee", "description": "Faded black"}
    wardrobe = get_example_wardrobe()
    
    result = suggest_outfit(new_item, wardrobe)
    assert isinstance(result, str)
    assert len(result) > 0

# ── Tool 3 Tests ───────────────────────────────────────────────────────────

def test_create_fit_card_success():
    # Mock item and outfit (模拟商品和搭配文本)
    new_item = {"title": "Y2K Baby Tee", "price": 18.0, "platform": "depop"}
    outfit = "Pairing this tee with dark wash baggy jeans and chunky white sneakers."
    
    result = create_fit_card(outfit, new_item)
    assert isinstance(result, str)
    assert len(result) > 0
    assert "Unable to create fit card" not in result

def test_create_fit_card_empty_outfit():
    # Mock an empty outfit failure case (模拟传入的搭配文本为空或缺失)
    new_item = {"title": "Y2K Baby Tee"}
    result = create_fit_card("", new_item)
    
    assert isinstance(result, str)
    assert "Unable to create fit card" in result  # 验证是否返回了我们在代码里设定的错误提示

def test_suggest_outfit_empty_wardrobe():
    # Mock item
    new_item = {"title": "Vintage Graphic Tee", "description": "Faded black"}
    wardrobe = get_empty_wardrobe()
    
    result = suggest_outfit(new_item, wardrobe)
    assert isinstance(result, str)
    assert len(result) > 0