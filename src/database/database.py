"""MySQL数据库连接管理"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from src.config.config import settings
from src.database.models import Base
import pymysql
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def _create_database_if_not_exists(self):
        try:
            connection = pymysql.connect(
                host=settings.mysql_host,
                port=settings.mysql_port,
                user=settings.mysql_user,
                password=settings.mysql_password
            )
            cursor = connection.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {settings.mysql_database} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            cursor.close()
            connection.close()
            logger.info(f"数据库 {settings.mysql_database} 检查/创建成功")
        except Exception as e:
            logger.error(f"创建数据库失败: {e}")
            raise
    
    def initialize(self):
        if self._initialized:
            return
        
        try:
            self._create_database_if_not_exists()
            
            connection_string = f"mysql+pymysql://{settings.mysql_user}:{settings.mysql_password}@{settings.mysql_host}:{settings.mysql_port}/{settings.mysql_database}"
            self.engine = create_engine(connection_string, pool_pre_ping=True, pool_recycle=3600)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            self._initialized = True
            logger.info("MySQL数据库连接初始化成功")
        except Exception as e:
            logger.error(f"MySQL数据库连接初始化失败: {e}")
            raise
    
    def get_db(self) -> Session:
        if not self._initialized:
            self.initialize()
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    def create_tables(self):
        if not self._initialized:
            self.initialize()
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("数据库表创建成功")
        except SQLAlchemyError as e:
            logger.error(f"数据库表创建失败: {e}")
            raise
    
    def drop_tables(self):
        if not self._initialized:
            self.initialize()
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.info("数据库表删除成功")
        except SQLAlchemyError as e:
            logger.error(f"数据库表删除失败: {e}")
            raise

db_manager = DatabaseManager()