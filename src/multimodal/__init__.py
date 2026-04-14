"""多模态接入模块 - 支持图像、语音输入输出"""

from .image_to_text import ImageToText, image_to_text
from .speech_to_text import SpeechToText, speech_to_text
from .text_to_speech import TextToSpeech, text_to_speech
from .multimodal_processor import MultimodalProcessor
from .config import MultimodalConfig, multimodal_config

__all__ = [
    "ImageToText",
    "image_to_text",
    "SpeechToText",
    "speech_to_text",
    "TextToSpeech",
    "text_to_speech",
    "MultimodalProcessor",
    "MultimodalConfig",
    "multimodal_config"
]