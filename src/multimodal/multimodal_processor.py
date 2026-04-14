"""图像多模态处理器 - 独立无状态模块，不进入对话历史"""
from typing import Optional, Dict, Any, Union, Tuple
from .image_to_text import ImageToText
from .character_recognizer import CharacterRecognizer


class ImageProcessor:
    """图像处理器 - 独立无状态设计，支持角色识别和图片描述"""
    
    def __init__(self):
        self.image_to_text = ImageToText()
        self.character_recognizer = CharacterRecognizer()
        self.enabled = True
        self.character_recognition_enabled = True
    
    def configure(self, config: Dict[str, Any]):
        """配置图像处理器"""
        if "image_to_text" in config:
            self.image_to_text.api_key = config["image_to_text"].get("api_key")
            self.image_to_text.model = config["image_to_text"].get("model", "qwen-vl-plus")
            self.character_recognizer.api_key = config["image_to_text"].get("api_key")
        
        self.enabled = config.get("enabled", True)
        self.character_recognition_enabled = config.get("character_recognition_enabled", True)
        print("✓ 图像处理器配置完成")
    
    def recognize_character(self, image_path: str) -> Tuple[str, float]:
        """独立的角色识别方法 - 不影响图片描述"""
        if not self.character_recognition_enabled:
            return "", 0.0
        return self.character_recognizer.recognize_character(image_path)
    
    def describe_image(self, image_data: str, input_type: str = "base64", prompt: str = "") -> str:
        """独立的图片描述方法 - 无上下文、无历史，纯客观描述"""
        return self.image_to_text.process(image_data, input_type, prompt)
    
    def process_images(self, images: list) -> str:
        """
        处理图片列表，转换为客观描述文本
        
        Args:
            images: 图片列表，每个元素包含data和type字段
        
        Returns:
            图片描述文本，不包含任何历史上下文或角色识别信息
        """
        if not images or not self.enabled:
            return ""
        
        descriptions = []
        for i, image in enumerate(images):
            desc = self._process_single_image(image)
            if desc:
                descriptions.append(f"【图片{i+1}】{desc}")
        
        return "\n".join(descriptions)
    
    def _process_single_image(self, image_info: Dict[str, Any]) -> str:
        """处理单个图片 - 无上下文、无历史，纯客观描述"""
        try:
            image_data = image_info.get("data", "")
            input_type = image_info.get("type", "base64")
            prompt = image_info.get("prompt", "")
            
            return self.image_to_text.process(image_data, input_type, prompt)
        except Exception as e:
            print(f"图片处理失败: {e}")
            return ""
    
    def enhance_message(self, user_message: str, images: Optional[list] = None) -> str:
        """
        增强用户消息，拼接图片描述（前置拼接，不进入对话历史）
        
        Args:
            user_message: 用户原始文本消息
            images: 图片列表
        
        Returns:
            增强后的消息文本（仅包含图片描述，不含角色识别结果）
        """
        if not images or not self.enabled:
            return user_message
        
        image_descriptions = self.process_images(images)
        if image_descriptions:
            return image_descriptions + "\n\n" + user_message
        
        return user_message