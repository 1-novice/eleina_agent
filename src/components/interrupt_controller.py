"""中断、恢复、超时控制器 - 管理会话的中断、恢复和超时"""
from typing import Dict, Callable, Optional, Any
from datetime import datetime, timedelta
import threading
import time

class InterruptController:
    """中断、恢复、超时控制器"""
    
    def __init__(self):
        self.timeout_handlers: Dict[str, Callable] = {}
        self.timers: Dict[str, threading.Timer] = {}
        self.paused_sessions: Dict[str, Dict[str, Any]] = {}
        self.default_timeout = timedelta(minutes=30)
        self.interrupted_tasks: Dict[str, Dict[str, Any]] = {}
    
    def set_timeout(self, session_id: str, timeout: timedelta = None, 
                    handler: Callable = None):
        """设置会话超时"""
        # 清除之前的定时器
        self.clear_timeout(session_id)
        
        # 创建新定时器
        timeout_seconds = (timeout or self.default_timeout).total_seconds()
        
        def timeout_callback():
            if handler:
                handler(session_id)
            else:
                self._default_timeout_handler(session_id)
        
        timer = threading.Timer(timeout_seconds, timeout_callback)
        timer.daemon = True
        timer.start()
        
        self.timers[session_id] = timer
        self.timeout_handlers[session_id] = handler
    
    def clear_timeout(self, session_id: str):
        """清除会话超时"""
        timer = self.timers.pop(session_id, None)
        if timer:
            timer.cancel()
        self.timeout_handlers.pop(session_id, None)
    
    def reset_timeout(self, session_id: str):
        """重置会话超时计时器"""
        handler = self.timeout_handlers.get(session_id)
        self.set_timeout(session_id, self.default_timeout, handler)
    
    def _default_timeout_handler(self, session_id: str):
        """默认超时处理"""
        print(f"会话 {session_id} 超时")
        self.pause_session(session_id, reason="timeout")
    
    def pause_session(self, session_id: str, reason: str = "user_request"):
        """暂停会话"""
        from src.components.session_manager import session_manager
        
        session = session_manager.get_session(session_id)
        if session:
            self.paused_sessions[session_id] = {
                "session_data": session,
                "paused_at": datetime.now().isoformat(),
                "reason": reason
            }
            session["status"] = "paused"
    
    def resume_session(self, session_id: str) -> bool:
        """恢复会话"""
        paused_data = self.paused_sessions.pop(session_id, None)
        if paused_data:
            from src.components.session_manager import session_manager
            
            session = session_manager.get_session(session_id)
            if session:
                session["status"] = "active"
                session["resumed_at"] = datetime.now().isoformat()
                session["paused_reason"] = paused_data["reason"]
            
            # 重置超时计时器
            self.reset_timeout(session_id)
            return True
        
        return False
    
    def interrupt_task(self, task_id: str, reason: str = "user_request"):
        """中断任务"""
        from src.components.task_progress_manager import task_progress_manager
        
        task = task_progress_manager.get_task(task_id)
        if task:
            self.interrupted_tasks[task_id] = {
                "task_data": task.copy(),
                "interrupted_at": datetime.now().isoformat(),
                "reason": reason
            }
            task_progress_manager.pause_task(task_id)
    
    def resume_task(self, task_id: str) -> bool:
        """恢复任务"""
        interrupted_data = self.interrupted_tasks.pop(task_id, None)
        if interrupted_data:
            from src.components.task_progress_manager import task_progress_manager
            
            task_progress_manager.resume_task(task_id)
            return True
        
        return False
    
    def cancel_task(self, task_id: str):
        """取消任务"""
        from src.components.task_progress_manager import task_progress_manager
        
        task_progress_manager.fail_task(task_id, "任务已取消")
        self.interrupted_tasks.pop(task_id, None)
    
    def force_quit(self, session_id: str):
        """强制退出会话"""
        self.clear_timeout(session_id)
        self.paused_sessions.pop(session_id, None)
        
        from src.components.session_manager import session_manager
        session_manager.destroy_session(session_id)
        
        # 取消所有相关任务
        from src.components.task_progress_manager import task_progress_manager
        tasks = task_progress_manager.get_tasks_by_session(session_id)
        for task in tasks:
            task_progress_manager.fail_task(task["task_id"], "会话已关闭")
    
    def get_paused_sessions(self) -> Dict[str, Dict[str, Any]]:
        """获取所有暂停的会话"""
        return self.paused_sessions
    
    def get_interrupted_tasks(self) -> Dict[str, Dict[str, Any]]:
        """获取所有中断的任务"""
        return self.interrupted_tasks


# 全局中断控制器实例
interrupt_controller = InterruptController()
