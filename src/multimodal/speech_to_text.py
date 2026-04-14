"""语音转文本模块 - 使用阿里大模型API"""
import requests
import json
import base64
from typing import Optional, Dict, Any


class SpeechToText:
    """语音转文本处理器 - 阿里大模型ASR"""
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://dashscope.aliyuncs.com/api/text/speech/asr"
        self.token = None
        self.token_expire_time = 0
    
    def _get_token(self):
        """获取阿里大模型访问token"""
        import time
        if self.token and time.time() < self.token_expire_time:
            return self.token
        
        url = "https://dashscope.aliyuncs.com/api/text/auth/token"
        headers = {
            "Content-Type": "application/json"
        }
        payload = {
            "api_key": self.api_key,
            "api_secret": self.api_secret
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            
            if result.get("status") == "success":
                self.token = result.get("access_token")
                self.token_expire_time = time.time() + int(result.get("expires_in", 3600))
                return self.token
            else:
                print(f"获取Token失败: {result.get('message')}")
        except Exception as e:
            print(f"获取Token异常: {e}")
        
        return None
    
    def process(self, audio_input: str, input_type: str = "file", format: str = "wav") -> str:
        """
        处理语音转文本 - 使用阿里大模型ASR
        
        Args:
            audio_input: 音频文件路径、URL或base64数据
            input_type: "file" | "url" | "base64"
            format: 音频格式，支持wav, mp3, m4a等
        
        Returns:
            转写后的文本
        """
        if not self.api_key or not self.api_secret:
            return "错误：请配置阿里大模型API密钥"
        
        token = self._get_token()
        if not token:
            return "错误：无法获取访问令牌"
        
        # 处理音频数据
        if input_type == "file":
            with open(audio_input, "rb") as f:
                audio_data = base64.b64encode(f.read()).decode("utf-8")
        elif input_type == "url":
            audio_data = audio_input
        else:
            audio_data = audio_input
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "paraformer-realtime-v1",
            "input": {
                "audio": audio_data,
                "audio_type": input_type,
                "format": format
            },
            "parameters": {
                "language": "zh",
                "enable_punctuation": True
            }
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            
            if result.get("status") == "success":
                return result.get("output", {}).get("text", "")
            else:
                error_msg = result.get("message", "语音识别失败")
                return f"语音识别失败: {error_msg}"
        
        except Exception as e:
            print(f"语音识别异常: {e}")
            return f"语音识别异常: {str(e)}"


# 全局实例
speech_to_text = SpeechToText()