"""结构化记忆服务 - 管理结构化记忆数据"""
from sqlalchemy.orm import Session
from src.database.models import StructuredMemory
from src.database.database import db_manager
from datetime import datetime, timedelta
import uuid

class MemoryService:
    @staticmethod
    def get_memory(db: Session, memory_id: str) -> StructuredMemory:
        return db.query(StructuredMemory).filter(StructuredMemory.id == memory_id).first()
    
    @staticmethod
    def get_memory_by_key(db: Session, user_id: str, key: str) -> StructuredMemory:
        return db.query(StructuredMemory).filter(
            StructuredMemory.user_id == user_id,
            StructuredMemory.key == key
        ).first()
    
    @staticmethod
    def create_memory(db: Session, user_id: str, memory_type: str, key: str, value: dict, score: float = 1.0, expires_at: datetime = None) -> StructuredMemory:
        memory = StructuredMemory(
            id=str(uuid.uuid4()),
            user_id=user_id,
            memory_type=memory_type,
            key=key,
            value=value,
            score=score,
            expires_at=expires_at,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.add(memory)
        db.commit()
        db.refresh(memory)
        return memory
    
    @staticmethod
    def update_memory(db: Session, memory_id: str, **kwargs) -> StructuredMemory:
        memory = MemoryService.get_memory(db, memory_id)
        if memory:
            for key, value in kwargs.items():
                if hasattr(memory, key):
                    setattr(memory, key, value)
            memory.updated_at = datetime.now()
            db.commit()
            db.refresh(memory)
        return memory
    
    @staticmethod
    def upsert_memory(db: Session, user_id: str, memory_type: str, key: str, value: dict, score: float = 1.0) -> StructuredMemory:
        existing = MemoryService.get_memory_by_key(db, user_id, key)
        if existing:
            return MemoryService.update_memory(db, existing.id, value=value, score=score)
        return MemoryService.create_memory(db, user_id, memory_type, key, value, score)
    
    @staticmethod
    def delete_memory(db: Session, memory_id: str) -> bool:
        memory = MemoryService.get_memory(db, memory_id)
        if memory:
            db.delete(memory)
            db.commit()
            return True
        return False
    
    @staticmethod
    def delete_memory_by_key(db: Session, user_id: str, key: str) -> bool:
        memory = MemoryService.get_memory_by_key(db, user_id, key)
        if memory:
            db.delete(memory)
            db.commit()
            return True
        return False
    
    @staticmethod
    def get_user_memories(db: Session, user_id: str, memory_type: str = None) -> list:
        query = db.query(StructuredMemory).filter(StructuredMemory.user_id == user_id)
        if memory_type:
            query = query.filter(StructuredMemory.memory_type == memory_type)
        return query.order_by(StructuredMemory.score.desc()).all()
    
    @staticmethod
    def get_memories_by_type(db: Session, memory_type: str) -> list:
        return db.query(StructuredMemory).filter(StructuredMemory.memory_type == memory_type).all()
    
    @staticmethod
    def cleanup_expired_memories(db: Session) -> int:
        expired = db.query(StructuredMemory).filter(StructuredMemory.expires_at < datetime.now()).all()
        count = len(expired)
        for memory in expired:
            db.delete(memory)
        db.commit()
        return count

memory_service = MemoryService()