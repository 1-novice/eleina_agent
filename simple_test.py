import requests
import base64

api_key = "sk-d67d72c8791845df961e722ad90ebcf3"

# 测试文本embedding
print("测试 text-embedding-v1...")
headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
payload = {"model": "text-embedding-v1", "input": {"text": "test"}}

response = requests.post("https://dashscope.aliyuncs.com/api/v1/text-embedding/text-embedding", headers=headers, json=payload)
print(f"状态码: {response.status_code}")
print(f"响应: {response.text}")

# 测试多模态embedding用URL
print("\n测试 qwen3-vl-embedding (URL)...")
payload2 = {"model": "qwen3-vl-embedding", "input": {"contents": [{"type": "image", "image": "https://i.imgur.com/7WZ3Q4Y.jpg"}]}}
response2 = requests.post("https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-embedding/embedding", headers=headers, json=payload2)
print(f"状态码: {response2.status_code}")
print(f"响应: {response2.text}")