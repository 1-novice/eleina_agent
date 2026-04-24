"""Qwen Plus模型测试脚本"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.agent.model_engine import ModelEngine


def test_qwen_plus():
    """测试Qwen Plus模型"""
    print("=== 测试Qwen Plus模型 ===")
    
    # 创建模型引擎并切换到Qwen Plus
    model_engine = ModelEngine("qwen_plus")
    
    print(f"当前模型: {model_engine.current_model}")
    print(f"已初始化的模型: {list(model_engine.models.keys())}")
    
    if "qwen_plus" not in model_engine.models:
        print("错误: Qwen Plus模型未初始化")
        return
    
    # 测试生成响应
    test_messages = [
        {"role": "user", "content": "你好，我想了解一下天气情况"}
    ]
    
    request = {
        "model": "qwen_plus",
        "messages": test_messages,
        "stream": False,
        "user_id": "test_user",
        "add_system_prompt": False
    }
    
    print("\n发送测试请求...")
    result = model_engine.generate(request)
    
    print("\n=== 测试结果 ===")
    print(f"内容: {result.get('content', '')[:200]}...")
    print(f"使用情况: {result.get('usage', {})}")
    print(f"结束原因: {result.get('finish_reason', '')}")


def test_qwen_plus_stream():
    """测试Qwen Plus流式响应"""
    print("\n=== 测试Qwen Plus流式响应 ===")
    
    model_engine = ModelEngine("qwen_plus")
    
    test_messages = [
        {"role": "user", "content": "你好，简单介绍一下自己"}
    ]
    
    request = {
        "model": "qwen_plus",
        "messages": test_messages,
        "stream": True,
        "user_id": "test_user",
        "add_system_prompt": False
    }
    
    print("\n发送流式测试请求...")
    result = model_engine.generate(request)
    
    if result.get("stream") and callable(result.get("content")):
        print("\n流式输出:")
        full_content = ""
        for chunk in result["content"]:
            print(chunk, end="", flush=True)
            full_content += chunk
        print("\n")
        print(f"完整内容长度: {len(full_content)}")
    else:
        print(f"非流式响应: {result.get('content', '')[:200]}...")


if __name__ == "__main__":
    # 检查API密钥是否配置
    if not os.getenv('DASHSCOPE_API_KEY') and not os.getenv('QIANWEN_API_KEY'):
        print("警告: 未配置API密钥，请在.env文件中设置DASHSCOPE_API_KEY或QIANWEN_API_KEY")
        print("测试将无法正常执行")
    else:
        test_qwen_plus()
        test_qwen_plus_stream()
