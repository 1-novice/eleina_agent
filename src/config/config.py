import os


class Settings:
    def __init__(self):
        # Model Configuration
        self.model_type = os.getenv('MODEL_TYPE', 'local_api')
        self.local_model_path = os.getenv('LOCAL_MODEL_PATH', r"D:\qwenmodel")
        self.lora_path = os.getenv('LORA_PATH', r"D:\LLaMA-Factory\saves\Qwen2.5-7B-Instruct\lora\train_2026-04-06-15-47-06")
        self.local_api_url = os.getenv('LOCAL_API_URL', "http://127.0.0.1:8000/v1/chat/completions")
        
        # API Keys
        self.openai_api_key = os.getenv('OPENAI_API_KEY', None)
        # 支持DASHSCOPE_API_KEY或QIANWEN_API_KEY（兼容旧配置）
        self.dashscope_api_key = os.getenv('DASHSCOPE_API_KEY') or os.getenv('QIANWEN_API_KEY', None)
        self.baidu_api_key = os.getenv('BAIDU_API_KEY', None)
        self.qianwen_api_key = os.getenv('QIANWEN_API_KEY', '')
        
        # Vector Database
        self.vector_db_type = os.getenv('VECTOR_DB_TYPE', "chromadb")
        self.chromadb_path = os.getenv('CHROMADB_PATH', "./vector_db")
        self.milvus_host = os.getenv('MILVUS_HOST', "localhost")
        self.milvus_port = int(os.getenv('MILVUS_PORT', "19530"))
        
        # Neo4j Graph Database
        self.neo4j_uri = os.getenv('NEO4J_URI', "bolt://localhost:7687")
        self.neo4j_user = os.getenv('NEO4J_USER', "neo4j")
        self.neo4j_password = os.getenv('NEO4J_PASSWORD', "password")
        
        # Redis
        self.redis_url = os.getenv('REDIS_URL', "redis://localhost:6379/0")
        
        # API Configuration
        self.api_host = os.getenv('API_HOST', "0.0.0.0")
        self.api_port = int(os.getenv('API_PORT', "8000"))
        
        # Security
        self.secret_key = os.getenv('SECRET_KEY', "your-secret-key-here")
        
        # Monitoring
        self.langsmith_tracing = os.getenv('LANGSMITH_TRACING', "false").lower() == "true"
        self.langsmith_api_key = os.getenv('LANGSMITH_API_KEY', None)
        
        # Tools Configuration
        self.enable_search_tool = os.getenv('ENABLE_SEARCH_TOOL', "true").lower() == "true"
        self.enable_file_tool = os.getenv('ENABLE_FILE_TOOL', "true").lower() == "true"
        self.enable_code_execution = os.getenv('ENABLE_CODE_EXECUTION', "false").lower() == "true"
        self.enable_weather_tool = os.getenv('ENABLE_WEATHER_TOOL', "true").lower() == "true"
        
        # Open-Meteo API
        self.open_meteo_base_url = os.getenv('OPEN_METEO_BASE_URL', "https://api.open-meteo.com/v1")
        
        
        # Logging
        self.log_level = os.getenv('LOG_LEVEL', "INFO")


settings = Settings()