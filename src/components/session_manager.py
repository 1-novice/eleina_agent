"""会话管理器 - 管理用户会话的创建、销毁和生命周期"""
from typing import Dict, Optional, Any
import uuid
from datetime import datetime, timedelta
import json
import os

class SessionManager:
    """会话管理器"""
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.session_timeout = timedelta(minutes=30)
        self.archived_sessions: Dict[str, Dict[str, Any]] = {}
        self._load_archived_sessions()
    
    def _load_archived_sessions(self):
        """加载归档的会话"""
        archive_path = "data/sessions/archived_sessions.json"
        if os.path.exists(archive_path):
            try:
                with open(archive_path, 'r', encoding='utf-8') as f:
                    self.archived_sessions = json.load(f)
            except:
                self.archived_sessions = {}
    
    def _save_archived_sessions(self):
        """保存归档的会话"""
        os.makedirs("data/sessions", exist_ok=True)
        archive_path = "data/sessions/archived_sessions.json"
        with open(archive_path, 'w', encoding='utf-8') as f:
            json.dump(self.archived_sessions, f, ensure_ascii=False, indent=2)
    
    def create_session(self, user_id: str, **kwargs) -> str:
        """创建会话"""
        session_id = str(uuid.uuid4())
        
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat(),
            "status": "active",
            "context": [],
            "task_info": None,
            "metadata": {
                "device": kwargs.get("device", "unknown"),
                "source": kwargs.get("source", "unknown"),
                "ip": kwargs.get("ip", "unknown")
            }
        }
        
        self.sessions[session_id] = session_data
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话"""
        session = self.sessions.get(session_id)
        if session:
            # 更新最后活跃时间
            session["last_active"] = datetime.now().isoformat()
            return session
        return None
    
    def update_session(self, session_id: str, **kwargs):
        """更新会话"""
        session = self.sessions.get(session_id)
        if session:
            session.update(kwargs)
            session["last_active"] = datetime.now().isoformat()
    
    def update_context(self, session_id: str, context_item: Dict[str, Any]):
        """更新会话上下文"""
        session = self.sessions.get(session_id)
        if session:
            session["context"].append(context_item)
            session["last_active"] = datetime.now().isoformat()
    
    def destroy_session(self, session_id: str, archive: bool = True):
        """销毁会话"""
        session = self.sessions.pop(session_id, None)
        if session and archive:
            self._archive_session(session)
    
    def _archive_session(self, session: Dict[str, Any]):
        """归档会话"""
        session["archived_at"] = datetime.now().isoformat()
        session["status"] = "archived"
        self.archived_sessions[session["session_id"]] = session
        self._save_archived_sessions()
    
    def cleanup_expired_sessions(self):
        """清理过期会话"""
        now = datetime.now()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            last_active = datetime.fromisoformat(session["last_active"])
            if now - last_active > self.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self.destroy_session(session_id)
        
        return len(expired_sessions)
    
    def get_active_sessions(self) -> Dict[str, Dict[str, Any]]:
        """获取所有活跃会话"""
        return self.sessions
    
    def get_session_count(self) -> int:
        """获取活跃会话数"""
        return len(self.sessions)
    
    def get_user_sessions(self, user_id: str) -> list:
        """获取用户的所有活跃会话"""
        return [s for s in self.sessions.values() if s["user_id"] == user_id]
    
    def is_session_active(self, session_id: str) -> bool:
        """检查会话是否活跃"""
        session = self.sessions.get(session_id)
        if not session:
            return False
        
        last_active = datetime.fromisoformat(session["last_active"])
        return datetime.now() - last_active <= self.session_timeout


# 全局会话管理器实例
session_manager = SessionManager()
