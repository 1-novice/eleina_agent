from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from src.api.schemas import (
    ChatRequest, ChatResponse, SessionRequest, SessionResponse,
    MemoryRequest, MemoryResponse, HealthResponse
)
from src.agent.execution_controller import execution_controller
from src.components.session_manager import session_manager
from src.memory.memory_manager import memory_manager
from datetime import datetime

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        session_id = request.session_id or session_manager.create_session(request.user_id)
        
        context = {
            "user_id": request.user_id,
            "session_id": session_id,
            "stream": False
        }
        
        # 如果前端传递了历史消息，将其添加到上下文中
        if request.messages and len(request.messages) > 1:
            context["history_messages"] = request.messages[:-1]  # 排除当前用户输入
        
        result = execution_controller.execute(request.user_input, context)
        
        return ChatResponse(
            status=result.get("status", "error"),
            answer=result.get("answer", ""),
            session_id=session_id,
            usage=result.get("usage", {})
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    try:
        session_id = request.session_id or session_manager.create_session(request.user_id)
        print(f"[API] 会话ID: {session_id}, 用户ID: {request.user_id}, 传入的session_id: {request.session_id}")
        
        context = {
            "user_id": request.user_id,
            "session_id": session_id,
            "stream": True
        }
        
        # 如果前端传递了历史消息，将其添加到上下文中
        if request.messages and len(request.messages) > 1:
            context["history_messages"] = request.messages[:-1]  # 排除当前用户输入
            print(f"[API] 前端传递了 {len(request.messages)-1} 条历史消息")
        
        import asyncio
        
        async def generate():
            import time
            start_time = time.time()
            data_received = False
            
            # 立即发送session_id
            yield f"data: {{\"type\":\"session\",\"session_id\":\"{session_id}\"}}\n\n"
            
            # 创建队列用于心跳消息
            heartbeat_queue = asyncio.Queue()
            
            # 启动心跳协程
            async def heartbeat():
                nonlocal data_received
                while True:
                    await asyncio.sleep(2)
                    if not data_received:
                        await heartbeat_queue.put(f"data: {{\"type\":\"heartbeat\",\"time\":{time.time()}}}\n\n")
            
            # 创建心跳任务
            heartbeat_task = asyncio.create_task(heartbeat())
            
            try:
                # 处理流式响应
                for chunk in execution_controller.execute_stream(request.user_input, context):
                    data_received = True
                    print(f"[API] 收到数据块，长度: {len(chunk)}")
                    yield f"data: {{\"type\":\"content\",\"content\":\"{chunk}\"}}\n\n"
                    
                    # 强制刷新缓冲区
                    await asyncio.sleep(0)
            finally:
                heartbeat_task.cancel()
                try:
                    await heartbeat_task
                except asyncio.CancelledError:
                    pass
            
            print(f"[API] 流式响应完成，总耗时: {time.time() - start_time:.2f}秒")
        
        return StreamingResponse(
            generate(), 
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # 禁用nginx缓冲
            }
        )
    except Exception as e:
        print(f"[API] 流式响应错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/session", response_model=SessionResponse)
async def create_session(request: SessionRequest):
    try:
        session_id = session_manager.create_session(request.user_id)
        return SessionResponse(
            session_id=session_id,
            user_id=request.user_id,
            created_at=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    try:
        session_info = session_manager.get_session(session_id)
        if not session_info:
            raise HTTPException(status_code=404, detail="会话不存在")
        return session_info
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    try:
        success = session_manager.delete_session(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="会话不存在")
        return {"status": "success", "message": "会话已删除"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/memory", response_model=MemoryResponse)
async def get_memory(request: MemoryRequest):
    try:
        user_memory = memory_manager.retriever.get_user_memory(request.user_id)
        dialog_history = []
        if request.session_id:
            dialog_history = memory_manager.retriever.get_dialog_history(request.session_id)
        
        return MemoryResponse(
            user_memory=user_memory,
            dialog_history=dialog_history
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse()