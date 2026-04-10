from src.agent.execution_controller import execution_controller
from src.memory import memory_manager
from src.tools import tool_registry


def main():
    """主函数"""
    print("=== 全能智能体动漫角色Agent ===")
    print("输入 'exit' 退出")
    
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
    print("天气工具注册成功")
    
    # 注册天气查询意图
    from src.skill.intent_registry import intent_registry
    intent_registry.register_intent(
        intent_name="weather_intent",
        patterns=["天气", "气温", "温度", "下雨", "晴天", "多云", "刮风", "下雪"],
        skill_id="weather_skill",
        confidence_threshold=0.2,  # 降低阈值，使其更容易被识别
        priority=1
    )
    print("天气查询意图注册成功")
    
    user_id = "test_user"
    session_id = "default_session"
    
    while True:
        user_input = input("用户: ")
        if user_input.lower() == "exit":
            break
        
        # 提取并写入记忆
        memory_manager.writer.extract_and_write_memory(user_id, session_id, user_input)
        
        # 获取上下文记忆
        context = {
            "user_id": user_id,
            "session_id": session_id,
            "stream": False
        }
        
        # 执行查询
        result = execution_controller.execute(user_input, context)
        
        # 写入助手回复到记忆
        if result.get("status") == "completed":
            if "final_result" in result:
                assistant_response = result['final_result']['answer']
            else:
                assistant_response = result.get('answer', '完成')
            memory_manager.writer.write_dialog_memory(session_id, "assistant", assistant_response)
        
        # 处理执行结果
        if result.get("status") == "needs_clarification":
            print("Agent: 需要澄清")
            for question in result.get("questions", []):
                print(f"  - {question}")
        elif result.get("status") == "completed":
            if "final_result" in result:
                print(f"Agent: {result['final_result']['answer']}")
            else:
                print(f"Agent: {result.get('answer', '完成')}")
        elif result.get("status") == "paused":
            print("Agent: 任务暂停")
            print(f"当前步骤: {result['current_step']}")
            print(f"步骤内容: {result['step']['step']}")
        else:
            print(f"Agent: {result.get('answer', '处理中...')}")


if __name__ == "__main__":
    main()