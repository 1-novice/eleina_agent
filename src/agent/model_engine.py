import time
from typing import List, Dict, Optional, Any, Generator
from src.config.config import settings

# 尝试导入httpx
try:
    import httpx
    has_httpx = True
except ImportError:
    has_httpx = False
    print("警告: 无法导入httpx模块，将使用urllib作为备选")

# 尝试导入torch和transformers
torch = None
try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    has_transformers = True
except ImportError:
    has_transformers = False
    print("警告: 无法导入torch或transformers模块，将使用本地API模式")


class ModelEngine:
    def __init__(self):
        self.models = {}
        self.token_usage = {}
        self.initialize_models()
    
    def initialize_models(self):
        """初始化模型"""
        try:
            # 检查是否有transformers
            if not has_transformers:
                # 强制使用本地API模式
                settings.model_type = "local_api"
                print("由于缺少依赖，强制使用本地API模式")
            
            if settings.model_type == "local_api":
                # 本地API模式
                if has_httpx:
                    self.models["local_api"] = {
                        "client": httpx.Client(base_url=settings.local_api_url, timeout=60.0)
                    }
                    print(f"本地API模型初始化成功，URL: {settings.local_api_url}")
                else:
                    # 使用urllib作为备选
                    self.models["local_api"] = {
                        "client": "urllib"
                    }
                    print(f"本地API模型初始化成功（使用urllib），URL: {settings.local_api_url}")
            else:
                # 本地模型模式
                if not has_transformers:
                    raise ImportError("缺少transformers依赖")
                
                # 检查CUDA是否可用
                cuda_available = torch.cuda.is_available() if torch else False
                print(f"CUDA可用: {cuda_available}")
                
                # 加载本地模型
                tokenizer = AutoTokenizer.from_pretrained(settings.local_model_path)
                
                if cuda_available and torch:
                    # 4bit量化配置
                    try:
                        quantization_config = BitsAndBytesConfig(
                            load_in_4bit=True,
                            bnb_4bit_quant_type="nf4",
                            bnb_4bit_compute_dtype=torch.float16,
                            bnb_4bit_use_double_quant=True
                        )
                        model = AutoModelForCausalLM.from_pretrained(
                            settings.local_model_path,
                            quantization_config=quantization_config,
                            device_map="auto"
                        )
                        print("使用4bit量化模型")
                    except Exception as e:
                        print(f"4bit量化失败: {e}，使用CPU模式")
                        model = AutoModelForCausalLM.from_pretrained(
                            settings.local_model_path,
                            device_map="cpu"
                        )
                else:
                    # CPU模式
                    model = AutoModelForCausalLM.from_pretrained(
                        settings.local_model_path,
                        device_map="cpu"
                    )
                    print("使用CPU模式模型")
                
                # 加载LoRA微调权重
                if settings.lora_path:
                    try:
                        from peft import PeftModel
                        model = PeftModel.from_pretrained(model, settings.lora_path)
                        print("LoRA权重加载成功")
                    except Exception as e:
                        print(f"LoRA权重加载失败: {e}")
                
                self.models["local"] = {
                    "model": model,
                    "tokenizer": tokenizer
                }
                print("本地模型初始化成功")
        except Exception as e:
            print(f"模型初始化失败: {e}")
            # 创建一个简单的回退模型
            self.models[settings.model_type] = {
                "model": None,
                "tokenizer": None
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
            
            if model_name == "local_api":
                # 本地API模式
                return self._generate_local_api(messages, stream, user_id)
            else:
                # 本地模型模式
                model_info = self.models[model_name]
                model = model_info["model"]
                tokenizer = model_info["tokenizer"]
                
                # 检查模型是否初始化成功
                if model is None or tokenizer is None:
                    raise ValueError("模型未初始化成功")
                
                # 构建prompt
                prompt = self._build_prompt(messages)
                
                # 编码输入
                inputs = tokenizer(prompt, return_tensors="pt")
                # 检查设备
                device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
                inputs = {k: v.to(device) for k, v in inputs.items()}
                prompt_tokens = inputs.input_ids.shape[1]
                
                # 生成响应
                if stream:
                    return self._stream_generate(model, tokenizer, inputs, prompt_tokens, user_id)
                else:
                    output = model.generate(
                        **inputs,
                        max_new_tokens=1024,
                        temperature=0.7,
                        do_sample=True,
                        top_p=0.95
                    )
                    
                    # 解码响应
                    response = tokenizer.decode(output[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
                    completion_tokens = output.shape[1] - inputs.input_ids.shape[1]
                    
                    # 记录token使用情况
                    self._record_token_usage(user_id, prompt_tokens, completion_tokens)
                    
                    return {
                        "content": response,
                        "tool_calls": [],
                        "usage": {
                            "prompt_tokens": prompt_tokens,
                            "completion_tokens": completion_tokens
                        },
                        "finish_reason": "stop"
                    }
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
        try:
            model_info = self.models["local_api"]
            client = model_info.get("client")
            
            if not client:
                raise ValueError("本地API客户端未初始化")
            
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
            
            # 发送请求
            if has_httpx and isinstance(client, httpx.Client):
                # 使用httpx发送请求
                response = client.post("", json=api_request, follow_redirects=True)
                response.raise_for_status()
                api_response = response.json()
            else:
                # 使用urllib发送请求
                import urllib.request
                import json
                url = settings.local_api_url
                data = json.dumps(api_request).encode('utf-8')
                headers = {'Content-Type': 'application/json'}
                req = urllib.request.Request(url, data=data, headers=headers)
                with urllib.request.urlopen(req, timeout=60) as response:
                    api_response = json.loads(response.read().decode('utf-8'))
            
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
    
    def _stream_generate(self, model, tokenizer, inputs, prompt_tokens, user_id) -> Generator[Dict[str, Any], None, None]:
        """流式生成响应"""
        completion_tokens = 0
        generated_text = ""
        
        for output in model.generate(
            **inputs,
            max_new_tokens=1024,
            temperature=0.7,
            do_sample=True,
            top_p=0.95,
            streamer=tokenizer,
            stream=True
        ):
            # 解码当前生成的token
            current_token = tokenizer.decode(output[-1:], skip_special_tokens=True)
            generated_text += current_token
            completion_tokens += 1
            
            yield {
                "content": current_token,
                "tool_calls": [],
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens
                },
                "finish_reason": None
            }
        
        # 记录token使用情况
        self._record_token_usage(user_id, prompt_tokens, completion_tokens)
        
        yield {
            "content": "",
            "tool_calls": [],
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens
            },
            "finish_reason": "stop"
        }
    
    def _build_prompt(self, messages: List[Dict[str, str]]) -> str:
        """构建模型输入prompt"""
        # 读取系统提示词
        try:
            with open("src/prompt/system_prompt.txt", "r", encoding="utf-8") as f:
                system_prompt = f.read().strip()
        except Exception:
            system_prompt = "你是一个全能的智能体动漫角色，具有丰富的知识和强大的能力。"
        
        prompt = f"[SYSTEM]\n{system_prompt}\n"
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                prompt += f"[USER]\n{content}\n"
            elif role == "assistant":
                prompt += f"[ASSISTANT]\n{content}\n"
        
        prompt += "[ASSISTANT]\n"
        return prompt
    
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