"""测试qwen3-vl-embedding API - 使用官方文档格式"""
import requests
import base64

api_key = "sk-d67d72c8791845df961e722ad90ebcf3"
base_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-embedding/embedding"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}

# 下载测试图片
image_url = "https://neeko-copilot.bytedance.net/api/text2image?prompt=anime%20girl%20portrait&image_size=square"

print(f"正在下载图片: {image_url}")
try:
    image_response = requests.get(image_url, timeout=30)
    image_response.raise_for_status()
    
    # 转换为base64
    image_base64 = base64.b64encode(image_response.content).decode("utf-8")
    print(f"图片下载成功，Base64长度: {len(image_base64)}")
    
    # 调用embedding API - 使用官方文档格式
    payload = {
        "model": "qwen3-vl-embedding",
        "input": {
            "contents": [
                {"type": "image", "image": image_base64, "image_type": "base64"}
            ]
        }
    }
    
    print("\n正在调用qwen3-vl-embedding API...")
    print(f"模型: qwen3-vl-embedding")
    
    response = requests.post(base_url, headers=headers, json=payload, timeout=120)
    print(f"\n响应状态码: {response.status_code}")
    print(f"响应内容: {response.text}")
    
    if response.status_code == 200:
        result = response.json()
        output = result.get("output", {})
        embeddings = output.get("embeddings", [])
        if embeddings and len(embeddings) > 0:
            embedding = embeddings[0]
            print(f"\n✅ Embedding生成成功!")
            print(f"向量维度: {len(embedding)}")
            print(f"向量前10个值: {embedding[:10]}")
            print(f"\n建议设置向量维度为: {len(embedding)}")
        else:
            print("\n❌ 未获取到Embedding")
    else:
        print(f"\n❌ API调用失败: {response.status_code}")
        
except requests.exceptions.RequestException as e:
    print(f"\n❌ 请求异常: {e}")