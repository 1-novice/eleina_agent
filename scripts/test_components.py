#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试所有核心组件"""

import sys
import time
from datetime import timedelta
sys.path.insert(0, '.')

from src.components.session_manager import session_manager
from src.components.state_machine import state_machine, State
from src.components.task_progress_manager import task_progress_manager
from src.components.slot_filler import slot_filler
from src.components.context_compressor import context_compressor
from src.components.interrupt_controller import interrupt_controller

def test_session_manager():
    """测试会话管理器"""
    print("=" * 60)
    print("测试会话管理器")
    print("=" * 60)
    
    # 创建会话
    session_id = session_manager.create_session(
        user_id="user_001",
        device="desktop",
        source="web"
    )
    print(f"创建会话: {session_id}")
    
    # 获取会话
    session = session_manager.get_session(session_id)
    print(f"获取会话: {session is not None}")
    print(f"会话状态: {session.get('status')}")
    
    # 更新上下文
    session_manager.update_context(session_id, {
        "role": "user",
        "content": "你好",
        "timestamp": "2024-01-01T00:00:00"
    })
    print(f"上下文长度: {len(session.get('context', []))}")
    
    # 获取用户会话
    sessions = session_manager.get_user_sessions("user_001")
    print(f"用户会话数: {len(sessions)}")
    
    # 检查会话活跃状态
    is_active = session_manager.is_session_active(session_id)
    print(f"会话活跃: {is_active}")
    
    # 销毁会话
    session_manager.destroy_session(session_id)
    print(f"会话已销毁: {session_manager.get_session(session_id) is None}")
    
    print("✓ 会话管理器测试完成")

def test_state_machine():
    """测试状态机引擎"""
    print("\n" + "=" * 60)
    print("测试状态机引擎")
    print("=" * 60)
    
    # 重置状态机
    state_machine.reset()
    print(f"初始状态: {state_machine.get_state().value}")
    
    # 执行状态转换
    state_machine.step(need_retrieval=True)
    print(f"转换后状态: {state_machine.get_state().value}")
    
    state_machine.step(retrieval_error=False)
    print(f"转换后状态: {state_machine.get_state().value}")
    
    state_machine.step(answer_generated=True)
    print(f"转换后状态: {state_machine.get_state().value}")
    
    # 检查状态历史
    history = state_machine.get_history()
    print(f"状态历史长度: {len(history)}")
    
    # 保存和加载状态
    state_json = state_machine.save_state()
    print(f"状态序列化长度: {len(state_json)}")
    
    state_machine.reset()
    state_machine.load_state(state_json)
    print(f"加载后状态: {state_machine.get_state().value}")
    
    print("✓ 状态机引擎测试完成")

def test_task_progress_manager():
    """测试任务进度管理器"""
    print("\n" + "=" * 60)
    print("测试任务进度管理器")
    print("=" * 60)
    
    # 创建任务
    task_id = task_progress_manager.create_task(
        intent="order_train_ticket",
        slots={"from": "北京"},
        total_steps=4
    )
    print(f"创建任务: {task_id}")
    
    # 更新任务步骤
    task_progress_manager.set_step(task_id, 1, "确认出发地", "completed")
    task_progress_manager.set_step(task_id, 2, "确认目的地", "completed")
    task_progress_manager.set_step(task_id, 3, "选择日期", "running")
    
    # 更新槽位
    task_progress_manager.set_slots(task_id, {"to": "上海", "date": "2026-04-15"})
    
    # 获取任务进度
    progress = task_progress_manager.get_task_progress(task_id)
    print(f"任务进度: {progress:.1f}%")
    
    # 完成任务
    task_progress_manager.complete_task(task_id, {"ticket_id": "T12345"})
    
    # 获取任务
    task = task_progress_manager.get_task(task_id)
    print(f"任务状态: {task.get('status')}")
    
    print("✓ 任务进度管理器测试完成")

