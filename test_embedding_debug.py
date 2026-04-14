"""调试 qwen3-vl-embedding API"""
import requests
import base64
import json

api_key = "sk-d67d72c8791845df961e722ad90ebcf3"
base_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-embedding/embedding"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}

# 测试1: 使用在线图片URL
print("=== 测试1: 使用在线图片URL ===")
payload1 = {
    "model": "qwen3-vl-embedding",
    "input": {
        "images": ["https://i.imgur.com/7WZ3Q4Y.jpg"],
        "image_types": ["url"]
    }
}

try:
    response = requests.post(base_url, headers=headers, json=payload1, timeout=60)
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text}")
except Exception as e:
    print(f"错误: {e}")

print("\n" + "="*50 + "\n")

# 测试2: 使用base64图片
print("=== 测试2: 使用base64图片 ===")
try:
    # 下载一个小图片
    img_url = "https://neeko-copilot.bytedance.net/api/text2image?prompt=anime%20girl%20face%20simple&image_size=square"
    img_response = requests.get(img_url, timeout=30)
    img_base64 = base64.b64encode(img_response.content).decode("utf-8")
    print(f"图片Base64长度: {len(img_base64)}")
    
    payload2 = {
        "model": "qwen3-vl-embedding",
        "input": {
            "images": [img_base64],
            "image_types": ["base64"]
        }
    }
    
    response = requests.post(base_url, headers=headers, json=payload2, timeout=60)
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text}")
except Exception as e:
    print(f"错误: {e}")

print("\n" + "="*50 + "\n")

# 测试3: 尝试不同的端点
print("=== 测试3: 尝试不同的端点 ===")
test_endpoints = [
    "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-embedding/embedding",
    "https://dashscope.aliyuncs.com/api/v1/text-embedding/text-embedding"
]

for endpoint in test_endpoints:
    print(f"\n测试端点: {endpoint}")
    try:
        if "text-embedding" in endpoint:
            # 文本embedding使用不同的格式
            payload = {"model": "text-embedding-v1", "input": {"text": "test"}}
        else:
            payload = {
                "model": "qwen3-vl-embedding",
                "input": {
                    "images": ["https://i.imgur.com/7WZ3Q4Y.jpg"],
                    "image_types": ["url"]
                }
            }
        
        response = requests.post(endpoint, headers=headers, json=payload, timeout=60)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text[:300]}")
    except Exception as e:
        print(f"错误: {e}")