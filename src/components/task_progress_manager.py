"""任务进度管理器 - 管理任务的生命周期和进度"""
from typing import Dict, Optional, Any, List
import uuid
from datetime import datetime, timedelta
import json
import os
from enum import Enum

class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskProgressManager:
    """任务进度管理器"""
    
    def __init__(self):
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.task_timeout = timedelta(hours=2)
        self._load_tasks()
    
    def _load_tasks(self):
        """加载保存的任务"""
        tasks_path = "data/tasks/tasks.json"
        if os.path.exists(tasks_path):
            try:
                with open(tasks_path, 'r', encoding='utf-8') as f:
                    self.tasks = json.load(f)
            except:
                self.tasks = {}
    
    def _save_tasks(self):
        """保存任务"""
        os.makedirs("data/tasks", exist_ok=True)
        tasks_path = "data/tasks/tasks.json"
        with open(tasks_path, 'w', encoding='utf-8') as f:
            json.dump(self.tasks, f, ensure_ascii=False, indent=2)
    
    def create_task(self, intent: str, slots: Dict[str, Any] = None, session_id: str = None, total_steps: int = 1) -> str:
        """创建任务"""
        task_id = str(uuid.uuid4())
        
        task_data = {
            "task_id": task_id,
            "intent": intent,
            "status": "running",
            "current_step": 0,
            "total_steps": total_steps,
            "slots": slots or {},
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "steps": [],
            "results": {}
        }
        
        self.tasks[task_id] = task_data
        self._save_tasks()
        return task_id
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务"""
        return self.tasks.get(task_id)
    
    def update_task(self, task_id: str, **kwargs):
        """更新任务"""
        task = self.tasks.get(task_id)
        if task:
            task.update(kwargs)
            task["updated_at"] = datetime.now().isoformat()
            self._save_tasks()
    
    def set_step(self, task_id: str, step_number: int, step_name: str, status: str = "completed"):
        """设置任务步骤"""
        task = self.tasks.get(task_id)
        if task:
            step = {
                "step_number": step_number,
                "step_name": step_name,
                "status": status,
                "completed_at": datetime.now().isoformat() if status == "completed" else None
            }
            
            # 查找并更新现有步骤
            existing_steps = [s for s in task["steps"] if s["step_number"] == step_number]
            if existing_steps:
                existing_steps[0].update(step)
            else:
                task["steps"].append(step)
            
            task["current_step"] = step_number
            task["updated_at"] = datetime.now().isoformat()
            self._save_tasks()
    
    def set_slots(self, task_id: str, slots: Dict[str, Any]):
        """设置槽位"""
        task = self.tasks.get(task_id)
        if task:
            task["slots"].update(slots)
            task["updated_at"] = datetime.now().isoformat()
            self._save_tasks()
    
    def complete_task(self, task_id: str, results: Dict[str, Any] = None):
        """完成任务"""
        task = self.tasks.get(task_id)
        if task:
            task["status"] = "completed"
            task["results"] = results or {}
            task["updated_at"] = datetime.now().isoformat()
            task["completed_at"] = datetime.now().isoformat()
            self._save_tasks()
    
    def fail_task(self, task_id: str, error_message: str):
        """任务失败"""
        task = self.tasks.get(task_id)
        if task:
            task["status"] = "failed"
            task["error_message"] = error_message
            task["updated_at"] = datetime.now().isoformat()
            task["failed_at"] = datetime.now().isoformat()
            self._save_tasks()
    
    def pause_task(self, task_id: str):
        """暂停任务"""
        task = self.tasks.get(task_id)
        if task:
            task["status"] = "paused"
            task["updated_at"] = datetime.now().isoformat()
            self._save_tasks()
    
    def resume_task(self, task_id: str):
        """恢复任务"""
        task = self.tasks.get(task_id)
        if task:
            task["status"] = "running"
            task["updated_at"] = datetime.now().isoformat()
            self._save_tasks()
    
    def destroy_task(self, task_id: str):
        """销毁任务"""
        self.tasks.pop(task_id, None)
        self._save_tasks()
    
    def cleanup_expired_tasks(self):
        """清理过期任务"""
        now = datetime.now()
        expired_tasks = []
        
        for task_id, task in self.tasks.items():
            updated_at = datetime.fromisoformat(task["updated_at"])
            if now - updated_at > self.task_timeout:
                expired_tasks.append(task_id)
        
        for task_id in expired_tasks:
            self.destroy_task(task_id)
        
        return len(expired_tasks)
    
    def get_tasks_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """获取会话的所有任务"""
        return [t for t in self.tasks.values() if t.get("session_id") == session_id]
    
    def get_tasks_by_status(self, status: str) -> List[Dict[str, Any]]:
        """获取指定状态的任务"""
        return [t for t in self.tasks.values() if t.get("status") == status]
    
    def get_task_progress(self, task_id: str) -> float:
        """获取任务进度百分比"""
        task = self.tasks.get(task_id)
        if not task:
            return 0.0
        
        if task["total_steps"] == 0:
            return 0.0
        
        return (task["current_step"] / task["total_steps"]) * 100


# 全局任务进度管理器实例
task_progress_manager = TaskProgressManager()
