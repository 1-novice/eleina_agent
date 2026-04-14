"""多模态模块配置 - 从环境变量读取"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class ImageToTextConfig(BaseSettings):
    """图像转文本配置"""
    api_key: Optional[str] = None
    model: str = "qwen-vlr"
    enabled: bool = False
    
    model_config = SettingsConfigDict(env_prefix="image_to_text_")


class SpeechToTextConfig(BaseSettings):
    """语音转文本配置 - 阿里大模型ASR"""
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    enabled: bool = False
    
    model_config = SettingsConfigDict(env_prefix="speech_to_text_")


class TextToSpeechConfig(BaseSettings):
    """文本转语音配置 - 阿里大模型TTS"""
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    voice: str = "female"
    rate: int = 0
    volume: int = 50
    enabled: bool = False
    
    model_config = SettingsConfigDict(env_prefix="text_to_speech_")


class MultimodalConfig(BaseSettings):
    """多模态配置"""
    enabled: bool = False
    image_to_text: ImageToTextConfig = ImageToTextConfig()
    speech_to_text: SpeechToTextConfig = SpeechToTextConfig()
    text_to_speech: TextToSpeechConfig = TextToSpeechConfig()


# 全局配置实例
multimodal_config = MultimodalConfig()