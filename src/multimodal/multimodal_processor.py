"""多模态处理器 - 统一协调图像、语音输入输出"""
from typing import Optional, Dict, Any, Union
from .image_to_text import ImageToText
from .speech_to_text import SpeechToText
from .text_to_speech import TextToSpeech


class MultimodalProcessor:
    """多模态处理器 - 非侵入式增强架构"""
    
    def __init__(self):
        self.image_processor = ImageToText()
        self.speech_processor = SpeechToText()
        self.tts_processor = TextToSpeech()
        self.enabled = True
    
    def configure(self, config: Dict[str, Any]):
        """配置多模态模块 - 使用阿里大模型API"""
        if "image_to_text" in config:
            self.image_processor.api_key = config["image_to_text"].get("api_key")
            self.image_processor.model = config["image_to_text"].get("model", "qwen-vl-max")
        
        if "speech_to_text" in config:
            self.speech_processor.api_key = config["speech_to_text"].get("api_key")
            self.speech_processor.api_secret = config["speech_to_text"].get("api_secret")
        
        if "text_to_speech" in config:
            self.tts_processor.api_key = config["text_to_speech"].get("api_key")
            self.tts_processor.api_secret = config["text_to_speech"].get("api_secret")
        
        self.enabled = config.get("enabled", True)
        print("✓ 多模态处理器配置完成（阿里大模型API）")
    
    def process_input(self, input_data: Union[str, Dict[str, Any]]) -> str:
        """
        处理用户输入，自动识别并转换多模态内容
        
        Args:
            input_data: 可以是纯文本字符串，或包含多模态信息的字典
        
        Returns:
            统一的文本格式输入
        """
        if not self.enabled:
            return str(input_data)
        
        if isinstance(input_data, dict):
            # 处理结构化多模态输入
            text_parts = []
            
            # 处理图片
            if "images" in input_data:
                for image in input_data["images"]:
                    image_text = self._process_image(image)
                    if image_text:
                        text_parts.append(f"【图片内容】{image_text}")
            
            # 处理语音
            if "speech" in input_data:
                speech_text = self._process_speech(input_data["speech"])
                if speech_text:
                    text_parts.append(f"【语音内容】{speech_text}")
            
            # 处理文本
            if "text" in input_data:
                text_parts.append(input_data["text"])
            
            return "\n".join(text_parts)
        
        return str(input_data)
    
    def _process_image(self, image_info: Dict[str, Any]) -> str:
        """处理单个图片"""
        try:
            image_data = image_info.get("data", "")
            input_type = image_info.get("type", "base64")
            prompt = image_info.get("prompt", "")
            
            return self.image_processor.process(image_data, input_type, prompt)
        except Exception as e:
            print(f"图片处理失败: {e}")
            return ""
    
    def _process_speech(self, speech_info: Dict[str, Any]) -> str:
        """处理语音输入"""
        try:
            audio_data = speech_info.get("data", "")
            input_type = speech_info.get("type", "file")
            format = speech_info.get("format", "wav")
            
            return self.speech_processor.process(audio_data, input_type, format)
        except Exception as e:
            print(f"语音处理失败: {e}")
            return ""
    
    def process_output(self, text: str, output_mode: str = "text") -> Union[str, bytes]:
        """
        处理Agent输出，根据模式返回不同格式
        
        Args:
            text: Agent生成的文本回答
            output_mode: "text" | "speech"
        
        Returns:
            文本或语音数据
        """
        if not self.enabled or output_mode == "text":
            return text
        
        if output_mode == "speech":
            return self.tts_processor.process(text)
        
        return text
    
    def enhance_user_message(self, user_message: str, images: Optional[list] = None) -> str:
        """
        增强用户消息，拼接图片描述
        
        Args:
            user_message: 用户原始文本消息
            images: 图片列表，每个元素包含data和type字段
        
        Returns:
            增强后的消息文本
        """
        if not images or not self.enabled:
            return user_message
        
        image_descriptions = []
        for i, image in enumerate(images):
            desc = self._process_image(image)
            if desc:
                image_descriptions.append(f"【图片{i+1}】{desc}")
        
        if image_descriptions:
            return "\n".join(image_descriptions) + "\n\n" + user_message
        
        return user_message