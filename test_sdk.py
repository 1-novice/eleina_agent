"""使用DashScope官方SDK测试qwen3-vl-embedding"""
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("DASHSCOPE_API_KEY")

if not api_key:
    print("❌ 未配置DASHSCOPE_API_KEY")
    exit(1)

try:
    from dashscope import MultiModalEmbedding
    
    # 设置API密钥
    MultiModalEmbedding.api_key = api_key
    
    # 下载测试图片
    import requests
    import base64
    
    image_url = "https://neeko-copilot.bytedance.net/api/text2image?prompt=anime%20girl%20portrait&image_size=square"
    print(f"下载测试图片: {image_url}")
    response = requests.get(image_url, timeout=30)
    image_base64 = base64.b64encode(response.content).decode("utf-8")
    
    print(f"图片Base64长度: {len(image_base64)}")
    
    # 调用多模态Embedding
    print("\n调用 qwen3-vl-embedding...")
    result = MultiModalEmbedding.call(
        model=MultiModalEmbedding.Models.qwen3_vl_embedding,
        input=[{"image": image_base64}]
    )
    
    print(f"状态码: {result.status_code}")
    
    if result.status_code == 200:
        embedding = result.output.embeddings[0].embedding
        print(f"✅ 成功! Embedding维度: {len(embedding)}")
        print(f"前10个值: {embedding[:10]}")
    else:
        print(f"❌ 失败: {result.message}")
        
except ImportError:
    print("❌ 未安装dashscope SDK，请运行: pip install dashscope")
except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()