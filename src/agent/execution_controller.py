from typing import Dict, List, Optional, Any, Generator
from src.agent.model_engine import model_engine
from src.agent.intent_parser import intent_parser
from src.agent.reasoning_engine import reasoning_engine
from src.config.config import settings


class ExecutionController:
    def __init__(self):
        self.execution_history = {}
    
    def execute(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行用户请求"""
        user_id = context.get("user_id", "unknown")
        session_id = context.get("session_id", "default")
        
        # 初始化执行历史
        if user_id not in self.execution_history:
            self.execution_history[user_id] = {}
        if session_id not in self.execution_history[user_id]:
            self.execution_history[user_id][session_id] = {
                "steps": [],
                "current_step": 0,
                "status": "running"
            }
        
        # 从记忆系统获取上下文
        from src.memory import memory_manager
        memory_context = memory_manager.get_context_memory(user_id, session_id)
        
        # 解析用户意图
        intent_result = intent_parser.parse(user_input)
        
        # 检查是否需要澄清
        if intent_result["needs_clarification"]:
            return {
                "status": "needs_clarification",
                "questions": intent_result["clarification_questions"]
            }
        
        # 检查是否需要多步执行
        if intent_result["needs_multistep"]:
            # 规划复杂任务
            plan = reasoning_engine.plan(user_input)
            return self._execute_multistep(plan, context)
        
        # 检查是否需要工具
        if intent_result["needs_tool"]:
            # 思考并选择工具
            thinking_result = reasoning_engine.think(user_input, context)
            if thinking_result["tool_choice"]:
                # 执行工具调用
                tool_result = self._execute_tool(thinking_result["tool_choice"], thinking_result["tool_params"])
                # 整合结果
                return self._integrate_results(tool_result, context)
        
        # 直接回答
        return self._direct_answer(user_input, context, memory_context)
    
    def _execute_multistep(self, plan: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        """执行多步任务"""
        user_id = context.get("user_id", "unknown")
        session_id = context.get("session_id", "default")
        
        # 记录执行步骤
        execution_info = self.execution_history[user_id][session_id]
        execution_info["steps"] = plan
        execution_info["current_step"] = 0
        execution_info["status"] = "running"
        
        # 执行步骤
        results = []
        for i, step in enumerate(plan):
            # 更新当前步骤
            execution_info["current_step"] = i
            
            # 执行步骤
            step_result = self._execute_step(step, context)
            results.append(step_result)
            
            # 检查是否需要暂停
            if step_result.get("status") == "paused":
                execution_info["status"] = "paused"
                return {
                    "status": "paused",
                    "current_step": i,
                    "step": step,
                    "result": step_result
                }
        
        # 任务完成
        execution_info["status"] = "completed"
        
        # 整合结果
        final_result = self._integrate_results(results, context)
        return {
            "status": "completed",
            "plan": plan,
            "results": results,
            "final_result": final_result
        }
    
    def _execute_step(self, step: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个步骤"""
        # 构建步骤执行提示词
        prompt = f"""请执行以下步骤：

{step['step']}
{step['description']}

当前上下文：{context}

请提供执行结果。"""
        
        # 调用模型执行步骤
        request = {
            "model": settings.model_type,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "stream": False,
            "user_id": context.get("user_id", "unknown")
        }
        
        try:
            response = model_engine.generate(request)
            return {
                "step": step,
                "result": response.get("content", ""),
                "status": "completed"
            }
        except Exception as e:
            print(f"执行步骤失败: {e}")
            return {
                "step": step,
                "result": "执行步骤失败",
                "status": "completed"
            }
    
    def _execute_tool(self, tool_name: str, tool_params: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具调用"""
        # 模拟工具执行
        # 实际实现中应该调用真实的工具
        return {
            "tool": tool_name,
            "params": tool_params,
            "result": f"工具 {tool_name} 执行成功，参数: {tool_params}",
            "status": "success"
        }
    
    def _direct_answer(self, user_input: str, context: Dict[str, Any], memory_context: str = "") -> Dict[str, Any]:
        """直接回答用户"""
        # 构建回答提示词
        prompt = f"""请回答用户的问题：

用户输入：{user_input}

记忆上下文：{memory_context}

当前上下文：{context}

请提供准确、有用的回答。"""
        
        # 调用模型生成回答
        request = {
            "model": settings.model_type,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "stream": context.get("stream", False),
            "user_id": context.get("user_id", "unknown")
        }
        
        try:
            response = model_engine.generate(request)
            return {
                "status": "completed",
                "answer": response.get("content", ""),
                "usage": response.get("usage", {})
            }
        except Exception as e:
            print(f"直接回答失败: {e}")
            return {
                "status": "completed",
                "answer": "抱歉，我暂时无法处理您的请求，请稍后再试。",
                "usage": {}
            }
    
    def _integrate_results(self, results: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """整合工具执行结果"""
        # 构建整合提示词
        if isinstance(results, list):
            results_str = "\n".join([f"步骤结果: {str(result)}" for result in results])
        else:
            results_str = str(results)
        
        prompt = f"""请整合以下工具执行结果，生成自然、友好的回答：

工具执行结果：
{results_str}

当前上下文：{context}

请将结果整理成易于理解的自然语言。"""
        
        # 调用模型整合结果
        request = {
            "model": settings.model_type,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "stream": False,
            "user_id": context.get("user_id", "unknown")
        }
        
        try:
            response = model_engine.generate(request)
            return {
                "status": "completed",
                "answer": response.get("content", ""),
                "usage": response.get("usage", {})
            }
        except Exception as e:
            print(f"整合结果失败: {e}")
            return {
                "status": "completed",
                "answer": "抱歉，我暂时无法处理您的请求，请稍后再试。",
                "usage": {}
            }
    
    def resume_execution(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """恢复暂停的执行"""
        if user_id not in self.execution_history or session_id not in self.execution_history[user_id]:
            return {
                "status": "error",
                "message": "执行历史不存在"
            }
        
        execution_info = self.execution_history[user_id][session_id]
        if execution_info["status"] != "paused":
            return {
                "status": "error",
                "message": "执行未暂停"
            }
        
        # 继续执行剩余步骤
        plan = execution_info["steps"]
        current_step = execution_info["current_step"]
        
        results = []
        for i in range(current_step, len(plan)):
            step = plan[i]
            step_result = self._execute_step(step, {"user_id": user_id, "session_id": session_id})
            results.append(step_result)
        
        # 任务完成
        execution_info["status"] = "completed"
        
        # 整合结果
        final_result = self._integrate_results(results, {"user_id": user_id, "session_id": session_id})
        return {
            "status": "completed",
            "plan": plan,
            "results": results,
            "final_result": final_result
        }
    
    def get_execution_status(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """获取执行状态"""
        if user_id not in self.execution_history or session_id not in self.execution_history[user_id]:
            return {
                "status": "error",
                "message": "执行历史不存在"
            }
        
        return self.execution_history[user_id][session_id]


# 全局执行控制器实例
execution_controller = ExecutionController()