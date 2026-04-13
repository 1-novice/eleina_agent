"""任务服务 - 管理任务数据"""
from sqlalchemy.orm import Session
from src.database.models import Task, TaskStatus
from src.database.database import db_manager
from datetime import datetime
import uuid

class TaskService:
    @staticmethod
    def get_task(db: Session, task_id: str) -> Task:
        return db.query(Task).filter(Task.id == task_id).first()
    
    @staticmethod
    def create_task(db: Session, user_id: str, intent: str, session_id: str = None, total_steps: int = 1) -> Task:
        task = Task(
            id=str(uuid.uuid4()),
            user_id=user_id,
            session_id=session_id,
            intent=intent,
            status=TaskStatus.PENDING,
            current_step=0,
            total_steps=total_steps,
            slots={},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task
    
    @staticmethod
    def update_task(db: Session, task_id: str, **kwargs) -> Task:
        task = TaskService.get_task(db, task_id)
        if task:
            for key, value in kwargs.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            task.updated_at = datetime.now()
            db.commit()
            db.refresh(task)
        return task
    
    @staticmethod
    def update_slots(db: Session, task_id: str, slots: dict) -> Task:
        task = TaskService.get_task(db, task_id)
        if task:
            task.slots = slots
            task.updated_at = datetime.now()
            db.commit()
            db.refresh(task)
        return task
    
    @staticmethod
    def update_step(db: Session, task_id: str, current_step: int, status: TaskStatus = None) -> Task:
        task = TaskService.get_task(db, task_id)
        if task:
            task.current_step = current_step
            if status:
                task.status = status
            task.updated_at = datetime.now()
            db.commit()
            db.refresh(task)
        return task
    
    @staticmethod
    def complete_task(db: Session, task_id: str, result: dict = None) -> Task:
        task = TaskService.get_task(db, task_id)
        if task:
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.completed_at = datetime.now()
            task.updated_at = datetime.now()
            db.commit()
            db.refresh(task)
        return task
    
    @staticmethod
    def fail_task(db: Session, task_id: str, error_message: str) -> Task:
        task = TaskService.get_task(db, task_id)
        if task:
            task.status = TaskStatus.FAILED
            task.error_message = error_message
            task.updated_at = datetime.now()
            db.commit()
            db.refresh(task)
        return task
    
    @staticmethod
    def pause_task(db: Session, task_id: str) -> Task:
        task = TaskService.get_task(db, task_id)
        if task:
            task.status = TaskStatus.PAUSED
            task.updated_at = datetime.now()
            db.commit()
            db.refresh(task)
        return task
    
    @staticmethod
    def delete_task(db: Session, task_id: str) -> bool:
        task = TaskService.get_task(db, task_id)
        if task:
            db.delete(task)
            db.commit()
            return True
        return False
    
    @staticmethod
    def get_user_tasks(db: Session, user_id: str, status: TaskStatus = None) -> list:
        query = db.query(Task).filter(Task.user_id == user_id)
        if status:
            query = query.filter(Task.status == status)
        return query.all()
    
    @staticmethod
    def get_session_tasks(db: Session, session_id: str) -> list:
        return db.query(Task).filter(Task.session_id == session_id).all()
    
    @staticmethod
    def get_running_tasks(db: Session) -> list:
        return db.query(Task).filter(Task.status == TaskStatus.RUNNING).all()

task_service = TaskService()