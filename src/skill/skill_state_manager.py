from typing import Dict, List, Optional, Any
import time


class SkillStateManager:
    def __init__(self):
        # 存储会话状态
        self.session_states = {}
        # 会话超时时间（秒）
        self.session_timeout = 3600  # 1小时
    
    def get_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话状态
        
        Args:
            session_id: 会话ID
            
        Returns:
            Optional[Dict[str, Any]]: 会话状态
        """
        if session_id not in self.session_states:
            return None
        
        # 检查会话是否超时
        state = self.session_states[session_id]
        last_update = state.get("last_update", 0)
        if time.time() - last_update > self.session_timeout:
            # 会话超时，删除状态
            del self.session_states[session_id]
            return None
        
        return state
    
    def set_state(self, session_id: str, state: Dict[str, Any]):
        """设置会话状态
        
        Args:
            session_id: 会话ID
            state: 会话状态
        """
        # 更新最后更新时间
        state["last_update"] = time.time()
        self.session_states[session_id] = state
    
    def update_state(self, session_id: str, **kwargs):
        """更新会话状态
        
        Args:
            session_id: 会话ID
            **kwargs: 要更新的状态字段
        """
        state = self.get_state(session_id)
        if state:
            state.update(kwargs)
            self.set_state(session_id, state)
        else:
            # 创建新状态
            new_state = {
                "skill_id": kwargs.get("skill_id"),
                "current_step": 0,
                "slots": {},
                "tool_executions": [],
                "waiting_for_user": False,
                "last_update": time.time()
            }
            new_state.update(kwargs)
            self.set_state(session_id, new_state)
    
    def clear_state(self, session_id: str):
        """清除会话状态
        
        Args:
            session_id: 会话ID
        """
        if session_id in self.session_states:
            del self.session_states[session_id]
    
    def create_snapshot(self, session_id: str) -> Optional[Dict[str, Any]]:
        """创建上下文快照
        
        Args:
            session_id: 会话ID
            
        Returns:
            Optional[Dict[str, Any]]: 上下文快照
        """
        state = self.get_state(session_id)
        if not state:
            return None
        
        # 创建快照
        snapshot = {
            "session_id": session_id,
            "skill_id": state.get("skill_id"),
            "current_step": state.get("current_step", 0),
            "slots": state.get("slots", {}),
            "tool_executions": state.get("tool_executions", []),
            "waiting_for_user": state.get("waiting_for_user", False),
            "snapshot_time": time.time()
        }
        
        return snapshot
    
    def restore_from_snapshot(self, snapshot: Dict[str, Any]) -> bool:
        """从快照恢复状态
        
        Args:
            snapshot: 上下文快照
            
        Returns:
            bool: 是否恢复成功
        """
        session_id = snapshot.get("session_id")
        if not session_id:
            return False
        
        # 恢复状态
        state = {
            "skill_id": snapshot.get("skill_id"),
            "current_step": snapshot.get("current_step", 0),
            "slots": snapshot.get("slots", {}),
            "tool_executions": snapshot.get("tool_executions", []),
            "waiting_for_user": snapshot.get("waiting_for_user", False),
            "last_update": time.time()
        }
        
        self.set_state(session_id, state)
        return True
    
    def is_waiting_for_user(self, session_id: str) -> bool:
        """检查是否等待用户输入
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 是否等待用户输入
        """
        state = self.get_state(session_id)
        if not state:
            return False
        
        return state.get("waiting_for_user", False)
    
    def set_waiting_for_user(self, session_id: str, waiting: bool):
        """设置是否等待用户输入
        
        Args:
            session_id: 会话ID
            waiting: 是否等待用户输入
        """
        self.update_state(session_id, waiting_for_user=waiting)


# 全局Skill状态管理实例
skill_state_manager = SkillStateManager()