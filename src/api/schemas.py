from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class ChatRequest(BaseModel):
    user_input: str = Field(..., description="用户输入")
    user_id: Optional[str] = Field("unknown", description="用户ID")
    session_id: Optional[str] = Field(None, description="会话ID")
    stream: Optional[bool] = Field(False, description="是否流式输出")
    messages: Optional[List[Dict[str, str]]] = Field(None, description="历史消息列表")


class ChatResponse(BaseModel):
    status: str = Field(..., description="状态: completed/error")
    answer: str = Field("", description="回答内容")
    session_id: str = Field(..., description="会话ID")
    usage: Dict[str, Any] = Field({}, description="使用统计")


class StreamChatResponse(BaseModel):
    chunk: str = Field(..., description="流式输出内容")
    session_id: str = Field(..., description="会话ID")


class SessionRequest(BaseModel):
    user_id: Optional[str] = Field("unknown", description="用户ID")


class SessionResponse(BaseModel):
    session_id: str = Field(..., description="会话ID")
    user_id: str = Field(..., description="用户ID")
    created_at: str = Field(..., description="创建时间")


class MemoryRequest(BaseModel):
    user_id: str = Field(..., description="用户ID")
    session_id: Optional[str] = Field(None, description="会话ID")


class MemoryResponse(BaseModel):
    user_memory: List[Dict[str, Any]] = Field([], description="用户记忆")
    dialog_history: List[Dict[str, Any]] = Field([], description="对话历史")


class HealthResponse(BaseModel):
    status: str = Field("healthy", description="服务状态")
    version: str = Field("1.0.0", description="版本号")