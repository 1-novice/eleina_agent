from typing import Dict, List, Optional, Any
import time
from src.memory.memory_store import MemoryStore
from src.memory.memory_writer import MemoryWriter
from src.memory.memory_retriever import MemoryRetriever


class MemoryManager:
    def __init__(self):
        self.store = MemoryStore()
        self.writer = MemoryWriter(self.store)
        self.retriever = MemoryRetriever(self.store)
        
    def add_memory(self, user_id: str, memory_type: str, content: str, source: str = "dialog", expire_time: Optional[str] = None) -> bool:
        """写入记忆
        
        Args:
            user_id: 用户ID
            memory_type: 记忆类型 (preference, knowledge, task, etc.)
            content: 记忆内容
            source: 记忆来源 (dialog, tool, etc.)
            expire_time: 过期时间 (ISO格式字符串)
            
        Returns:
            bool: 是否写入成功
        """
        try:
            memory = {
                "user_id": user_id,
                "memory_type": memory_type,
                "content": content,
                "source": source,
                "create_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "expire_time": expire_time
            }
            return self.writer.write_memory(memory)
        except Exception as e:
            print(f"写入记忆失败: {e}")
            return False
    
    def get_memory(self, user_id: str, memory_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """读取记忆
        
        Args:
            user_id: 用户ID
            memory_type: 记忆类型 (可选)
            
        Returns:
            List[Dict[str, Any]]: 记忆列表
        """
        try:
            return self.retriever.get_memory(user_id, memory_type)
        except Exception as e:
            print(f"读取记忆失败: {e}")
            return []
    
    def search_memory(self, user_id: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """语义检索记忆
        
        Args:
            user_id: 用户ID
            query: 检索查询
            top_k: 返回结果数量
            
        Returns:
            List[Dict[str, Any]]: 相关记忆列表
        """
        try:
            return self.retriever.search_memory(user_id, query, top_k)
        except Exception as e:
            print(f"检索记忆失败: {e}")
            return []
    
    def clear_memory(self, user_id: str, session_id: Optional[str] = None, memory_type: Optional[str] = None) -> bool:
        """清理记忆
        
        Args:
            user_id: 用户ID
            session_id: 会话ID (可选，清理会话记忆)
            memory_type: 记忆类型 (可选)
            
        Returns:
            bool: 是否清理成功
        """
        try:
            return self.store.clear_memory(user_id, session_id, memory_type)
        except Exception as e:
            print(f"清理记忆失败: {e}")
            return False
    
    def get_context_memory(self, user_id: str, session_id: str, max_turns: int = 5) -> str:
        """获取上下文记忆，用于拼入Prompt
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            max_turns: 最大轮数
            
        Returns:
            str: 格式化的上下文记忆
        """
        try:
            # 获取用户档案
            user_profile = self.retriever.get_user_profile(user_id)
            
            # 获取当前任务
            current_task = self.retriever.get_current_task(session_id)
            
            # 获取历史对话
            history = self.retriever.get_dialog_history(session_id, max_turns)
            
            # 格式化记忆
            context = """
【用户档案】
"""
            
            if user_profile:
                for item in user_profile:
                    context += f"{item['key']}: {item['value']}\n"
            
            context += "\n【当前任务】\n"
            if current_task:
                context += f"{current_task.get('task', '无')}\n"
                context += f"进度: {current_task.get('progress', '0%')}\n"
            else:
                context += "无\n"
            
            context += "\n【历史对话】\n"
            if history:
                for item in history:
                    role = item.get('role', 'user')
                    content = item.get('content', '')
                    if role == 'user':
                        context += f"用户: {content}\n"
                    elif role == 'assistant':
                        context += f"助手: {content}\n"
            else:
                context += "无\n"
            
            return context
        except Exception as e:
            print(f"获取上下文记忆失败: {e}")
            return ""
    
    def update_session_memory(self, session_id: str, key: str, value: Any) -> bool:
        """更新会话记忆
        
        Args:
            session_id: 会话ID
            key: 键
            value: 值
            
        Returns:
            bool: 是否更新成功
        """
        try:
            return self.store.update_session_memory(session_id, key, value)
        except Exception as e:
            print(f"更新会话记忆失败: {e}")
            return False


# 全局记忆管理器实例
memory_manager = MemoryManager()