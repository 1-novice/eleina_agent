"""权限服务 - 管理权限数据"""
from sqlalchemy.orm import Session
from src.database.models import Permission, RolePermission, UserRole
from src.database.database import db_manager

class PermissionService:
    @staticmethod
    def get_permission(db: Session, permission_id: int) -> Permission:
        return db.query(Permission).filter(Permission.id == permission_id).first()
    
    @staticmethod
    def get_permission_by_name(db: Session, name: str) -> Permission:
        return db.query(Permission).filter(Permission.name == name).first()
    
    @staticmethod
    def create_permission(db: Session, name: str, description: str = None, resource: str = None, action: str = None) -> Permission:
        permission = Permission(
            name=name,
            description=description,
            resource=resource,
            action=action
        )
        db.add(permission)
        db.commit()
        db.refresh(permission)
        return permission
    
    @staticmethod
    def update_permission(db: Session, permission_id: int, **kwargs) -> Permission:
        permission = PermissionService.get_permission(db, permission_id)
        if permission:
            for key, value in kwargs.items():
                if hasattr(permission, key):
                    setattr(permission, key, value)
            db.commit()
            db.refresh(permission)
        return permission
    
    @staticmethod
    def delete_permission(db: Session, permission_id: int) -> bool:
        permission = PermissionService.get_permission(db, permission_id)
        if permission:
            db.delete(permission)
            db.commit()
            return True
        return False
    
    @staticmethod
    def assign_permission_to_role(db: Session, role: UserRole, permission_id: int) -> RolePermission:
        role_permission = RolePermission(role=role, permission_id=permission_id)
        db.add(role_permission)
        db.commit()
        db.refresh(role_permission)
        return role_permission
    
    @staticmethod
    def get_role_permissions(db: Session, role: UserRole) -> list:
        return db.query(Permission).join(RolePermission).filter(RolePermission.role == role).all()
    
    @staticmethod
    def has_permission(db: Session, role: UserRole, permission_name: str) -> bool:
        permission = PermissionService.get_permission_by_name(db, permission_name)
        if not permission:
            return False
        return db.query(RolePermission).filter(
            RolePermission.role == role,
            RolePermission.permission_id == permission.id
        ).first() is not None

permission_service = PermissionService()