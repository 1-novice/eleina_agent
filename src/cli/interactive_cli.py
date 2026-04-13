"""交互式CLI模块 - 处理命令行交互逻辑"""

from src.agent.execution_controller import execution_controller
from src.memory import memory_manager
from src.components import (
    session_manager,
    state_machine,
    task_progress_manager,
    context_compressor,
    interrupt_controller
)


def create_session(user_id="default_user"):
    """创建用户会话"""
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
    return session_id


def handle_status(session_id):
    """显示当前状态"""
    print("\n=== 当前状态 ===")
    print(f"会话ID: {session_id[:8]}...")
    print(f"会话状态: {session_manager.get_session(session_id).get('status', 'unknown')}")
    print(f"状态机状态: {state_machine.get_state().value}")
    print(f"活跃任务数: {len(task_progress_manager.get_tasks_by_session(session_id))}")
    print(f"上下文长度: {len(session_manager.get_session(session_id).get('context', []))}")


def handle_reset(user_id="default_user"):
    """重置会话"""
    session_id = session_manager.create_session(user_id=user_id, device="terminal", source="cli")
    state_machine.reset()
    task_progress_manager.cleanup_expired_tasks()
    print("Agent: 会话已重置，重新开始吧！")
    return session_id


def process_user_input(session_id, user_input, user_id="default_user"):
    """处理用户输入"""
    # 更新会话上下文
    session_manager.update_context(session_id, {
        "role": "user",
        "content": user_input,
        "timestamp": "2024-01-01T00:00:00"
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
        state_machine.step()
    
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


def run_interactive_cli():
    """运行交互式CLI"""
    print("\n=== 开始对话 ===")
    
    user_id = "default_user"
    session_id = create_session(user_id)
    
    # 设置上下文压缩器
    context_compressor.set_system_prompt("你是伊蕾娜，一位旅行者，温柔优雅，喜欢旅行和讲故事。")
    
    # 交互模式
    while True:
        user_input = input("\n用户: ")
        
        if user_input.lower() == "exit":
            print("Agent: 再见！旅途愉快！")
            session_manager.destroy_session(session_id)
            break
        
        if user_input.lower() == "status":
            handle_status(session_id)
            continue
        
        if user_input.lower() == "reset":
            session_id = handle_reset(user_id)
            continue
        
        process_user_input(session_id, user_input, user_id)