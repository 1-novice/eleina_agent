"""图像转文本模块 - 独立无状态模块，仅输出客观图片描述"""
import base64
from typing import Optional


class ImageToText:
    """图像转文本处理器 - 使用DashScope官方SDK，独立无状态设计"""
    
    DEFAULT_PROMPT = """
用简短客观描述图片,30-80字。
只写：角色发型、发色、服装、武器、背景关键元素。
不要艺术风格、不要氛围、不要光影、不要细节、不要分点、不要总结。
"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "qwen-vl-plus"):
        self.api_key = api_key
        self.model = model
    
    def process(self, image_input: str, input_type: str = "base64", prompt: str = "") -> str:
        if not self.api_key:
            return "图片内容解析失败：未配置API密钥"
        
        try:
            from dashscope import MultiModalConversation
            MultiModalConversation.api_key = self.api_key
            
            if input_type == "path":
                with open(image_input, "rb") as f:
                    image_data = base64.b64encode(f.read()).decode("utf-8")
            else:
                image_data = image_input
            
            if not image_data.startswith("data:image"):
                image_data = f"data:image/png;base64,{image_data}"
            
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"image": image_data},
                        {"text": prompt or self.DEFAULT_PROMPT}
                    ]
                }
            ]
            
            response = MultiModalConversation.call(model=self.model, messages=messages)
            
            if response.status_code == 200:
                content = response.output.choices[0].message.content
                if isinstance(content, list) and len(content) > 0:
                    if isinstance(content[0], dict) and 'text' in content[0]:
                        return content[0]['text']
                    elif isinstance(content[0], str):
                        return content[0]
                elif isinstance(content, str):
                    return content
                return str(content)
            else:
                return f"图片解析失败: {response.message}"
        
        except ImportError:
            return "错误：未安装 dashscope SDK"
        except Exception as e:
            return f"图片解析异常: {str(e)}"


image_to_text = ImageToText()