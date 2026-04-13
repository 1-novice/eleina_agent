"""用户服务 - 管理用户数据"""
from sqlalchemy.orm import Session
from src.database.models import User, UserRole
from src.database.database import db_manager
from datetime import datetime
import uuid
import hashlib

class UserService:
    @staticmethod
    def get_user(db: Session, user_id: str) -> User:
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> User:
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> User:
        return db.query(User).filter(User.username == username).first()
    
    @staticmethod
    def create_user(db: Session, username: str, email: str, password: str, role: UserRole = UserRole.USER) -> User:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        user = User(
            id=str(uuid.uuid4()),
            username=username,
            email=email,
            password_hash=password_hash,
            role=role,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def update_user(db: Session, user_id: str, **kwargs) -> User:
        user = UserService.get_user(db, user_id)
        if user:
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            user.updated_at = datetime.now()
            db.commit()
            db.refresh(user)
        return user
    
    @staticmethod
    def delete_user(db: Session, user_id: str) -> bool:
        user = UserService.get_user(db, user_id)
        if user:
            db.delete(user)
            db.commit()
            return True
        return False
    
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> User:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        return db.query(User).filter(
            User.email == email,
            User.password_hash == password_hash,
            User.is_active == True
        ).first()
    
    @staticmethod
    def list_users(db: Session, skip: int = 0, limit: int = 100) -> list:
        return db.query(User).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_users_by_role(db: Session, role: UserRole) -> list:
        return db.query(User).filter(User.role == role).all()

user_service = UserService()