def test_slot_filler():
    """测试槽位填充器"""
    print("\n" + "=" * 60)
    print("测试槽位填充器")
    print("=" * 60)
    
    # 定义槽位
    slot_filler.define_slots([
        {"name": "from", "required": True, "entity_type": "city", "prompt": "出发城市"},
        {"name": "to", "required": True, "entity_type": "city", "prompt": "到达城市"},
        {"name": "date", "required": True, "entity_type": "date", "prompt": "出发日期"}
    ])
    
    # 提取槽位
    text = "我想订从北京到上海的火车票，日期是2026年4月15日"
    extracted = slot_filler.extract_slots(text)
    print(f"抽取结果: {extracted}")
    
    # 检查缺失槽位
    missing = slot_filler.get_missing_slots()
    print(f"缺失槽位: {missing}")
    
    # 填充槽位
    slot_filler.fill_slot("from", "北京")
    slot_filler.fill_slot("to", "上海")
    slot_filler.fill_slot("date", "2026-04-15")
    
    # 检查是否完整
    is_complete = slot_filler.is_complete()
    print(f"槽位完整: {is_complete}")
    
    # 获取槽位值
    values = slot_filler.get_slot_values()
    print(f"槽位值: {values}")
    
    # 重置
    slot_filler.reset()
    print("✓ 槽位填充器测试完成")

def test_context_compressor():
    """测试上下文压缩器"""
    print("\n" + "=" * 60)
    print("测试上下文压缩器")
    print("=" * 60)
    
    # 创建模拟对话历史
    messages = [
        {"role": "user", "content": "你好，我想查询天气"},
        {"role": "assistant", "content": "好的，请问你想查询哪个城市的天气？"},
        {"role": "user", "content": "北京"},
        {"role": "assistant", "content": "北京今天晴转多云，温度15-25度"},
        {"role": "user", "content": "那上海呢？"},
        {"role": "assistant", "content": "上海今天阴有小雨，温度18-22度"},
        {"role": "user", "content": "谢谢"},
        {"role": "assistant", "content": "不客气，有问题随时问我"}
    ]
    
    # 设置系统提示
    context_compressor.set_system_prompt("你是一个智能助手")
    
    # 压缩上下文
    compressed = context_compressor.compress(messages, keep_recent_rounds=2)
    print(f"原始消息数: {len(messages)}")
    print(f"压缩后消息数: {len(compressed)}")
    
    # 清理上下文
    cleaned = context_compressor.clean_context(messages)
    print(f"清理后消息数: {len(cleaned)}")
    
    # 合并连续消息
    merged = context_compressor.merge_consecutive_same_role(messages)
    print(f"合并后消息数: {len(merged)}")
    
    print("✓ 上下文压缩器测试完成")

def test_interrupt_controller():
    """测试中断控制器"""
    print("\n" + "=" * 60)
    print("测试中断控制器")
    print("=" * 60)
    
    # 创建会话
    session_id = session_manager.create_session("user_001")
    
    # 设置超时
    def timeout_handler(sid):
        print(f"超时处理: {sid}")
    
    interrupt_controller.set_timeout(session_id, timedelta(seconds=10), timeout_handler)
    print("已设置超时")
    
    # 暂停会话
    interrupt_controller.pause_session(session_id, "user_request")
    print(f"暂停会话数: {len(interrupt_controller.get_paused_sessions())}")
    
    # 恢复会话
    resumed = interrupt_controller.resume_session(session_id)
    print(f"会话已恢复: {resumed}")
    
    # 强制退出
    interrupt_controller.force_quit(session_id)
    print(f"会话已退出: {session_manager.get_session(session_id) is None}")
    
    print("✓ 中断控制器测试完成")

def main():
    """主测试函数"""
    print("=" * 60)
    print("测试所有核心组件")
    print("=" * 60)
    
    test_session_manager()
    test_state_machine()
    test_task_progress_manager()
    test_slot_filler()
    test_context_compressor()
    test_interrupt_controller()
    
    print("\n" + "=" * 60)
    print("所有组件测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    import time
    main()
