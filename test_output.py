import os
os.environ['DASHSCOPE_API_KEY'] = 'sk-d67d72c8791845df961e722ad90ebcf3'

output = []
output.append("=== 测试 DashScope SDK ===")

try:
    from dashscope import MultiModalEmbedding
    output.append("1. SDK导入成功")
except ImportError as e:
    output.append(f"1. SDK导入失败: {e}")
    with open("output.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(output))
    exit(1)

output.append("2. 调用 qwen3-vl-embedding...")

import requests
import base64

try:
    img_url = "https://i.imgur.com/7WZ3Q4Y.jpg"
    img_data = requests.get(img_url, timeout=30).content
    img_base64 = base64.b64encode(img_data).decode("utf-8")
    output.append(f"3. 图片Base64长度: {len(img_base64)}")
    
    response = MultiModalEmbedding.call(
        model=MultiModalEmbedding.Models.qwen3_vl_embedding,
        input=[{"image": img_base64}]
    )
    
    output.append(f"4. 响应状态码: {response.status_code}")
    
    if response.status_code == 200:
        embedding = response.output.embeddings[0].embedding
        output.append(f"5. ✅ 成功! Embedding维度: {len(embedding)}")
        output.append(f"6. 前5个值: {embedding[:5]}")
    else:
        output.append(f"5. ❌ 失败: {response.message}")
        
except Exception as e:
    output.append(f"错误: {e}")
    import traceback
    output.append(f"详细错误: {traceback.format_exc()}")

# 写入文件
with open("test_output_result.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(output))

print("结果已写入 test_output_result.txt")