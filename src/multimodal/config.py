"""多模态模块配置 - 仅保留图像转文本配置"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class ImageToTextConfig(BaseSettings):
    """图像转文本配置"""
    api_key: Optional[str] = None
    model: str = "qwen-vlr"
    enabled: bool = False
    
    model_config = SettingsConfigDict(env_prefix="image_to_text_")


class MultimodalConfig(BaseSettings):
    """多模态配置 - 仅包含图像处理"""
    enabled: bool = False
    image_to_text: ImageToTextConfig = ImageToTextConfig()


multimodal_config = MultimodalConfig()