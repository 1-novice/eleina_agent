"""会话服务 - 管理会话数据"""
from sqlalchemy.orm import Session
from src.database.models import Session, SessionStatus
from src.database.database import db_manager
from datetime import datetime, timedelta
import uuid

class SessionService:
    @staticmethod
    def get_session(db: Session, session_id: str) -> Session:
        return db.query(Session).filter(Session.id == session_id).first()
    
    @staticmethod
    def create_session(db: Session, user_id: str = None, device: str = None, source: str = None, ip_address: str = None) -> Session:
        session = Session(
            id=str(uuid.uuid4()),
            user_id=user_id,
            device=device,
            source=source,
            ip_address=ip_address,
            status=SessionStatus.ACTIVE,
            context={},
            created_at=datetime.now(),
            last_active_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=24)
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session
    
    @staticmethod
    def update_session(db: Session, session_id: str, **kwargs) -> Session:
        session = SessionService.get_session(db, session_id)
        if session:
            for key, value in kwargs.items():
                if hasattr(session, key):
                    setattr(session, key, value)
            session.last_active_at = datetime.now()
            db.commit()
            db.refresh(session)
        return session
    
    @staticmethod
    def update_context(db: Session, session_id: str, context: dict) -> Session:
        session = SessionService.get_session(db, session_id)
        if session:
            session.context = context
            session.last_active_at = datetime.now()
            db.commit()
            db.refresh(session)
        return session
    
    @staticmethod
    def expire_session(db: Session, session_id: str) -> bool:
        session = SessionService.get_session(db, session_id)
        if session:
            session.status = SessionStatus.EXPIRED
            db.commit()
            return True
        return False
    
    @staticmethod
    def delete_session(db: Session, session_id: str) -> bool:
        session = SessionService.get_session(db, session_id)
        if session:
            db.delete(session)
            db.commit()
            return True
        return False
    
    @staticmethod
    def get_user_sessions(db: Session, user_id: str) -> list:
        return db.query(Session).filter(Session.user_id == user_id).all()
    
    @staticmethod
    def get_active_sessions(db: Session) -> list:
        return db.query(Session).filter(Session.status == SessionStatus.ACTIVE).all()
    
    @staticmethod
    def cleanup_expired_sessions(db: Session) -> int:
        expired = db.query(Session).filter(Session.expires_at < datetime.now()).all()
        count = len(expired)
        for session in expired:
            db.delete(session)
        db.commit()
        return count

session_service = SessionService()