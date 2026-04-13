import time
from typing import List, Dict, Optional, Any
from src.config.config import settings

# 尝试导入httpx
try:
    import httpx
    has_httpx = True
except ImportError:
    has_httpx = False
    print("警告: 无法导入httpx模块，将使用urllib作为备选")


class ModelEngine:
    def __init__(self):
        self.models = {}
        self.token_usage = {}
        self.initialize_models()
    
    def initialize_models(self):
        """初始化模型"""
        try:
            # 强制使用本地API模式
            settings.model_type = "local_api"
            print("使用本地API模式")
            
            # 本地API模式
            if has_httpx:
                self.models["local_api"] = {
                    "client": httpx.Client(base_url=settings.local_api_url, timeout=600.0)
                }
                print(f"本地API模型初始化成功，URL: {settings.local_api_url}，超时时间: 600秒")
            else:
                # 使用urllib作为备选
                self.models["local_api"] = {
                    "client": "urllib"
                }
                print(f"本地API模型初始化成功（使用urllib），URL: {settings.local_api_url}，超时时间: 600秒")
        except Exception as e:
            print(f"模型初始化失败: {e}")
            # 创建一个简单的回退模型
            self.models[settings.model_type] = {
                "client": "urllib"
            }
            print("已创建回退模型")
    
    def generate(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """生成响应"""
        start_time = time.time()
        model_name = request.get("model", settings.model_type)
        messages = request.get("messages", [])
        stream = request.get("stream", False)
        user_id = request.get("user_id", "unknown")
        
        # 调用模型
        try:
            if model_name not in self.models:
                raise ValueError(f"模型 {model_name} 未初始化")
            
            # 只使用本地API模式
            return self._generate_local_api(messages, stream, user_id)
        except Exception as e:
            print(f"模型生成失败: {e}")
            # 降级处理
            return {
                "content": "抱歉，我暂时无法处理您的请求，请稍后再试。",
                "tool_calls": [],
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0
                },
                "finish_reason": "error"
            }
    
    def _generate_local_api(self, messages: List[Dict[str, str]], stream: bool, user_id: str) -> Dict[str, Any]:
        """使用本地API生成响应"""
        import time
        start_time = time.time()
        try:
            model_info = self.models["local_api"]
            client = model_info.get("client")
            
            if not client:
                raise ValueError("本地API客户端未初始化")
            
            # 确保接口路径统一，移除末尾冗余斜杠
            api_path = settings.local_api_url.rstrip('/')
            
            # 读取system prompt
            system_prompt = self._get_system_prompt()
            
            # 构建完整的messages，添加system prompt
            full_messages = [
                {
                    "role": "system",
                    "content": system_prompt
                }
            ] + messages
            
            # 构建API请求
            api_request = {
                "model": "qwen2.5-7b-instruct",
                "messages": full_messages,
                "stream": stream,
                "temperature": 0.7,
                "top_p": 0.95,
                "max_tokens": 1024
            }
            
            # 记录请求日志
            print(f"[大模型调用] 用户: {user_id}, 消息数: {len(messages)}, 接口: {api_path}")
            
            # 发送请求
            if has_httpx and isinstance(client, httpx.Client):
                # 使用httpx发送请求
                print(f"[大模型调用] 开始发送HTTP请求...")
                response = client.post("", json=api_request, follow_redirects=True)
                response.raise_for_status()
                api_response = response.json()
            else:
                # 使用urllib发送请求
                import urllib.request
                import json
                url = api_path
                data = json.dumps(api_request).encode('utf-8')
                headers = {'Content-Type': 'application/json'}
                req = urllib.request.Request(url, data=data, headers=headers)
                print(f"[大模型调用] 开始发送HTTP请求...")
                with urllib.request.urlopen(req, timeout=120) as response:
                    api_response = json.loads(response.read().decode('utf-8'))
            
            # 记录响应日志
            prompt_tokens = api_response.get("usage", {}).get("prompt_tokens", 0)
            completion_tokens = api_response.get("usage", {}).get("completion_tokens", 0)
            print(f"[大模型调用] 请求完成，耗时: {(time.time() - start_time):.2f}秒, "
                  f"输入tokens: {prompt_tokens}, 输出tokens: {completion_tokens}")
            
            # 提取内容
            content = ""
            if "choices" in api_response and len(api_response["choices"]) > 0:
                choice = api_response["choices"][0]
                if "message" in choice and "content" in choice["message"]:
                    content = choice["message"]["content"]
            
            # 提取token使用情况
            usage = api_response.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            
            # 记录token使用情况
            self._record_token_usage(user_id, prompt_tokens, completion_tokens)
            
            return {
                "content": content,
                "tool_calls": [],
                "usage": usage,
                "finish_reason": api_response.get("finish_reason", "stop")
            }
        except Exception as e:
            print(f"本地API调用失败: {e}")
            # 降级处理
            return {
                "content": "抱歉，我暂时无法处理您的请求，请稍后再试。",
                "tool_calls": [],
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0
                },
                "finish_reason": "error"
            }
    
    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        try:
            with open("src/prompt/system_prompt.txt", "r", encoding="utf-8") as f:
                system_prompt = f.read().strip()
        except Exception:
            system_prompt = "你是一个全能的智能体动漫角色，具有丰富的知识和强大的能力。"
        return system_prompt
    
    def _record_token_usage(self, user_id: str, prompt_tokens: int, completion_tokens: int):
        """记录token使用情况"""
        if user_id not in self.token_usage:
            self.token_usage[user_id] = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "last_used": time.time()
            }
        
        self.token_usage[user_id]["prompt_tokens"] += prompt_tokens
        self.token_usage[user_id]["completion_tokens"] += completion_tokens
        self.token_usage[user_id]["total_tokens"] += prompt_tokens + completion_tokens
        self.token_usage[user_id]["last_used"] = time.time()
    
    def get_token_usage(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户的token使用情况"""
        return self.token_usage.get(user_id)


# 全局模型引擎实例
model_engine = ModelEngine()