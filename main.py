"""全能智能体动漫角色Agent - 集成状态管理组件"""
from src.agent.execution_controller import execution_controller
from src.memory import memory_manager
from src.tools import tool_registry
from src.components import (
    session_manager,
    state_machine,
    task_progress_manager,
    slot_filler,
    context_compressor,
    interrupt_controller
)


def main():
    """主函数 - 集成状态管理组件"""
    print("=== 全能智能体动漫角色Agent ===")
    print("输入 'exit' 退出")
    print("输入 'status' 查看状态")
    print("输入 'reset' 重置会话")
    
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
    
    # 注册天气查询意图
    from src.skill.intent_registry import intent_registry
    intent_registry.register_intent(
        intent_name="weather_intent",
        patterns=["天气", "气温", "温度", "下雨", "晴天", "多云", "刮风", "下雪"],
        skill_id="weather_skill",
        confidence_threshold=0.2,
        priority=1
    )
    print("✓ 天气查询意图注册成功")
    
    # 创建用户会话
    user_id = "default_user"
    session_id = session_manager.create_session(
        user_id=user_id,
        device="terminal",
        source="cli"
    )
    print(f"✓ 会话创建成功: {session_id[:8]}...")
    
    # 设置会话超时（30分钟）
    def on_timeout(sid):
        print(f"\n⚠️ 会话 {sid[:8]}... 超时，已暂停")
    
    interrupt_controller.set_timeout(session_id, handler=on_timeout)
    
    # 设置上下文压缩器
    context_compressor.set_system_prompt("你是伊蕾娜，一位旅行者，温柔优雅，喜欢旅行和讲故事。")
    
    print("\n=== 开始对话 ===")
    
    # 交互模式
    while True:
        user_input = input("\n用户: ")
        
        if user_input.lower() == "exit":
            print("Agent: 再见！旅途愉快！")
            session_manager.destroy_session(session_id)
            break
        
        if user_input.lower() == "status":
            # 显示当前状态
            print("\n=== 当前状态 ===")
            print(f"会话ID: {session_id[:8]}...")
            print(f"会话状态: {session_manager.get_session(session_id).get('status', 'unknown')}")
            print(f"状态机状态: {state_machine.get_state().value}")
            print(f"活跃任务数: {len(task_progress_manager.get_tasks_by_session(session_id))}")
            print(f"上下文长度: {len(session_manager.get_session(session_id).get('context', []))}")
            continue
        
        if user_input.lower() == "reset":
            # 重置会话
            session_manager.destroy_session(session_id)
            session_id = session_manager.create_session(user_id=user_id, device="terminal", source="cli")
            state_machine.reset()
            task_progress_manager.cleanup_expired_tasks()
            print("Agent: 会话已重置，重新开始吧！")
            continue
        
        # 更新会话上下文
        session_manager.update_context(session_id, {
            "role": "user",
            "content": user_input,
            "timestamp": "2024-01-01T00:00:00"  # 实际应用中应该使用当前时间
        })
        
        # 提取并写入记忆
        memory_manager.writer.extract_and_write_memory(user_id, session_id, user_input)
        
        # 获取上下文并压缩
        session = session_manager.get_session(session_id)
        context_history = session.get("context", [])
        compressed_context = context_compressor.compress(context_history, keep_recent_rounds=5)
        
        # 重置超时计时器
        interrupt_controller.reset_timeout(session_id)
        
        # 设置状态机上下文
        state_machine.context.update({
            "user_input": user_input,
            "session_id": session_id,
            "context_length": len(compressed_context)
        })
        
        # 状态机转换 - 理解意图
        state_machine.step()
        print(f"状态机状态: {state_machine.get_state().value}")
        
        # 获取上下文
        context = {
            "user_id": user_id,
            "session_id": session_id,
            "stream": False,
            "compressed_context": compressed_context
        }
        
        # 执行查询
        print("执行查询...")
        result = execution_controller.execute(user_input, context)
        
        # 状态机转换 - 根据结果更新状态
        if result.get("status") == "completed":
            state_machine.step(answer_generated=True)
            assistant_response = result.get('final_result', {}).get('answer', result.get('answer', '完成'))
            memory_manager.writer.write_dialog_memory(session_id, "assistant", assistant_response)
            session_manager.update_context(session_id, {
                "role": "assistant",
                "content": assistant_response,
                "timestamp": "2024-01-01T00:00:01"
            })
        elif result.get("status") == "timeout":
            state_machine.step(retrieval_error=True)
        elif result.get("status") == "error":
            state_machine.step()  # 转换到ERROR状态
        
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
