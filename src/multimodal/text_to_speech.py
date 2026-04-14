"""文本转语音模块 - 使用阿里大模型API"""
import requests
import json
from typing import Optional, Dict, Any


class TextToSpeech:
    """文本转语音处理器 - 阿里大模型TTS"""
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://dashscope.aliyuncs.com/api/text/speech/tts"
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
    
    def process(self, text: str, voice: str = "female", rate: int = 0, volume: int = 50, output_format: str = "mp3") -> bytes:
        """
        处理文本转语音 - 使用阿里大模型TTS
        
        Args:
            text: 要转换的文本
            voice: 音色，支持 female/male/child
            rate: 语速，-500~500，0为正常
            volume: 音量，0~100
            output_format: 输出格式，支持mp3/wav
        
        Returns:
            音频数据（bytes）
        """
        if not self.api_key or not self.api_secret:
            print("错误：请配置阿里大模型API密钥")
            return b""
        
        token = self._get_token()
        if not token:
            print("错误：无法获取访问令牌")
            return b""
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # 映射音色参数
        voice_map = {
            "female": "zh-CN-XiaoyunNeural",
            "male": "zh-CN-YunfengNeural",
            "child": "zh-CN-XiaoxiaoNeural"
        }
        
        payload = {
            "model": "speech-synthesis-v1",
            "input": {
                "text": text
            },
            "parameters": {
                "voice": voice_map.get(voice, "zh-CN-XiaoyunNeural"),
                "rate": rate,
                "volume": volume,
                "format": output_format
            }
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=payload)
            response.raise_for_status()
            
            # 检查响应内容类型
            content_type = response.headers.get("Content-Type", "")
            if "audio" in content_type or "octet-stream" in content_type:
                return response.content
            else:
                # 可能是JSON错误响应
                try:
                    result = response.json()
                    if result.get("status") != "success":
                        print(f"语音合成失败: {result.get('message')}")
                except:
                    pass
                return b""
        
        except Exception as e:
            print(f"语音合成异常: {e}")
            return b""
    
    def save_to_file(self, text: str, file_path: str, **kwargs):
        """将语音保存到文件"""
        audio_data = self.process(text, **kwargs)
        if audio_data:
            with open(file_path, "wb") as f:
                f.write(audio_data)
            return True
        return False


# 全局实例
text_to_speech = TextToSpeech()