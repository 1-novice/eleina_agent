"""全面测试项目所有功能 - 使用本地API服务"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_multimodal():
    """测试图像多模态功能"""
    print("=" * 60)
    print("测试1: 图像多模态功能")
    print("=" * 60)
    try:
        from src.multimodal.image_processor import ImageProcessor
        processor = ImageProcessor()
        print("✓ 图像处理器初始化成功")
        
        test_image_path = "D:\\jialuo.jpg"
        if os.path.exists(test_image_path):
            base64_image = processor.image_to_base64(test_image_path)
            print(f"✓ 图片转换Base64成功，长度: {len(base64_image)}")
            
            description = processor.describe_image(base64_image)
            print(f"✓ 图片描述成功")
            print(f"  描述内容: {description[:100]}...")
        else:
            print("⚠ 测试图片不存在，跳过图片描述测试")
        
    except Exception as e:
        print(f"✗ 图像多模态测试失败: {e}")

def test_multi_round_conversation():
    """测试多轮对话功能"""
    print("\n" + "=" * 60)
    print("测试2: 多轮对话功能")
    print("=" * 60)
    try:
        from src.memory.memory_manager import memory_manager
        
        user_id = "test_user_001"
        session_id = "test_session_001"
        
        memory_manager.extract_and_write_memory(user_id, session_id, "你好")
        print("✓ 第一轮对话记忆写入成功")
        
        memory_manager.extract_and_write_memory(user_id, session_id, "我叫小明")
        print("✓ 第二轮对话记忆写入成功")
        
        memory_manager.extract_and_write_memory(user_id, session_id, "我今年25岁")
        print("✓ 第三轮对话记忆写入成功")
        
        memory = memory_manager.get_memory(user_id)
        print(f"✓ 记忆获取成功")
        print(f"  短期记忆消息数: {len(memory['short_term'])}")
        
    except Exception as e:
        print(f"✗ 多轮对话测试失败: {e}")

def test_tool_calling():
    """测试工具调用功能"""
    print("\n" + "=" * 60)
    print("测试3: 工具调用功能")
    print("=" * 60)
    try:
        from src.tools.cli_registrar import get_weather
        
        result = get_weather("北京")
        print(f"✓ 天气工具调用成功")
        print(f"  结果: {result}")
        
        result = get_weather("上海", "明天")
        print(f"✓ 带日期参数的天气工具调用成功")
        print(f"  结果: {result}")
        
    except Exception as e:
        print(f"✗ 工具调用测试失败: {e}")

def test_rag_retrieval():
    """测试RAG检索功能"""
    print("\n" + "=" * 60)
    print("测试4: RAG检索功能")
    print("=" * 60)
    try:
        from src.rag.retriever import retriever
        
        query = "什么是人工智能"
        docs = retriever.retrieve(query, k=3)
        print(f"✓ RAG检索成功")
        print(f"  检索到文档数: {len(docs)}")
        
        if docs:
            for i, doc in enumerate(docs[:2], 1):
                content = doc.get('content', doc.get('page_content', ''))
                print(f"  文档{i}: {content[:50]}...")
        
    except Exception as e:
        print(f"✗ RAG检索测试失败: {e}")

def test_state_machine():
    """测试状态机功能"""
    print("\n" + "=" * 60)
    print("测试5: 状态机功能")
    print("=" * 60)
    try:
        from src.components.langgraph_state_machine import langgraph_state_machine
        
        result = langgraph_state_machine.run("你好", user_id="test", session_id="test_state", stream=False)
        print(f"✓ 状态机运行成功")
        print(f"  状态: {result['status']}")
        
    except Exception as e:
        print(f"✗ 状态机测试失败: {e}")

def test_model_engine():
    """测试大模型引擎"""
    print("\n" + "=" * 60)
    print("测试6: 大模型引擎")
    print("=" * 60)
    try:
        from src.agent.model_engine import model_engine
        
        result = model_engine.generate({
            "messages": [{"role": "user", "content": "你好，介绍一下你自己"}],
            "stream": False,
            "user_id": "test"
        })
        print(f"✓ 非流式生成成功")
        print(f"  响应: {result['content'][:100]}...")
        
        print("  测试流式生成...")
        stream_result = model_engine.generate({
            "messages": [{"role": "user", "content": "你好"}],
            "stream": True,
            "user_id": "test"
        })
        if stream_result.get("stream"):
            content = ""
            for chunk in stream_result["content"]:
                content += chunk
            print(f"✓ 流式生成成功")
            print(f"  响应: {content[:50]}...")
        
    except Exception as e:
        print(f"✗ 大模型引擎测试失败: {e}")

def test_intent_parser():
    """测试意图识别功能"""
    print("\n" + "=" * 60)
    print("测试7: 意图识别功能")
    print("=" * 60)
    try:
        from src.agent.intent_parser import intent_parser
        
        test_cases = [
            "今天北京天气怎么样",
            "写一首诗",
            "你好",
            "帮我搜索一下人工智能"
        ]
        
        for test in test_cases:
            result = intent_parser.parse(test)
            print(f"✓ 意图识别成功: '{test}' -> {result['intent']}")
            
    except Exception as e:
        print(f"✗ 意图识别测试失败: {e}")

def main():
    """运行所有测试"""
    print("=" * 60)
    print("项目全面功能测试")
    print("=" * 60)
    print("注意：请确保本地API服务正在运行")
    print("本地API地址: http://127.0.0.1:8080/v1/chat/completions")
    
    test_multimodal()
    test_multi_round_conversation()
    test_tool_calling()
    test_rag_retrieval()
    test_state_machine()
    test_model_engine()
    test_intent_parser()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    main()