"""MySQL数据库模型定义"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON, Enum, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

class UserRole(enum.Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"

class TaskStatus(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

class SessionStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, comment="用户唯一标识")
    username = Column(String(100), unique=True, nullable=False, comment="用户名")
    email = Column(String(255), unique=True, nullable=False, comment="邮箱")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    role = Column(Enum(UserRole), default=UserRole.USER, comment="用户角色")
    avatar_url = Column(String(500), comment="头像URL")
    settings = Column(JSON, default={}, comment="用户设置")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    is_active = Column(Boolean, default=True, comment="是否活跃")
    
    sessions = relationship("Session", back_populates="user")
    tasks = relationship("Task", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")

class Permission(Base):
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, comment="权限名称")
    description = Column(Text, comment="权限描述")
    resource = Column(String(100), comment="资源类型")
    action = Column(String(100), comment="操作类型")
    created_at = Column(DateTime, default=datetime.now)
    
    role_permissions = relationship("RolePermission", back_populates="permission")

class RolePermission(Base):
    __tablename__ = "role_permissions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    role = Column(Enum(UserRole), nullable=False, comment="角色")
    permission_id = Column(Integer, ForeignKey("permissions.id"), nullable=False)
    
    permission = relationship("Permission", back_populates="role_permissions")

class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(String(36), primary_key=True, comment="会话唯一标识")
    user_id = Column(String(36), ForeignKey("users.id"), comment="用户ID")
    device = Column(String(100), comment="设备信息")
    source = Column(String(100), comment="来源")
    ip_address = Column(String(50), comment="IP地址")
    status = Column(Enum(SessionStatus), default=SessionStatus.ACTIVE, comment="会话状态")
    context = Column(JSON, default={}, comment="会话上下文")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    last_active_at = Column(DateTime, default=datetime.now, comment="最后活跃时间")
    expires_at = Column(DateTime, comment="过期时间")
    
    user = relationship("User", back_populates="sessions")
    tasks = relationship("Task", back_populates="session")

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(String(36), primary_key=True, comment="任务唯一标识")
    user_id = Column(String(36), ForeignKey("users.id"), comment="用户ID")
    session_id = Column(String(36), ForeignKey("sessions.id"), comment="会话ID")
    intent = Column(String(100), nullable=False, comment="任务意图")
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, comment="任务状态")
    current_step = Column(Integer, default=0, comment="当前步骤")
    total_steps = Column(Integer, default=1, comment="总步骤数")
    slots = Column(JSON, default={}, comment="槽位信息")
    result = Column(JSON, comment="任务结果")
    error_message = Column(Text, comment="错误信息")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    completed_at = Column(DateTime, comment="完成时间")
    
    user = relationship("User", back_populates="tasks")
    session = relationship("Session", back_populates="tasks")

class AgentConfig(Base):
    __tablename__ = "agent_configs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, comment="配置名称")
    description = Column(Text, comment="配置描述")
    config_type = Column(String(50), comment="配置类型")
    config_data = Column(JSON, nullable=False, comment="配置数据")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class ToolMetadata(Base):
    __tablename__ = "tool_metadata"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tool_name = Column(String(100), unique=True, nullable=False, comment="工具名称")
    description = Column(Text, comment="工具描述")
    parameters = Column(JSON, comment="参数定义")
    return_type = Column(String(100), comment="返回类型")
    category = Column(String(50), comment="工具分类")
    enabled = Column(Boolean, default=True, comment="是否启用")
    requires_permission = Column(String(100), comment="所需权限")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class StructuredMemory(Base):
    __tablename__ = "structured_memory"
    
    id = Column(String(36), primary_key=True, comment="记忆唯一标识")
    user_id = Column(String(36), ForeignKey("users.id"), comment="用户ID")
    memory_type = Column(String(50), nullable=False, comment="记忆类型")
    key = Column(String(200), nullable=False, comment="记忆键")
    value = Column(JSON, nullable=False, comment="记忆值")
    score = Column(Float, default=1.0, comment="重要性分数")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    expires_at = Column(DateTime, comment="过期时间")
    
    user = relationship("User")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("users.id"), comment="用户ID")
    action = Column(String(100), nullable=False, comment="操作类型")
    resource_type = Column(String(100), comment="资源类型")
    resource_id = Column(String(36), comment="资源ID")
    details = Column(JSON, comment="操作详情")
    ip_address = Column(String(50), comment="IP地址")
    user_agent = Column(String(500), comment="用户代理")
    success = Column(Boolean, default=True, comment="是否成功")
    error_message = Column(Text, comment="错误信息")
    created_at = Column(DateTime, default=datetime.now)
    
    user = relationship("User", back_populates="audit_logs")