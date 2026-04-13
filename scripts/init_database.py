#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""初始化MySQL数据库"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.database import db_manager
from src.database.services import user_service, permission_service
from src.database.models import UserRole

def init_database():
    print("=== 初始化数据库 ===")
    
    try:
        # 创建数据库连接
        db_manager.initialize()
        print("✓ 数据库连接初始化成功")
        
        # 创建表
        db_manager.create_tables()
        print("✓ 数据库表创建成功")
        
        # 获取数据库会话
        db = next(db_manager.get_db())
        
        # 检查是否需要初始化数据
        if db.query(user_service.User).count() == 0:
            print("=== 初始化默认数据 ===")
            
            # 创建管理员用户
            admin = user_service.UserService.create_user(
                db,
                username="admin",
                email="admin@example.com",
                password="admin123",
                role=UserRole.ADMIN
            )
            print(f"✓ 创建管理员用户: {admin.username}")
            
            # 创建测试用户
            user = user_service.UserService.create_user(
                db,
                username="user",
                email="user@example.com",
                password="user123",
                role=UserRole.USER
            )
            print(f"✓ 创建测试用户: {user.username}")
            
            # 创建权限
            permissions = [
                {"name": "read_user", "description": "读取用户信息", "resource": "user", "action": "read"},
                {"name": "write_user", "description": "修改用户信息", "resource": "user", "action": "write"},
                {"name": "delete_user", "description": "删除用户", "resource": "user", "action": "delete"},
                {"name": "run_tool", "description": "运行工具", "resource": "tool", "action": "run"},
                {"name": "manage_config", "description": "管理配置", "resource": "config", "action": "manage"},
                {"name": "view_logs", "description": "查看日志", "resource": "log", "action": "view"},
            ]
            
            for perm_data in permissions:
                perm = permission_service.PermissionService.create_permission(db, **perm_data)
                print(f"✓ 创建权限: {perm.name}")
            
            # 为管理员分配所有权限
            admin_permissions = db.query(permission_service.Permission).all()
            for perm in admin_permissions:
                permission_service.PermissionService.assign_permission_to_role(db, UserRole.ADMIN, perm.id)
            print("✓ 为管理员分配所有权限")
            
            # 为普通用户分配基础权限
            user_permissions = db.query(permission_service.Permission).filter(
                permission_service.Permission.name.in_(["read_user", "run_tool"])
            ).all()
            for perm in user_permissions:
                permission_service.PermissionService.assign_permission_to_role(db, UserRole.USER, perm.id)
            print("✓ 为普通用户分配基础权限")
        
        print("\n=== 数据库初始化完成 ===")
        
    except Exception as e:
        print(f"✗ 数据库初始化失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    init_database()