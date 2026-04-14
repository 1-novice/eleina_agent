import requests
import base64

api_key = "sk-d67d72c8791845df961e722ad90ebcf3"

# 下载测试图片
url = "https://neeko-copilot.bytedance.net/api/text2image?prompt=anime%20girl%20portrait&image_size=square"
img_data = requests.get(url).content
img_b64 = base64.b64encode(img_data).decode()

print(f"Image downloaded: {len(img_b64)} bytes")

# 调用API
headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
payload = {"model": "qwen3-vl-embedding", "input": {"image": img_b64, "image_type": "base64"}}

resp = requests.post("https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-embedding/embedding", headers=headers, json=payload)
print(f"Status: {resp.status_code}")
print(f"Response: {resp.text}")