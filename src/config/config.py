from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Model Configuration
    model_type: str = "local"
    local_model_path: str = "D:\qwenmodel"
    lora_path: str = "D:\LLaMA-Factory\saves\Qwen2.5-7B-Instruct\lora\train_2026-04-06-15-47-06"
    local_api_url: str = "http://localhost:8000/v1/chat/completions"
    
    # API Keys
    openai_api_key: Optional[str] = None
    dashscope_api_key: Optional[str] = None
    baidu_api_key: Optional[str] = None
    
    # Vector Database
    vector_db_type: str = "chromadb"
    chromadb_path: str = "./vector_db"
    milvus_host: str = "localhost"
    milvus_port: int = 19530
    
    # Neo4j Graph Database
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Security
    secret_key: str = "your-secret-key-here"
    
    # Monitoring
    langsmith_tracing: bool = False
    langsmith_api_key: Optional[str] = None
    
    # Tools Configuration
    enable_search_tool: bool = True
    enable_file_tool: bool = True
    enable_code_execution: bool = False
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()