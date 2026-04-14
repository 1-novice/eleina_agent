"""调试 qwen3-vl-embedding API"""
import requests
import json

api_key = "sk-d67d72c8791845df961e722ad90ebcf3"
base_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-embedding/embedding"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}

# 测试用在线图片
test_url = "https://i.imgur.com/7WZ3Q4Y.jpg"

print("=== 测试 qwen3-vl-embedding API ===")
print(f"API Key: {api_key[:10]}...")
print(f"端点: {base_url}")
print(f"测试图片URL: {test_url}")

# 测试1: 使用URL格式
print("\n--- 测试1: 使用URL格式 ---")
payload1 = {
    "model": "qwen3-vl-embedding",
    "input": {
        "contents": [
            {"type": "image", "image": test_url}
        ]
    }
}

try:
    response = requests.post(base_url, headers=headers, json=payload1, timeout=60)
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text}")
except Exception as e:
    print(f"错误: {e}")

# 测试2: 使用base64格式
print("\n--- 测试2: 使用base64格式 ---")
try:
    # 下载图片并转换为base64
    img_response = requests.get(test_url, timeout=30)
    import base64
    img_base64 = base64.b64encode(img_response.content).decode("utf-8")
    print(f"图片Base64长度: {len(img_base64)}")
    
    payload2 = {
        "model": "qwen3-vl-embedding",
        "input": {
            "contents": [
                {"type": "image", "image": f"data:image/jpeg;base64,{img_base64}"}
            ]
        }
    }
    
    response = requests.post(base_url, headers=headers, json=payload2, timeout=60)
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text}")
except Exception as e:
    print(f"错误: {e}")

# 测试3: 尝试不同的模型
print("\n--- 测试3: 尝试 text-embedding-v1 ---")
payload3 = {
    "model": "text-embedding-v1",
    "input": {
        "text": "测试文本"
    }
}

try:
    response = requests.post(
        "https://dashscope.aliyuncs.com/api/v1/text-embedding/text-embedding",
        headers=headers,
        json=payload3,
        timeout=60
    )
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text[:500]}")
except Exception as e:
    print(f"错误: {e}")