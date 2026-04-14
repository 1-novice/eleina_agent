import os
os.environ['DASHSCOPE_API_KEY'] = 'sk-d67d72c8791845df961e722ad90ebcf3'

print("=== 测试 DashScope SDK ===")

try:
    from dashscope import MultiModalEmbedding
    print("1. SDK导入成功")
except ImportError as e:
    print(f"1. SDK导入失败: {e}")
    exit(1)

print("2. 调用 qwen3-vl-embedding...")

import requests
import base64

try:
    img_url = "https://i.imgur.com/7WZ3Q4Y.jpg"
    img_data = requests.get(img_url, timeout=30).content
    img_base64 = base64.b64encode(img_data).decode("utf-8")
    
    response = MultiModalEmbedding.call(
        model=MultiModalEmbedding.Models.qwen3_vl_embedding,
        input=[{"image": img_base64}]
    )
    
    print(f"3. 响应状态码: {response.status_code}")
    
    if response.status_code == 200:
        embedding = response.output.embeddings[0].embedding
        print(f"4. ✅ 成功! Embedding维度: {len(embedding)}")
        print(f"5. 前5个值: {embedding[:5]}")
    else:
        print(f"4. ❌ 失败: {response.message}")
        
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()