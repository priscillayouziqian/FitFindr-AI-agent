import sys
import os
# 将项目根目录添加到系统路径中 (Add root directory to system path)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent import run_agent
from utils.data_loader import get_example_wardrobe

# ── Agent Integration Tests (集成测试) ───────────────────────────────────────

def test_agent_no_results_early_return():
    """测试：完全搜不到时，是否正确阻断并返回错误 (Test early halt on zero results)"""
    wardrobe = get_example_wardrobe()
    session = run_agent("designer ballgown size XXS under $5", wardrobe)
    
    # 验证是否返回了错误信息 (Verify error is set)
    assert session["error"] is not None
    assert "couldn't find" in session["error"].lower()
    # 验证是否及时阻断，没有去调用后续大模型 (Verify selected_item is empty)
    assert session["selected_item"] is None
    assert session["outfit_suggestion"] is None

def test_agent_retry_fallback_logic():
    """测试：条件过严时，是否触发了降级重试逻辑 (Test retry/fallback constraint relaxation)"""
    wardrobe = get_example_wardrobe()
    # 数据库里没有低于 $5 的 T 恤，但有价格更高的 (No tee under $5, but tees exist)
    session = run_agent("vintage graphic tee under $5", wardrobe)
    
    # 验证没有发生全局错误 (Verify no hard error)
    assert session["error"] is None
    # 验证是否触发了降级提示文案 (Verify fallback message is set)
    assert session["fallback_message"] is not None
    assert "removed those filters" in session["fallback_message"]
    # 验证最终还是找到了一件衣服 (Verify it actually found an item)
    assert session["selected_item"] is not None

def test_agent_style_memory_persistence():
    """测试：风格记忆是否能正确提取和跨轮次继承 (Test style profile extraction and passing)"""
    wardrobe = get_example_wardrobe()
    
    # 第一轮交互：包含风格偏好 (Interaction 1: mentions styles)
    session1 = run_agent("I love y2k and grunge", wardrobe)
    assert "y2k" in session1["style_profile"]
    assert "grunge" in session1["style_profile"]
    
    # 第二轮交互：不提风格，但传入记忆 (Interaction 2: no styles, but passes memory)
    # 模拟前端 Gradio 的 gr.State 行为
    session2 = run_agent("Find me some boots", wardrobe, style_profile=session1["style_profile"])
    
    # 验证记忆是否被成功继承 (Verify memory persisted)
    assert "y2k" in session2["style_profile"]
    assert "grunge" in session2["style_profile"]