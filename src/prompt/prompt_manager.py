"""提示词管理器 - 统一管理所有提示词文件"""
from typing import Dict, Optional
import os

class PromptManager:
    """提示词管理器"""
    
    def __init__(self):
        self.prompts: Dict[str, str] = {}
        self.prompt_dir = os.path.dirname(os.path.abspath(__file__))
        self._load_all_prompts()
    
    def _load_all_prompts(self):
        """加载所有提示词文件"""
        prompt_files = {
            "system": "system_prompt.txt",
            "cot": "CoT_prompt.txt",
            "plan": "plan_prompt.txt",
            "react": "react_prompt.txt",
            "rag": "rag_prompt.txt",
            "chat": "chat_prompt.txt",
            "weather": "weather_prompt.txt",
            "tool_result": "tool_result_prompt.txt",
            "context_compressor": "context_compressor_prompt.txt",
            "medical_system": "medical_system_prompt.txt"
        }
        
        for name, filename in prompt_files.items():
            filepath = os.path.join(self.prompt_dir, filename)
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        self.prompts[name] = f.read()
                    print(f"✓ 加载提示词: {name}")
                except Exception as e:
                    print(f"✗ 加载提示词失败 {name}: {e}")
            else:
                print(f"⚠ 提示词文件不存在: {filename}")
    
    def get_prompt(self, name: str) -> Optional[str]:
        """获取提示词内容"""
        return self.prompts.get(name)
    
    def format_prompt(self, name: str, **kwargs) -> Optional[str]:
        """获取格式化后的提示词"""
        prompt = self.get_prompt(name)
        if prompt:
            return prompt.format(**kwargs)
        return None
    
    def reload(self):
        """重新加载所有提示词"""
        self.prompts.clear()
        self._load_all_prompts()


# 全局提示词管理器实例
prompt_manager = PromptManager()