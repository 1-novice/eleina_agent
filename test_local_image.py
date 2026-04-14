"""测试使用本地图片调用qwen3-vl-embedding"""
import requests
import base64
import os

api_key = "sk-d67d72c8791845df961e722ad90ebcf3"
base_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-embedding/embedding"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}

# 测试图片路径
test_paths = [
    "D:\\yln.png",
    "D:\\yln_rag\\yln1.png"
]

for image_path in test_paths:
    print(f"\n=== 测试图片: {image_path} ===")
    
    if not os.path.exists(image_path):
        print(f"❌ 文件不存在: {image_path}")
        continue
    
    try:
        # 读取图片并转换为base64
        with open(image_path, "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode("utf-8")
        
        print(f"图片大小: {os.path.getsize(image_path)} bytes")
        print(f"Base64长度: {len(image_base64)}")
        
        # 调用API
        payload = {
            "model": "qwen3-vl-embedding",
            "input": {
                "images": [image_base64],
                "image_types": ["base64"]
            }
        }
        
        print("正在调用qwen3-vl-embedding API...")
        response = requests.post(base_url, headers=headers, json=payload, timeout=120)
        
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            embeddings = result.get("output", {}).get("embeddings", [])
            if embeddings:
                print(f"\n✅ 成功! 向量维度: {len(embeddings[0])}")
            else:
                print("\n❌ 未获取到embedding")
                
    except Exception as e:
        print(f"错误: {e}")