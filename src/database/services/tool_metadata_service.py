"""工具元数据服务 - 管理工具元数据"""
from sqlalchemy.orm import Session
from src.database.models import ToolMetadata
from src.database.database import db_manager
from datetime import datetime

class ToolMetadataService:
    @staticmethod
    def get_tool(db: Session, tool_id: int) -> ToolMetadata:
        return db.query(ToolMetadata).filter(ToolMetadata.id == tool_id).first()
    
    @staticmethod
    def get_tool_by_name(db: Session, tool_name: str) -> ToolMetadata:
        return db.query(ToolMetadata).filter(ToolMetadata.tool_name == tool_name).first()
    
    @staticmethod
    def create_tool(db: Session, tool_name: str, description: str = None, parameters: dict = None, return_type: str = None, category: str = None, enabled: bool = True, requires_permission: str = None) -> ToolMetadata:
        tool = ToolMetadata(
            tool_name=tool_name,
            description=description,
            parameters=parameters,
            return_type=return_type,
            category=category,
            enabled=enabled,
            requires_permission=requires_permission,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.add(tool)
        db.commit()
        db.refresh(tool)
        return tool
    
    @staticmethod
    def update_tool(db: Session, tool_id: int, **kwargs) -> ToolMetadata:
        tool = ToolMetadataService.get_tool(db, tool_id)
        if tool:
            for key, value in kwargs.items():
                if hasattr(tool, key):
                    setattr(tool, key, value)
            tool.updated_at = datetime.now()
            db.commit()
            db.refresh(tool)
        return tool
    
    @staticmethod
    def enable_tool(db: Session, tool_id: int) -> ToolMetadata:
        return ToolMetadataService.update_tool(db, tool_id, enabled=True)
    
    @staticmethod
    def disable_tool(db: Session, tool_id: int) -> ToolMetadata:
        return ToolMetadataService.update_tool(db, tool_id, enabled=False)
    
    @staticmethod
    def delete_tool(db: Session, tool_id: int) -> bool:
        tool = ToolMetadataService.get_tool(db, tool_id)
        if tool:
            db.delete(tool)
            db.commit()
            return True
        return False
    
    @staticmethod
    def get_enabled_tools(db: Session) -> list:
        return db.query(ToolMetadata).filter(ToolMetadata.enabled == True).all()
    
    @staticmethod
    def get_tools_by_category(db: Session, category: str) -> list:
        return db.query(ToolMetadata).filter(ToolMetadata.category == category).all()

tool_metadata_service = ToolMetadataService()