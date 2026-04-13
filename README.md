# Eleina Agent - 全能智能体动漫角色

## 项目简介

Eleina Agent是一个基于本地大模型的工业级智能体系统，具有强大的推理能力、记忆系统和工具调用能力。系统采用模块化设计，支持多种模型接入方式，可通过本地API或直接加载本地模型进行推理。

## 核心功能

### 1. Agent 大脑层

- **大模型调度引擎**：支持本地模型和本地API两种模式，实现模型路由、降级和容错
- **意图识别与任务解析**：自动识别用户意图，抽取槽位信息，判断任务类型
- **决策推理引擎**：实现思考链（CoT）和ReAct模式，支持工具选择和任务规划
- **执行控制引擎**：管理多步执行流程，处理上下文裁剪和结果整合
- **LangGraph状态机**：基于LangGraph实现状态流转，支持复杂工作流

### 2. 用户鉴权与上下文管理

- **用户鉴权中间件**：支持Token认证、会话管理、权限验证
- **请求上下文加载**：每请求独立加载用户信息、权限、工具列表、偏好记忆
- **多用户并发安全**：线程安全设计，无全局用户数据缓存

### 3. 记忆系统

- **短期记忆**：管理对话历史，实现上下文压缩和摘要
- **中期记忆**：保存用户偏好和历史任务进度
- **长期记忆**：存储用户档案和实体记忆，支持向量库和图谱（Neo4j）

### 4. 工具调用系统

- **工具注册中心**：管理工具元数据、权限和限流
- **工具执行引擎**：支持函数调用、API调用和代码执行
- **工具结果解析**：将结构化结果转换为自然语言

### 5. RAG 知识库

- **文档接入与管理**：支持PDF、Word文档上传和管理
- **文档解析与文本提取**：提取文本、表格、标题层级
- **文本分块模块**：支持按段落、语义、标题层级分块
- **向量化引擎**：使用阿里text-embedding-v3模型（1024维度）
- **向量存储层**：支持ChromaDB、Milvus等向量数据库
- **检索引擎**：支持多路召回（向量+关键词）
- **重排模块**：支持API重排和本地重排
- **上下文构建模块**：构建适合LLM处理的上下文

### 6. 数据库管理（MySQL）

- **用户管理**：用户信息、角色、权限管理
- **会话管理**：会话生命周期、上下文存储
- **任务管理**：任务状态、进度、槽位信息
- **配置管理**：Agent配置、工具元数据
- **审计日志**：全链路操作记录

### 7. 安全与合规

- **内容安全**：检测敏感词和恶意指令
- **数据合规**：实现数据脱敏和隐私保护
- **权限系统**：管理用户/角色/工具权限
- **审计日志**：记录全链路操作

### 8. 监控与运维

- **链路追踪**：集成langsmith和Jaeger
- **指标监控**：跟踪响应时长、成功率等
- **日志系统**：记录系统运行状态
- **告警机制**：及时发现和处理异常

## 安装与部署

### 环境要求

- Python 3.9+
- CUDA 11.7+ (推荐，用于加速模型推理)
- MySQL 8.0+
- Redis 7.0+
- 足够的内存和存储空间

### 安装步骤

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd eleina-agent
   ```

2. **创建虚拟环境**
   ```bash
   python -m venv venv
   ```

3. **激活虚拟环境**
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - Linux/MacOS:
     ```bash
     source venv/bin/activate
     ```

4. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```
   或使用Poetry:
   ```bash
   poetry install
   ```

5. **配置环境变量**
   编辑 `.env` 文件：
   ```env
   # Model Configuration
   MODEL_TYPE=local_api
   LOCAL_MODEL_PATH="/path/to/qwen2.5-7B-instruct"
   LOCAL_API_URL=http://localhost:8000/v1/chat/completions
   
   # MySQL Configuration
   MYSQL_HOST=localhost
   MYSQL_PORT=3306
   MYSQL_USER=root
   MYSQL_PASSWORD=your_password
   MYSQL_DATABASE=eleina_agent
   
   # Redis Configuration
   REDIS_URL=redis://localhost:6379/0
   
   # Vector Database
   VECTOR_DB_TYPE=chromadb
   CHROMADB_PATH=./vector_db
   ```

6. **初始化数据库**
   ```bash
   python scripts/init_database.py
   ```

## 使用方法

### 启动系统

```bash
python main.py
```

### 与Agent交互

系统启动后，您可以通过命令行与Agent进行交互：

