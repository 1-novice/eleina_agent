"""测试DashScope SDK并将结果写入文件"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("DASHSCOPE_API_KEY")

result_lines = []
result_lines.append(f"API Key: {api_key[:10] if api_key else 'None'}")

try:
    from dashscope import MultiModalEmbedding
    result_lines.append("DashScope SDK导入成功")
    
    MultiModalEmbedding.api_key = api_key
    
    import requests
    import base64
    
    image_url = "https://neeko-copilot.bytedance.net/api/text2image?prompt=anime%20girl%20portrait&image_size=square"
    result_lines.append(f"下载测试图片: {image_url}")
    
    try:
        response = requests.get(image_url, timeout=30)
        image_base64 = base64.b64encode(response.content).decode("utf-8")
        result_lines.append(f"图片Base64长度: {len(image_base64)}")
        
        result_lines.append("\n调用 qwen3-vl-embedding...")
        result = MultiModalEmbedding.call(
            model=MultiModalEmbedding.Models.qwen3_vl_embedding,
            input=[{"image": image_base64}]
        )
        
        result_lines.append(f"状态码: {result.status_code}")
        
        if result.status_code == 200:
            embedding = result.output.embeddings[0].embedding
            result_lines.append(f"✅ 成功! Embedding维度: {len(embedding)}")
            result_lines.append(f"前10个值: {embedding[:10]}")
        else:
            result_lines.append(f"❌ 失败: {result.message}")
            
    except Exception as e:
        result_lines.append(f"请求错误: {str(e)}")
        
except ImportError:
    result_lines.append("❌ DashScope SDK未安装")
except Exception as e:
    result_lines.append(f"错误: {str(e)}")

# 写入结果文件
with open("test_result.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(result_lines))
    
print("测试完成，结果已写入 test_result.txt")