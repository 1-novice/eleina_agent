from typing import Dict, List, Optional, Any
from src.memory.memory_store import MemoryStore


class MemoryWriter:
    def __init__(self, store: MemoryStore):
        self.store = store
    
    def write_memory(self, memory: Dict[str, Any]) -> bool:
        """写入记忆
        
        Args:
            memory: 记忆数据
            
        Returns:
            bool: 是否写入成功
        """
        try:
            memory_type = memory.get("memory_type")
            
            if memory_type == "dialog":
                # 写入对话历史
                session_id = memory.get("session_id")
                if session_id:
                    message = {
                        "role": memory.get("role", "user"),
                        "content": memory.get("content", ""),
                        "timestamp": memory.get("create_time")
                    }
                    return self.store.write_dialog_history(session_id, message)
            elif memory_type == "task":
                # 写入任务记忆
                session_id = memory.get("session_id")
                if session_id:
                    task_data = {
                        "task": memory.get("content", ""),
                        "progress": memory.get("progress", "0%"),
                        "steps": memory.get("steps", []),
                        "created_at": memory.get("create_time")
                    }
                    return self.store.write_session_memory(session_id, task_data)
            else:
                # 写入用户记忆
                return self.store.write_user_memory(memory)
        except Exception as e:
            print(f"写入记忆失败: {e}")
            return False
    
    def extract_and_write_memory(self, user_id: str, session_id: str, text: str, source: str = "dialog") -> bool:
        """从文本中提取记忆并写入
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            text: 文本内容
            source: 来源
            
        Returns:
            bool: 是否提取并写入成功
        """
        try:
            # 提取用户档案信息
            profile_memories = self._extract_user_profile(text)
            for memory in profile_memories:
                memory["user_id"] = user_id
                memory["source"] = source
                memory["create_time"] = memory.get("create_time", "")
                memory["expire_time"] = None  # 永久记忆
                self.write_memory(memory)
            
            # 提取任务信息
            task_memory = self._extract_task_info(text)
            if task_memory:
                task_memory["user_id"] = user_id
                task_memory["session_id"] = session_id
                task_memory["source"] = source
                task_memory["create_time"] = task_memory.get("create_time", "")
                task_memory["expire_time"] = None
                self.write_memory(task_memory)
            
            # 提取对话历史
            dialog_memory = {
                "user_id": user_id,
                "session_id": session_id,
                "memory_type": "dialog",
                "role": "user",
                "content": text,
                "source": source,
                "create_time": task_memory.get("create_time", "") if task_memory else "",
                "expire_time": None
            }
            self.write_memory(dialog_memory)
            
            return True
        except Exception as e:
            print(f"提取并写入记忆失败: {e}")
            return False
    
    def _extract_user_profile(self, text: str) -> List[Dict[str, Any]]:
        """从文本中提取用户档案信息
        
        Args:
            text: 文本内容
            
        Returns:
            List[Dict[str, Any]]: 提取的用户档案记忆
        """
        import re
        memories = []
        
        # 提取姓名
        name_patterns = [
            r"我叫([\u4e00-\u9fa5a-zA-Z]+)",
            r"我的名字是([\u4e00-\u9fa5a-zA-Z]+)",
            r"我是([\u4e00-\u9fa5a-zA-Z]+)"
        ]
        for pattern in name_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                memories.append({
                    "memory_type": "preference",
                    "content": f"姓名: {match}"
                })
        
        # 提取偏好
        preference_patterns = [
            r"我喜欢([^，。！？]+)",
            r"我不喜欢([^，。！？]+)",
            r"我偏好([^，。！？]+)",
            r"我讨厌([^，。！？]+)"
        ]
        for pattern in preference_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if "喜欢" in pattern or "偏好" in pattern:
                    memories.append({
                        "memory_type": "preference",
                        "content": f"喜欢: {match}"
                    })
                else:
                    memories.append({
                        "memory_type": "preference",
                        "content": f"不喜欢: {match}"
                    })
        
        # 提取职业
        job_patterns = [
            r"我是([^，。！？]+)的",
            r"我在([^，。！？]+)工作",
            r"我的职业是([^，。！？]+)"
        ]
        for pattern in job_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                memories.append({
                    "memory_type": "preference",
                    "content": f"职业: {match}"
                })
        
        return memories
    
    def _extract_task_info(self, text: str) -> Optional[Dict[str, Any]]:
        """从文本中提取任务信息
        
        Args:
            text: 文本内容
            
        Returns:
            Optional[Dict[str, Any]]: 提取的任务记忆
        """
        import re
        
        # 提取任务
        task_patterns = [
            r"帮我(.*?)(?:，|。|！|？|$)",
            r"请(.*?)(?:，|。|！|？|$)",
            r"我想(.*?)(?:，|。|！|？|$)"
        ]
        
        for pattern in task_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if match.strip():
                    return {
                        "memory_type": "task",
                        "content": match.strip(),
                        "progress": "0%",
                        "steps": []
                    }
        
        return None
    
    def write_dialog_memory(self, session_id: str, role: str, content: str) -> bool:
        """写入对话记忆
        
        Args:
            session_id: 会话ID
            role: 角色 (user/assistant)
            content: 内容
            
        Returns:
            bool: 是否写入成功
        """
        import time
        memory = {
            "session_id": session_id,
            "memory_type": "dialog",
            "role": role,
            "content": content,
            "source": "dialog",
            "create_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "expire_time": None
        }
        return self.write_memory(memory)
    
    def write_task_memory(self, session_id: str, task: str, progress: str = "0%", steps: List[str] = None) -> bool:
        """写入任务记忆
        
        Args:
            session_id: 会话ID
            task: 任务内容
            progress: 进度
            steps: 步骤列表
            
        Returns:
            bool: 是否写入成功
        """
        import time
        if steps is None:
            steps = []
        
        memory = {
            "session_id": session_id,
            "memory_type": "task",
            "content": task,
            "progress": progress,
            "steps": steps,
            "source": "task",
            "create_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "expire_time": None
        }
        return self.write_memory(memory)