```
=== 全能智能体动漫角色Agent ===
输入 'exit' 退出
用户: 介绍一下你自己
Agent: 我是一个全能的智能体动漫角色，具有丰富的知识和强大的能力。
```

### API接口

系统提供RESTful API接口：

```bash
POST http://localhost:8000/api/v1/chat
Content-Type: application/json

{
    "user_input": "你好",
    "token": "your_session_token",
    "session_id": "your_session_id"
}
```

### 添加知识库文档

1. **批量添加MD文件**：
   ```bash
   # 清空并重导
   python scripts/batch_add_knowledge.py
   
   # 追加模式
   python scripts/append_knowledge.py
   ```

2. **添加单个文件**：
   将文件放入 `src/rag/knowledge` 目录，运行追加脚本即可。

## 配置说明

### 模型配置

| 模式 | 说明 |
|------|------|
| `local` | 直接加载本地模型文件 |
| `local_api` | 通过本地API服务进行推理 |

### 数据库配置

MySQL用于存储：
- 用户信息、角色、权限
- 会话元数据
- 任务状态
- Agent配置
- 工具元数据
- 结构化记忆
- 审计日志

### 提示词配置

系统提示词存储在 `src/prompt/system_prompt.txt` 文件中。

## 项目结构

```
├── src/
│   ├── agent/              # Agent 大脑层
│   │   ├── model_engine.py         # 大模型调度引擎
│   │   ├── intent_parser.py        # 意图识别
│   │   ├── reasoning_engine.py     # 决策推理引擎
│   │   └── execution_controller.py # 执行控制引擎
│   ├── components/         # 状态管理组件
│   │   ├── langgraph_state_machine.py  # LangGraph状态机
│   │   ├── session_manager.py           # 会话管理
│   │   ├── task_progress_manager.py     # 任务进度管理
│   │   └── context_compressor.py        # 上下文压缩
│   ├── database/           # 数据库管理
│   │   ├── models.py                   # SQLAlchemy模型
│   │   ├── database.py                 # 数据库连接管理
│   │   └── services/                   # 数据库服务
│   │       ├── user_service.py         # 用户服务
│   │       ├── permission_service.py   # 权限服务
│   │       ├── session_service.py      # 会话服务
│   │       └── task_service.py         # 任务服务
│   ├── middleware/         # 中间件
│   │   ├── auth_middleware.py          # 用户鉴权中间件
│   │   └── context_loader.py           # 请求上下文加载器
│   ├── rag/                # RAG知识库
│   │   ├── doc_manager.py              # 文档管理
│   │   ├── doc_parser.py               # 文档解析
│   │   ├── text_chunker.py             # 文本分块
│   │   ├── embedding_engine.py         # 向量化引擎
│   │   ├── vector_store.py             # 向量存储
│   │   ├── retriever.py                # 检索引擎
│   │   └── reranker.py                # 重排模块
│   ├── tools/              # 工具调用系统
│   ├── memory/             # 记忆系统
│   ├── api/                # API服务
│   ├── config/             # 配置管理
│   ├── utils/              # 工具函数
│   └── prompt/             # 提示词管理
├── scripts/                # 脚本
│   ├── init_database.py               # 数据库初始化
│   ├── batch_add_knowledge.py         # 批量添加知识库
│   └── append_knowledge.py            # 追加知识库
├── .env                    # 环境变量配置
├── main.py                 # 主入口
├── pyproject.toml          # 项目依赖
└── README.md               # 项目文档
```

## 开发指南

### 添加新工具

1. 在 `src/tools/` 目录下创建工具实现
2. 在 `src/tools/tool_registry.py` 中注册工具
3. 在数据库中添加工具元数据

### 添加新配置

1. 在 `src/config/config.py` 中添加配置项
2. 在 `.env` 文件中添加环境变量
3. 在数据库 `agent_configs` 表中添加配置记录

### 代码规范

- 遵循PEP 8编码规范
- 使用类型提示
- 添加必要的注释
- 编写单元测试

## 故障排除

### 常见问题

1. **模型初始化失败**：检查模型路径是否正确，CUDA是否可用
2. **数据库连接失败**：检查MySQL服务是否运行，连接参数是否正确
3. **API调用失败**：检查API服务是否运行，URL是否正确
4. **内存不足**：考虑使用4bit量化或切换到local_api模式
5. **权限验证失败**：检查用户角色和权限配置

### 日志查看

系统日志会输出到控制台和 `agent.log` 文件，可通过调整日志级别控制输出详细程度。

## 贡献

欢迎提交Issue和Pull Request，帮助改进Eleina Agent。

## 许可证

MIT License