from typing import Dict, List, Optional, Any
from src.memory import memory_manager


class ToolCallback:
    def __init__(self):
        pass
    
    def callback(self, tool_result: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """工具回调
        
        Args:
            tool_result: 工具执行结果
            context: 上下文信息
            
        Returns:
            Dict[str, Any]: 回调结果
        """
        user_id = context.get("user_id", "unknown")
        session_id = context.get("session_id", "default")
        
        # 写入记忆层
        self._write_to_memory(tool_result, user_id, session_id)
        
        # 构建回调消息
        callback_message = self._build_callback_message(tool_result)
        
        return {
            "tool_result": tool_result,
            "callback_message": callback_message,
            "context": context
        }
    
    def _write_to_memory(self, tool_result: Dict[str, Any], user_id: str, session_id: str):
        """写入记忆层
        
        Args:
            tool_result: 工具执行结果
            user_id: 用户ID
            session_id: 会话ID
        """
        tool_name = tool_result.get("tool", "")
        status = tool_result.get("status", "")
        result = tool_result.get("result", "")
        
        # 写入工具执行历史
        memory_manager.add_memory(
            user_id=user_id,
            memory_type="tool_execution",
            content=f"工具 {tool_name} 执行{status}，结果: {result}",
            source="tool",
            expire_time=None
        )
        
        # 写入对话历史
        if status == "success":
            from src.tools.result_formatter import result_formatter
            formatted_result = result_formatter.format_result(tool_result)
            memory_manager.writer.write_dialog_memory(
                session_id=session_id,
                role="assistant",
                content=f"工具执行结果: {formatted_result}"
            )
    
    def _build_callback_message(self, tool_result: Dict[str, Any]) -> Dict[str, Any]:
        """构建回调消息
        
        Args:
            tool_result: 工具执行结果
            
        Returns:
            Dict[str, Any]: 回调消息
        """
        tool_name = tool_result.get("tool", "")
        status = tool_result.get("status", "")
        result = tool_result.get("result", "")
        
        # 构建回调消息
        callback_message = {
            "role": "tool",
            "name": tool_name,
            "content": str(result)
        }
        
        return callback_message
    
    def sync_state(self, tool_result: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """同步状态
        
        Args:
            tool_result: 工具执行结果
            context: 上下文信息
            
        Returns:
            bool: 是否同步成功
        """
        session_id = context.get("session_id", "default")
        tool_name = tool_result.get("tool", "")
        status = tool_result.get("status", "")
        
        # 更新会话状态
        memory_manager.update_session_memory(
            session_id=session_id,
            key=f"tool_{tool_name}_status",
            value=status
        )
        
        # 更新任务进度
        if status == "success":
            current_task = memory_manager.retriever.get_current_task(session_id)
            if current_task:
                progress = current_task.get("progress", "0%")
                # 简单的进度更新逻辑
                if progress == "0%":
                    new_progress = "50%"
                else:
                    new_progress = "100%"
                
                memory_manager.update_session_memory(
                    session_id=session_id,
                    key="progress",
                    value=new_progress
                )
        
        return True


# 全局工具回调实例
tool_callback = ToolCallback()