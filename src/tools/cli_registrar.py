"""CLI工具注册器 - 用于注册内置工具"""

from src.tools import tool_registry


def register_cli_tools():
    """注册CLI模式下使用的工具"""
    # 注册天气工具
    tool_registry.register_tool(
        name="get_weather",
        description="查询指定城市的天气信息",
        parameters={
            "city": {
                "type": "string",
                "description": "城市名称",
                "required": True
            },
            "date": {
                "type": "string",
                "description": "日期，例如：今天、明天、后天"
            }
        },
        return_schema={
            "type": "object",
            "properties": {
                "city": {"type": "string"},
                "date": {"type": "string"},
                "weather": {"type": "string"},
                "temp": {"type": "number"},
                "humidity": {"type": "string"},
                "wind": {"type": "string"}
            }
        }
    )
    print("✓ 天气工具注册成功")