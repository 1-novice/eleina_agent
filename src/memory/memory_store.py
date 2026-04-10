from typing import Dict, List, Optional, Any
import json
from src.config.config import settings

# 尝试导入redis
try:
    import redis
    has_redis = True
except ImportError:
    has_redis = False
    print("警告: 无法导入redis模块，将使用本地内存存储")


class MemoryStore:
    def __init__(self):
        # 初始化Redis连接
        self.redis_client = None
        if has_redis:
            try:
                self.redis_client = redis.from_url(settings.redis_url, decode_responses=True)
                self.redis_client.ping()
                print("Redis连接成功")
            except Exception as e:
                print(f"Redis连接失败，使用内存存储: {e}")
                self.redis_client = None
        else:
            print("Redis模块不可用，使用内存存储")
        
        # 内存存储（作为Redis的降级方案）
        self.in_memory_store = {
            "user_memory": {},  # user_id -> {memory_type -> [memories]}
            "session_memory": {},  # session_id -> {key -> value}
            "dialog_history": {}  # session_id -> [messages]
        }
    
    def write_user_memory(self, memory: Dict[str, Any]) -> bool:
        """写入用户记忆
        
        Args:
            memory: 记忆数据
            
        Returns:
            bool: 是否写入成功
        """
        try:
            user_id = memory.get("user_id")
            memory_type = memory.get("memory_type")
            
            if not user_id or not memory_type:
                return False
            
            # 使用Redis存储
            if self.redis_client:
                key = f"user:{user_id}:memory:{memory_type}"
                # 获取现有记忆
                existing_memories = self.redis_client.get(key)
                if existing_memories:
                    memories = json.loads(existing_memories)
                else:
                    memories = []
                
                # 添加新记忆
                memories.append(memory)
                # 去重（简单去重，基于内容）
                unique_memories = self._deduplicate_memories(memories)
                
                # 保存回Redis
                self.redis_client.set(key, json.dumps(unique_memories))
            else:
                # 使用内存存储
                if user_id not in self.in_memory_store["user_memory"]:
                    self.in_memory_store["user_memory"][user_id] = {}
                if memory_type not in self.in_memory_store["user_memory"][user_id]:
                    self.in_memory_store["user_memory"][user_id][memory_type] = []
                
                # 添加新记忆
                self.in_memory_store["user_memory"][user_id][memory_type].append(memory)
                # 去重
                self.in_memory_store["user_memory"][user_id][memory_type] = \
                    self._deduplicate_memories(self.in_memory_store["user_memory"][user_id][memory_type])
            
            return True
        except Exception as e:
            print(f"写入用户记忆失败: {e}")
            return False
    
    def write_session_memory(self, session_id: str, data: Dict[str, Any]) -> bool:
        """写入会话记忆
        
        Args:
            session_id: 会话ID
            data: 会话数据
            
        Returns:
            bool: 是否写入成功
        """
        try:
            # 使用Redis存储
            if self.redis_client:
                key = f"session:{session_id}"
                self.redis_client.set(key, json.dumps(data))
            else:
                # 使用内存存储
                self.in_memory_store["session_memory"][session_id] = data
            
            return True
        except Exception as e:
            print(f"写入会话记忆失败: {e}")
            return False
    
    def write_dialog_history(self, session_id: str, message: Dict[str, Any]) -> bool:
        """写入对话历史
        
        Args:
            session_id: 会话ID
            message: 消息数据
            
        Returns:
            bool: 是否写入成功
        """
        try:
            # 使用Redis存储
            if self.redis_client:
                key = f"session:{session_id}:dialog"
                # 获取现有历史
                existing_history = self.redis_client.get(key)
                if existing_history:
                    history = json.loads(existing_history)
                else:
                    history = []
                
                # 添加新消息
                history.append(message)
                # 限制历史长度（保留最近20条）
                if len(history) > 20:
                    history = history[-20:]
                
                # 保存回Redis
                self.redis_client.set(key, json.dumps(history))
            else:
                # 使用内存存储
                if session_id not in self.in_memory_store["dialog_history"]:
                    self.in_memory_store["dialog_history"][session_id] = []
                
                # 添加新消息
                self.in_memory_store["dialog_history"][session_id].append(message)
                # 限制历史长度
                if len(self.in_memory_store["dialog_history"][session_id]) > 20:
                    self.in_memory_store["dialog_history"][session_id] = \
                        self.in_memory_store["dialog_history"][session_id][-20:]
            
            return True
        except Exception as e:
            print(f"写入对话历史失败: {e}")
            return False
    
    def get_user_memory(self, user_id: str, memory_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取用户记忆
        
        Args:
            user_id: 用户ID
            memory_type: 记忆类型 (可选)
            
        Returns:
            List[Dict[str, Any]]: 记忆列表
        """
        try:
            memories = []
            
            # 使用Redis存储
            if self.redis_client:
                if memory_type:
                    # 获取特定类型的记忆
                    key = f"user:{user_id}:memory:{memory_type}"
                    existing_memories = self.redis_client.get(key)
                    if existing_memories:
                        memories = json.loads(existing_memories)
                else:
                    # 获取所有类型的记忆
                    keys = self.redis_client.keys(f"user:{user_id}:memory:*")
                    for key in keys:
                        existing_memories = self.redis_client.get(key)
                        if existing_memories:
                            memories.extend(json.loads(existing_memories))
            else:
                # 使用内存存储
                if user_id in self.in_memory_store["user_memory"]:
                    if memory_type:
                        # 获取特定类型的记忆
                        if memory_type in self.in_memory_store["user_memory"][user_id]:
                            memories = self.in_memory_store["user_memory"][user_id][memory_type]
                    else:
                        # 获取所有类型的记忆
                        for mem_type, mem_list in self.in_memory_store["user_memory"][user_id].items():
                            memories.extend(mem_list)
            
            # 过滤过期记忆
            return self._filter_expired_memories(memories)
        except Exception as e:
            print(f"获取用户记忆失败: {e}")
            return []
    
    def get_session_memory(self, session_id: str) -> Dict[str, Any]:
        """获取会话记忆
        
        Args:
            session_id: 会话ID
            
        Returns:
            Dict[str, Any]: 会话数据
        """
        try:
            # 使用Redis存储
            if self.redis_client:
                key = f"session:{session_id}"
                existing_data = self.redis_client.get(key)
                if existing_data:
                    return json.loads(existing_data)
            else:
                # 使用内存存储
                if session_id in self.in_memory_store["session_memory"]:
                    return self.in_memory_store["session_memory"][session_id]
            
            return {}
        except Exception as e:
            print(f"获取会话记忆失败: {e}")
            return {}
    
    def get_dialog_history(self, session_id: str, max_turns: int = 5) -> List[Dict[str, Any]]:
        """获取对话历史
        
        Args:
            session_id: 会话ID
            max_turns: 最大轮数
            
        Returns:
            List[Dict[str, Any]]: 对话历史
        """
        try:
            history = []
            
            # 使用Redis存储
            if self.redis_client:
                key = f"session:{session_id}:dialog"
                existing_history = self.redis_client.get(key)
                if existing_history:
                    history = json.loads(existing_history)
            else:
                # 使用内存存储
                if session_id in self.in_memory_store["dialog_history"]:
                    history = self.in_memory_store["dialog_history"][session_id]
            
            # 返回最近的max_turns轮
            return history[-max_turns:]
        except Exception as e:
            print(f"获取对话历史失败: {e}")
            return []
    
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
            # 获取现有会话数据
            session_data = self.get_session_memory(session_id)
            # 更新数据
            session_data[key] = value
            # 写回存储
            return self.write_session_memory(session_id, session_data)
        except Exception as e:
            print(f"更新会话记忆失败: {e}")
            return False
    
    def clear_memory(self, user_id: str, session_id: Optional[str] = None, memory_type: Optional[str] = None) -> bool:
        """清理记忆
        
        Args:
            user_id: 用户ID
            session_id: 会话ID (可选)
            memory_type: 记忆类型 (可选)
            
        Returns:
            bool: 是否清理成功
        """
        try:
            if session_id:
                # 清理会话记忆
                if self.redis_client:
                    self.redis_client.delete(f"session:{session_id}")
                    self.redis_client.delete(f"session:{session_id}:dialog")
                else:
                    if session_id in self.in_memory_store["session_memory"]:
                        del self.in_memory_store["session_memory"][session_id]
                    if session_id in self.in_memory_store["dialog_history"]:
                        del self.in_memory_store["dialog_history"][session_id]
            
            if user_id and memory_type:
                # 清理特定类型的用户记忆
                if self.redis_client:
                    self.redis_client.delete(f"user:{user_id}:memory:{memory_type}")
                else:
                    if user_id in self.in_memory_store["user_memory"] and memory_type in self.in_memory_store["user_memory"][user_id]:
                        del self.in_memory_store["user_memory"][user_id][memory_type]
            elif user_id:
                # 清理用户的所有记忆
                if self.redis_client:
                    keys = self.redis_client.keys(f"user:{user_id}:memory:*")
                    if keys:
                        self.redis_client.delete(*keys)
                else:
                    if user_id in self.in_memory_store["user_memory"]:
                        del self.in_memory_store["user_memory"][user_id]
            
            return True
        except Exception as e:
            print(f"清理记忆失败: {e}")
            return False
    
    def _deduplicate_memories(self, memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重记忆
        
        Args:
            memories: 记忆列表
            
        Returns:
            List[Dict[str, Any]]: 去重后的记忆列表
        """
        seen = set()
        unique_memories = []
        
        for memory in reversed(memories):
            content = memory.get("content", "")
            memory_type = memory.get("memory_type", "")
            key = f"{memory_type}:{content}"
            if key not in seen:
                seen.add(key)
                unique_memories.insert(0, memory)
        
        return unique_memories
    
    def _filter_expired_memories(self, memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """过滤过期记忆
        
        Args:
            memories: 记忆列表
            
        Returns:
            List[Dict[str, Any]]: 未过期的记忆列表
        """
        import datetime
        now = datetime.datetime.now()
        valid_memories = []
        
        for memory in memories:
            expire_time = memory.get("expire_time")
            if not expire_time:
                # 没有过期时间，永久有效
                valid_memories.append(memory)
            else:
                try:
                    expire_dt = datetime.datetime.strptime(expire_time, "%Y-%m-%d %H:%M:%S")
                    if expire_dt > now:
                        valid_memories.append(memory)
                except Exception:
                    # 时间格式错误，视为永久有效
                    valid_memories.append(memory)
        
        return valid_memories