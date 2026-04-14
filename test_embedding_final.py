"""最终测试 qwen3-vl-embedding API"""
import requests
import base64
import json

api_key = "sk-d67d72c8791845df961e722ad90ebcf3"

# 尝试不同的端点
endpoints = [
    "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-embedding/embedding",
    "https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/multimodal-embedding/embedding"
]

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}

# 下载测试图片
image_url = "https://neeko-copilot.bytedance.net/api/text2image?prompt=anime%20girl%20simple%20portrait&image_size=square"
image_response = requests.get(image_url, timeout=30)
image_base64 = base64.b64encode(image_response.content).decode("utf-8")

print(f"图片Base64长度: {len(image_base64)}")

for endpoint in endpoints:
    print(f"\n=== 测试端点: {endpoint} ===")
    
    # 测试1: 基础格式
    payload1 = {
        "model": "qwen3-vl-embedding",
        "input": {
            "contents": [
                {"type": "image", "image": image_base64, "image_type": "base64"}
            ]
        }
    }
    
    try:
        response = requests.post(endpoint, headers=headers, json=payload1, timeout=120)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text[:500]}")
    except Exception as e:
        print(f"错误: {e}")

print("\n=== 测试使用URL ===")
payload_url = {
    "model": "qwen3-vl-embedding",
    "input": {
        "contents": [
            {"type": "image", "image": "https://i.imgur.com/7WZ3Q4Y.jpg", "image_type": "url"}
        ]
    }
}

try:
    response = requests.post(endpoints[0], headers=headers, json=payload_url, timeout=120)
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text[:500]}")
except Exception as e:
    print(f"错误: {e}")