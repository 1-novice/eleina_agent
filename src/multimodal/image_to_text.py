"""图像转文本模块 - 二次元专用零幻觉版本"""
import base64
import requests
from typing import Optional, Dict, Any


class ImageToText:
    """图像转文本处理器 - 二次元专用，零幻觉强约束版本"""
    
    # 二次元专用强约束提示词 - 严格禁止幻觉，只返回描述
    DEFAULT_PROMPT = """你是专业二次元图像识别专家，严格只描述图片真实存在的元素，绝对禁止脑补和添加任何额外内容。优先识别角色身份、发型发色、服饰细节、特征（如猫耳、女仆装）、画风，明确标注为二次元插画。禁止将女仆装误判为魔女制服、女仆头饰误判为魔法帽。回答必须简洁，仅包含图片描述，禁止生成AI绘画提示词、翻译或任何额外内容。"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "qwen-vl-max"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
    
    def encode_image(self, image_path: str) -> str:
        """将图片文件编码为base64"""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    
    def process(self, image_input: str, input_type: str = "base64", prompt: str = "") -> str:
        """
        处理图像转文本（二次元专用）
        
        Args:
            image_input: 图片base64字符串或URL或本地路径
            input_type: "base64" | "url" | "path"
            prompt: 额外提示词（可选，默认使用二次元专用提示词）
        
        Returns:
            图像内容的文本描述
        """
        if not self.api_key:
            return "图片内容解析失败：未配置API密钥"
        
        image_data = None
        actual_type = None
        
        if input_type == "path":
            try:
                image_data = self.encode_image(image_input)
                actual_type = "base64"
            except Exception as e:
                return f"图片读取失败: {str(e)}"
        elif input_type == "url":
            image_data = image_input
            actual_type = "url"
        else:
            image_data = image_input
            actual_type = "base64"
        
        if not image_data:
            return "图片内容解析失败：无效的图片数据"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model,
            "input": {
                "prompt": prompt or self.DEFAULT_PROMPT,
                "image": image_data,
                "image_type": actual_type
            },
            "parameters": {
                "max_tokens": 512,
                "temperature": 0.01,
                "top_p": 0.05,
                "repetition_penalty": 1.1,
                "use_raw_prompt": True
            }
        }
        
        # 调试信息
        print(f"[ImageToText] 模型: {self.model}")
        print(f"[ImageToText] 图片类型: {actual_type}")
        print(f"[ImageToText] 图片数据长度: {len(image_data) if image_data else 0}")
        print(f"[ImageToText] 请求体大小: {len(str(payload))}")
        
        try:
            response = requests.post(self.base_url, headers=headers, json=payload)
            print(f"[ImageToText] 响应状态码: {response.status_code}")
            print(f"[ImageToText] 响应内容: {response.text}")
            response.raise_for_status()
            result = response.json()
            
            output = result.get("output", {})
            if output:
                choices = output.get("choices", [])
                if choices:
                    message = choices[0].get("message", {})
                    content = message.get("content", [])
                    if content:
                        texts = []
                        for item in content:
                            if isinstance(item, dict) and "text" in item:
                                texts.append(item["text"])
                        if texts:
                            return "".join(texts)
                        return str(content)
                    return message.get("content", "")
                if "text" in output:
                    return output["text"]
                return str(output)
            else:
                error_msg = result.get("message", "图像转文本失败")
                error_code = result.get("code", "")
                return f"图片内容解析失败: {error_msg}"
        
        except requests.exceptions.RequestException as e:
            try:
                error_response = response.json() if response else {}
                error_detail = error_response.get("message", str(e))
                return f"图片内容解析异常: {error_detail}"
            except:
                return f"图片内容解析异常: {str(e)}"
        except Exception as e:
            return f"图片内容解析异常: {str(e)}"


image_to_text = ImageToText()