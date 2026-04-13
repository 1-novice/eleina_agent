"""审计日志服务 - 管理审计日志数据"""
from sqlalchemy.orm import Session
from src.database.models import AuditLog
from src.database.database import db_manager
from datetime import datetime

class AuditService:
    @staticmethod
    def get_log(db: Session, log_id: int) -> AuditLog:
        return db.query(AuditLog).filter(AuditLog.id == log_id).first()
    
    @staticmethod
    def create_log(db: Session, user_id: str, action: str, resource_type: str = None, resource_id: str = None, details: dict = None, ip_address: str = None, user_agent: str = None, success: bool = True, error_message: str = None) -> AuditLog:
        log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message,
            created_at=datetime.now()
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log
    
    @staticmethod
    def log_success(db: Session, user_id: str, action: str, resource_type: str = None, resource_id: str = None, details: dict = None, ip_address: str = None) -> AuditLog:
        return AuditService.create_log(db, user_id, action, resource_type, resource_id, details, ip_address, success=True)
    
    @staticmethod
    def log_failure(db: Session, user_id: str, action: str, error_message: str, resource_type: str = None, resource_id: str = None, details: dict = None, ip_address: str = None) -> AuditLog:
        return AuditService.create_log(db, user_id, action, resource_type, resource_id, details, ip_address, success=False, error_message=error_message)
    
    @staticmethod
    def get_user_logs(db: Session, user_id: str) -> list:
        return db.query(AuditLog).filter(AuditLog.user_id == user_id).order_by(AuditLog.created_at.desc()).all()
    
    @staticmethod
    def get_logs_by_action(db: Session, action: str) -> list:
        return db.query(AuditLog).filter(AuditLog.action == action).order_by(AuditLog.created_at.desc()).all()
    
    @staticmethod
    def get_failed_logs(db: Session) -> list:
        return db.query(AuditLog).filter(AuditLog.success == False).order_by(AuditLog.created_at.desc()).all()
    
    @staticmethod
    def get_recent_logs(db: Session, limit: int = 100) -> list:
        return db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()

audit_service = AuditService()