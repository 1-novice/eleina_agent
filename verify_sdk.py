import os
from dotenv import load_dotenv

# 确保路径正确
os.chdir(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()
api_key = os.getenv("DASHSCOPE_API_KEY")

print("Step 1: 检查API Key")
print(f"API Key存在: {api_key is not None}")

print("\nStep 2: 导入DashScope SDK")
try:
    from dashscope import MultiModalEmbedding
    print("✅ DashScope SDK导入成功")
except ImportError as e:
    print(f"❌ DashScope SDK导入失败: {e}")
    print("请运行: pip install dashscope")
    exit(1)

print("\nStep 3: 测试API调用")
MultiModalEmbedding.api_key = api_key

import requests
import base64

try:
    # 使用一个简单的在线图片
    img_url = "https://i.imgur.com/7WZ3Q4Y.jpg"
    img_data = requests.get(img_url, timeout=30).content
    img_base64 = base64.b64encode(img_data).decode("utf-8")
    
    print(f"图片Base64长度: {len(img_base64)}")
    
    response = MultiModalEmbedding.call(
        model=MultiModalEmbedding.Models.qwen3_vl_embedding,
        input=[{"image": img_base64}]
    )
    
    print(f"响应状态码: {response.status_code}")
    
    if response.status_code == 200:
        embedding = response.output.embeddings[0].embedding
        print(f"✅ 成功! Embedding维度: {len(embedding)}")
    else:
        print(f"❌ 失败: {response.message}")
        
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()