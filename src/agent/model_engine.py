import time
import json
from typing import List, Dict, Optional, Any, Generator
from src.config.config import settings

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
            settings.model_type = "local_api"
            print("使用本地API模式")
            
            if has_httpx:
                self.models["local_api"] = {
                    "client": httpx.Client(base_url=settings.local_api_url, timeout=600.0)
                }
                print(f"本地API模型初始化成功，URL: {settings.local_api_url}，超时时间: 600秒")
            else:
                self.models["local_api"] = {
                    "client": "urllib"
                }
                print(f"本地API模型初始化成功（使用urllib），URL: {settings.local_api_url}，超时时间: 600秒")
        except Exception as e:
            print(f"模型初始化失败: {e}")
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
        
        try:
            if model_name not in self.models:
                raise ValueError(f"模型 {model_name} 未初始化")
            
            if stream:
                return self._generate_local_api_stream(messages, user_id)
            else:
                return self._generate_local_api(messages, stream, user_id)
        except Exception as e:
            print(f"模型生成失败: {e}")
            return {
                "content": "抱歉，我暂时无法处理您的请求，请稍后再试。",
                "tool_calls": [],
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0
                },
                "finish_reason": "error"
            }
    
    def generate_stream(self, request: Dict[str, Any]) -> Generator[str, None, None]:
        """流式生成响应"""
        model_name = request.get("model", settings.model_type)
        messages = request.get("messages", [])
        user_id = request.get("user_id", "unknown")
        
        try:
            if model_name not in self.models:
                raise ValueError(f"模型 {model_name} 未初始化")
            
            yield from self._stream_local_api(messages, user_id)
        except Exception as e:
            print(f"流式生成失败: {e}")
            yield "抱歉，我暂时无法处理您的请求，请稍后再试。"
    
    def _generate_local_api(self, messages: List[Dict[str, str]], stream: bool, user_id: str) -> Dict[str, Any]:
        """使用本地API生成响应"""
        import time
        start_time = time.time()
        try:
            model_info = self.models["local_api"]
            client = model_info.get("client")
            
            if not client:
                raise ValueError("本地API客户端未初始化")
            
            api_path = settings.local_api_url.rstrip('/')
            system_prompt = self._get_system_prompt()
            
            full_messages = [
                {
                    "role": "system",
                    "content": system_prompt
                }
            ] + messages
            
            api_request = {
                "model": "qwen2.5-7b-instruct",
                "messages": full_messages,
                "stream": stream,
                "temperature": 0.7,
                "top_p": 0.95,
                "max_tokens": 1024
            }
            
            print(f"[大模型调用] 用户: {user_id}, 消息数: {len(messages)}, 接口: {api_path}")
            
            if has_httpx and isinstance(client, httpx.Client):
                print(f"[大模型调用] 开始发送HTTP请求...")
                response = client.post("", json=api_request, follow_redirects=True)
                response.raise_for_status()
                api_response = response.json()
            else:
                import urllib.request
                url = api_path
                data = json.dumps(api_request).encode('utf-8')
                headers = {'Content-Type': 'application/json'}
                req = urllib.request.Request(url, data=data, headers=headers)
                print(f"[大模型调用] 开始发送HTTP请求...")
                with urllib.request.urlopen(req, timeout=120) as response:
                    api_response = json.loads(response.read().decode('utf-8'))
            
            prompt_tokens = api_response.get("usage", {}).get("prompt_tokens", 0)
            completion_tokens = api_response.get("usage", {}).get("completion_tokens", 0)
            print(f"[大模型调用] 请求完成，耗时: {(time.time() - start_time):.2f}秒, "
                  f"输入tokens: {prompt_tokens}, 输出tokens: {completion_tokens}")
            
            content = ""
            if "choices" in api_response and len(api_response["choices"]) > 0:
                choice = api_response["choices"][0]
                if "message" in choice and "content" in choice["message"]:
                    content = choice["message"]["content"]
            
            usage = api_response.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            
            self._record_token_usage(user_id, prompt_tokens, completion_tokens)
            
            return {
                "content": content,
                "tool_calls": [],
                "usage": usage,
                "finish_reason": api_response.get("finish_reason", "stop")
            }
        except Exception as e:
            print(f"本地API调用失败: {e}")
            return {
                "content": "抱歉，我暂时无法处理您的请求，请稍后再试。",
                "tool_calls": [],
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0
                },
                "finish_reason": "error"
            }
    
    def _generate_local_api_stream(self, messages: List[Dict[str, str]], user_id: str) -> Dict[str, Any]:
        """使用本地API流式生成响应"""
        try:
            model_info = self.models["local_api"]
            client = model_info.get("client")
            
            if not client or not has_httpx:
                raise ValueError("流式输出需要httpx客户端")
            
            api_path = settings.local_api_url.rstrip('/')
            system_prompt = self._get_system_prompt()
            
            full_messages = [
                {
                    "role": "system",
                    "content": system_prompt
                }
            ] + messages
            
            api_request = {
                "model": "qwen2.5-7b-instruct",
                "messages": full_messages,
                "stream": True,
                "temperature": 0.7,
                "top_p": 0.95,
                "max_tokens": 1024
            }
            
            print(f"[大模型调用] 流式输出 - 用户: {user_id}, 消息数: {len(messages)}")
            
            def stream_generator():
                with client.stream("POST", "", json=api_request, follow_redirects=True) as response:
                    response.raise_for_status()
                    buffer = ""
                    for chunk in response.iter_text(chunk_size=1024):
                        buffer += chunk
                        while "data: " in buffer:
                            idx = buffer.find("data: ")
                            end_idx = buffer.find("\n\n", idx)
                            if end_idx == -1:
                                break
                            json_str = buffer[idx + 6:end_idx].strip()
                            buffer = buffer[end_idx + 2:]
                            if json_str == "[DONE]":
                                return
                            try:
                                data = json.loads(json_str)
                                if data.get("choices"):
                                    delta = data["choices"][0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        yield content
                            except json.JSONDecodeError:
                                continue
            
            return {
                "content": stream_generator(),
                "tool_calls": [],
                "usage": {},
                "finish_reason": "stop",
                "stream": True
            }
        except Exception as e:
            print(f"本地API流式调用失败: {e}")
            return {
                "content": "抱歉，我暂时无法处理您的请求，请稍后再试。",
                "tool_calls": [],
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0
                },
                "finish_reason": "error",
                "stream": False
            }
    
    def _stream_local_api(self, messages: List[Dict[str, str]], user_id: str) -> Generator[str, None, None]:
        """使用本地API流式生成响应（直接返回生成器）"""
        try:
            model_info = self.models["local_api"]
            client = model_info.get("client")
            
            if not client or not has_httpx:
                raise ValueError("流式输出需要httpx客户端")
            
            api_path = settings.local_api_url.rstrip('/')
            system_prompt = self._get_system_prompt()
            
            full_messages = [
                {
                    "role": "system",
                    "content": system_prompt
                }
            ] + messages
            
            api_request = {
                "model": "qwen2.5-7b-instruct",
                "messages": full_messages,
                "stream": True,
                "temperature": 0.7,
                "top_p": 0.95,
                "max_tokens": 1024
            }
            
            print(f"[大模型调用] 流式输出 - 用户: {user_id}, 消息数: {len(messages)}")
            
            with client.stream("POST", "", json=api_request, follow_redirects=True) as response:
                response.raise_for_status()
                buffer = ""
                for chunk in response.iter_text(chunk_size=1024):
                    buffer += chunk
                    while "data: " in buffer:
                        idx = buffer.find("data: ")
                        end_idx = buffer.find("\n\n", idx)
                        if end_idx == -1:
                            break
                        json_str = buffer[idx + 6:end_idx].strip()
                        buffer = buffer[end_idx + 2:]
                        if json_str == "[DONE]":
                            return
                        try:
                            data = json.loads(json_str)
                            if data.get("choices"):
                                delta = data["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            print(f"本地API流式调用失败: {e}")
            yield "抱歉，我暂时无法处理您的请求，请稍后再试。"
    
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


model_engine = ModelEngine()