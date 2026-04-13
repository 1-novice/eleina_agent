"""CLI意图注册器 - 用于注册内置意图"""

from src.skill.intent_registry import intent_registry


def register_cli_intents():
    """注册CLI模式下使用的意图"""
    # 注册天气查询意图
    intent_registry.register_intent(
        intent_name="weather_intent",
        patterns=["天气", "气温", "温度", "下雨", "晴天", "多云", "刮风", "下雪"],
        skill_id="weather_skill",
        confidence_threshold=0.2,
        priority=1
    )
    print("✓ 天气查询意图注册成功")