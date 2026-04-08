from typing import Dict, List, Optional, Any
from src.memory.memory_store import MemoryStore


class MemoryRetriever:
    def __init__(self, store: MemoryStore):
        self.store = store
    
    def get_memory(self, user_id: str, memory_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取记忆
        
        Args:
            user_id: 用户ID
            memory_type: 记忆类型 (可选)
            
        Returns:
            List[Dict[str, Any]]: 记忆列表
        """
        try:
            return self.store.get_user_memory(user_id, memory_type)
        except Exception as e:
            print(f"获取记忆失败: {e}")
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
            # 获取用户的所有记忆
            all_memories = self.store.get_user_memory(user_id)
            
            # 简单的基于关键词的匹配
            # 实际项目中可以使用向量相似度计算
            relevant_memories = []
            for memory in all_memories:
                content = memory.get("content", "")
                # 计算关键词匹配度
                score = self._calculate_relevance(query, content)
                if score > 0:
                    memory["score"] = score
                    relevant_memories.append(memory)
            
            # 按相关性排序
            relevant_memories.sort(key=lambda x: x.get("score", 0), reverse=True)
            
            # 返回前top_k个结果
            return relevant_memories[:top_k]
        except Exception as e:
            print(f"检索记忆失败: {e}")
            return []
    
    def get_user_profile(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户档案
        
        Args:
            user_id: 用户ID
            
        Returns:
            List[Dict[str, Any]]: 用户档案记忆
        """
        try:
            # 获取用户偏好记忆
            preferences = self.store.get_user_memory(user_id, "preference")
            
            # 格式化用户档案
            profile = []
            for memory in preferences:
                content = memory.get("content", "")
                # 尝试解析内容为键值对
                if ":" in content:
                    key, value = content.split(":", 1)
                    profile.append({
                        "key": key.strip(),
                        "value": value.strip()
                    })
            
            return profile
        except Exception as e:
            print(f"获取用户档案失败: {e}")
            return []
    
    def get_current_task(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取当前任务
        
        Args:
            session_id: 会话ID
            
        Returns:
            Optional[Dict[str, Any]]: 当前任务
        """
        try:
            session_memory = self.store.get_session_memory(session_id)
            if session_memory:
                return {
                    "task": session_memory.get("task", ""),
                    "progress": session_memory.get("progress", "0%"),
                    "steps": session_memory.get("steps", []),
                    "created_at": session_memory.get("created_at")
                }
            return None
        except Exception as e:
            print(f"获取当前任务失败: {e}")
            return None
    
    def get_dialog_history(self, session_id: str, max_turns: int = 5) -> List[Dict[str, Any]]:
        """获取对话历史
        
        Args:
            session_id: 会话ID
            max_turns: 最大轮数
            
        Returns:
            List[Dict[str, Any]]: 对话历史
        """
        try:
            return self.store.get_dialog_history(session_id, max_turns)
        except Exception as e:
            print(f"获取对话历史失败: {e}")
            return []
    
    def get_context_for_prompt(self, user_id: str, session_id: str, query: str) -> str:
        """获取用于Prompt的上下文
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            query: 用户查询
            
        Returns:
            str: 格式化的上下文
        """
        try:
            # 获取用户档案
            user_profile = self.get_user_profile(user_id)
            
            # 获取当前任务
            current_task = self.get_current_task(session_id)
            
            # 获取对话历史
            history = self.get_dialog_history(session_id, 5)
            
            # 语义检索相关记忆
            relevant_memories = self.search_memory(user_id, query, 3)
            
            # 格式化上下文
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
            
            context += "\n【相关记忆】\n"
            if relevant_memories:
                for memory in relevant_memories:
                    content = memory.get('content', '')
                    context += f"- {content}\n"
            else:
                context += "无\n"
            
            return context
        except Exception as e:
            print(f"获取上下文失败: {e}")
            return ""
    
    def _calculate_relevance(self, query: str, content: str) -> float:
        """计算查询与内容的相关性
        
        Args:
            query: 查询文本
            content: 内容文本
            
        Returns:
            float: 相关性分数
        """
        import re
        
        # 转换为小写
        query = query.lower()
        content = content.lower()
        
        # 分词
        query_words = set(re.findall(r"\w+", query))
        content_words = set(re.findall(r"\w+", content))
        
        # 计算词重叠
        if not query_words:
            return 0.0
        
        overlap = len(query_words.intersection(content_words))
        return overlap / len(query_words)