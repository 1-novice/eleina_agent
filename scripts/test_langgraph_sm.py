#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试LangGraph状态机"""

import sys
sys.path.insert(0, '.')

from src.components.langgraph_state_machine import langgraph_state_machine

def test_langgraph_state_machine():
    """测试LangGraph状态机"""
    print("=" * 60)
    print("测试LangGraph状态机")
    print("=" * 60)
    
    # 测试用例
    test_cases = [
        ("你的师傅是谁", "测试检索路径"),
        ("北京天气怎么样", "测试工具调用路径"),
        ("你好", "测试直接回答路径"),
        ("?", "测试澄清路径")
    ]
    
    for query, description in test_cases:
        print(f"\n测试: {description}")
        print(f"查询: {query}")
        
        result = langgraph_state_machine.run(query, user_id="test_user", session_id="test_session")
        
        print(f"状态: {result.get('status')}")
        print(f"回答: {result.get('answer', '')[:100]}...")
        print(f"检索文档数: {len(result.get('retrieved_docs', []))}")
        
        if result.get('error_message'):
            print(f"错误: {result.get('error_message')}")
    
    print("\n" + "=" * 60)
    print("测试完成！")

if __name__ == "__main__":
    test_langgraph_state_machine()
