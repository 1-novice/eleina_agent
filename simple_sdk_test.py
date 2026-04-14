import os
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("DASHSCOPE_API_KEY")
print(f"API Key: {api_key[:10] if api_key else 'None'}")

try:
    from dashscope import MultiModalEmbedding
    print("DashScope SDK导入成功")
except ImportError:
    print("DashScope SDK未安装")