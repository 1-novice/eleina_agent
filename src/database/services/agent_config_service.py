"""Agent配置服务 - 管理Agent配置数据"""
from sqlalchemy.orm import Session
from src.database.models import AgentConfig
from src.database.database import db_manager
from datetime import datetime

class AgentConfigService:
    @staticmethod
    def get_config(db: Session, config_id: int) -> AgentConfig:
        return db.query(AgentConfig).filter(AgentConfig.id == config_id).first()
    
    @staticmethod
    def get_config_by_name(db: Session, name: str) -> AgentConfig:
        return db.query(AgentConfig).filter(AgentConfig.name == name).first()
    
    @staticmethod
    def create_config(db: Session, name: str, config_data: dict, description: str = None, config_type: str = None) -> AgentConfig:
        config = AgentConfig(
            name=name,
            description=description,
            config_type=config_type,
            config_data=config_data,
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.add(config)
        db.commit()
        db.refresh(config)
        return config
    
    @staticmethod
    def update_config(db: Session, config_id: int, **kwargs) -> AgentConfig:
        config = AgentConfigService.get_config(db, config_id)
        if config:
            for key, value in kwargs.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            config.updated_at = datetime.now()
            db.commit()
            db.refresh(config)
        return config
    
    @staticmethod
    def activate_config(db: Session, config_id: int) -> AgentConfig:
        return AgentConfigService.update_config(db, config_id, is_active=True)
    
    @staticmethod
    def deactivate_config(db: Session, config_id: int) -> AgentConfig:
        return AgentConfigService.update_config(db, config_id, is_active=False)
    
    @staticmethod
    def delete_config(db: Session, config_id: int) -> bool:
        config = AgentConfigService.get_config(db, config_id)
        if config:
            db.delete(config)
            db.commit()
            return True
        return False
    
    @staticmethod
    def get_active_configs(db: Session) -> list:
        return db.query(AgentConfig).filter(AgentConfig.is_active == True).all()
    
    @staticmethod
    def get_configs_by_type(db: Session, config_type: str) -> list:
        return db.query(AgentConfig).filter(AgentConfig.config_type == config_type).all()

agent_config_service = AgentConfigService()