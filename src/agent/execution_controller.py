"""执行控制器 - 整合状态管理组件"""
from typing import Dict, List, Optional, Any, Generator
import os
import time
import threading

from src.agent.model_engine import model_engine
from src.agent.intent_parser import intent_parser
from src.agent.reasoning_engine import reasoning_engine
from src.tools import tool_registry, tool_selector, param_parser, tool_executor, result_formatter, security_gateway, tool_callback
from src.skill import intent_registry as skill_intent_registry, intent_recognizer, skill_orchestrator, slot_filling, skill_tool_router, skill_state_manager
from src.config.config import settings
from src.memory.memory_manager import memory_manager

from src.components import (
    session_manager,
    langgraph_state_machine,
    task_progress_manager,
    slot_filler,
    context_compressor,
    interrupt_controller
)


class ExecutionController:
    def __init__(self):
        pass
    
    def execute(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行用户请求 - 使用LangGraph状态机"""
        user_id = context.get("user_id", "unknown")
        session_id = context.get("session_id", "default")
        stream = context.get("stream", False)
        
        print(f"[执行控制器] 开始处理请求")
        
        # 如果前端传递了历史消息，使用它们构建上下文记忆
        history_messages = context.get("history_messages", [])
        if history_messages:
            print(f"[执行控制器] 使用前端传递的 {len(history_messages)} 条历史消息")
            context_memory_parts = ["【历史对话】"]
            for msg in history_messages:
                role = msg.get('role')
                content = msg.get('content')
                if role == 'user':
                    context_memory_parts.append(f"用户: {content}")
                elif role == 'assistant':
                    context_memory_parts.append(f"助手: {content}")
            context_memory = "\n".join(context_memory_parts)
        else:
            # 否则从内存中获取
            context_memory = memory_manager.get_context_memory(user_id, session_id, max_turns=5)
        
        print(f"[执行控制器] 上下文记忆长度: {len(context_memory)}")
        print(f"[执行控制器] 上下文记忆包含历史对话: {'历史对话' in context_memory}")
        
        result = langgraph_state_machine.run(user_input, user_id, session_id, stream, context_memory)
        
        if result.get("answer"):
            memory_manager.writer.write_dialog_memory(session_id, "assistant", result["answer"])
        
        if result is None:
            return {"status": "error", "message": "状态机执行失败"}
        
        if result.get("status") == "completed":
            return {
                "status": "completed",
                "answer": result.get("answer", ""),
                "rag_result": result,
                "usage": {},
                "stream": stream
            }
        elif result.get("status") == "error":
            return {
                "status": "error",
                "message": result.get("error_message", "")
            }
        
        return result
    
    def execute_stream(self, user_input: str, context: Dict[str, Any]) -> Generator[str, None, None]:
        """流式执行用户请求"""
        user_id = context.get("user_id", "unknown")
        session_id = context.get("session_id", "default")
        
        print(f"[执行控制器] 开始流式处理请求 - 已修复版本")
        print(f"[执行控制器] 用户输入: {user_input}")
        
        # 如果前端传递了历史消息，使用它们构建上下文记忆
        history_messages = context.get("history_messages", [])
        if history_messages:
            print(f"[执行控制器] 使用前端传递的 {len(history_messages)} 条历史消息")
            context_memory_parts = ["【历史对话】"]
            for msg in history_messages:
                role = msg.get('role')
                content = msg.get('content')
                if role == 'user':
                    context_memory_parts.append(f"用户: {content}")
                elif role == 'assistant':
                    context_memory_parts.append(f"助手: {content}")
            context_memory = "\n".join(context_memory_parts)
        else:
            # 否则从内存中获取
            context_memory = memory_manager.get_context_memory(user_id, session_id, max_turns=5)
        
        print(f"[执行控制器] 上下文记忆长度: {len(context_memory)}")
        print(f"[执行控制器] 上下文记忆包含历史对话: {'历史对话' in context_memory}")
        
        full_answer = ""
        for chunk in langgraph_state_machine.run_stream(user_input, user_id, session_id, context_memory):
            full_answer += chunk
            yield chunk
        
        if full_answer:
            memory_manager.writer.write_dialog_memory(session_id, "assistant", full_answer)
    
    def _execute_multistep(self, plan: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        """执行多步任务 - 使用TaskProgressManager"""
        user_id = context.get("user_id", "unknown")
        session_id = context.get("session_id", "default")
        
        task_id = task_progress_manager.create_task(
            intent="multistep_task",
            slots={"plan": plan},
            session_id=session_id,
            total_steps=len(plan)
        )
        
        results = []
        for i, step in enumerate(plan):
            task_progress_manager.set_step(task_id, i + 1, step.get("step", f"步骤{i+1}"), "running")
            
            step_result = self._execute_step(step, context)
            results.append(step_result)
            
            task_progress_manager.set_step(task_id, i + 1, step.get("step", f"步骤{i+1}"), "completed")
            
            if step_result.get("status") == "paused":
                task_progress_manager.pause_task(task_id)
                return {
                    "status": "paused",
                    "current_step": i,
                    "step": step,
                    "result": step_result
                }
        
        task_progress_manager.complete_task(task_id, {"results": results})
        final_result = self._integrate_results(results, context)
        
        return {
            "status": "completed",
            "plan": plan,
            "results": results,
            "final_result": final_result
        }
    
    def _execute_step(self, step: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个步骤"""
        prompt = f"""请执行以下步骤：

{step.get('step', '')}
{step.get('description', '')}

当前上下文：{context}

请提供执行结果。"""
        
        request = {
            "model": settings.model_type,
            "messages": [{
                "role": "user",
                "content": prompt
            }],
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
    
    def _execute_skill(self, skill_intent_result: Dict[str, Any], user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行Skill"""
        session_id = context.get("session_id", "default")
        skill_id = skill_intent_result.get("skill_id")
        
        slots, missing_slots = slot_filling.fill_slots(user_input, skill_id)
        
        if missing_slots:
            questions = slot_filling.generate_clarification_questions(missing_slots, skill_id)
            skill_state_manager.update_state(
                session_id=session_id,
                skill_id=skill_id,
                slots=slots,
                waiting_for_user=True
            )
            return {
                "status": "needs_clarification",
                "questions": questions
            }
        
        orchestration_result = skill_orchestrator.orchestrate(skill_id, slots, context)
        
        if orchestration_result.get("status") == "needs_tool":
            tool_call = orchestration_result.get("tool_call")
            if tool_call:
                tool_result = self._execute_tool(
                    tool_call.get("tool_choice"),
                    tool_call.get("tool_params"),
                    context
                )
                return skill_orchestrator.resume_execution(session_id, tool_result)
        elif orchestration_result.get("status") == "needs_clarification":
            skill_state_manager.update_state(
                session_id=session_id,
                skill_id=skill_id,
                slots=slots,
                waiting_for_user=True
            )
            return orchestration_result
        
        skill_state_manager.clear_state(session_id)
        return orchestration_result
    
    def _continue_skill_execution(self, user_input: str, context: Dict[str, Any], skill_state: Dict[str, Any]) -> Dict[str, Any]:
        """继续执行Skill"""
        session_id = context.get("session_id", "default")
        skill_id = skill_state.get("skill_id")
        existing_slots = skill_state.get("slots", {})
        
        slots, missing_slots = slot_filling.fill_slots(user_input, skill_id, existing_slots)
        
        if missing_slots:
            questions = slot_filling.generate_clarification_questions(missing_slots, skill_id)
            skill_state_manager.update_state(
                session_id=session_id,
                skill_id=skill_id,
                slots=slots,
                waiting_for_user=True
            )
            return {
                "status": "needs_clarification",
                "questions": questions
            }
        
        orchestration_result = skill_orchestrator.orchestrate(skill_id, slots, context)
        
        if orchestration_result.get("status") == "needs_tool":
            tool_call = orchestration_result.get("tool_call")
            if tool_call:
                tool_result = self._execute_tool(
                    tool_call.get("tool_choice"),
                    tool_call.get("tool_params"),
                    context
                )
                result = skill_orchestrator.resume_execution(session_id, tool_result)
                skill_state_manager.clear_state(session_id)
                return result
        elif orchestration_result.get("status") == "needs_clarification":
            skill_state_manager.update_state(
                session_id=session_id,
                skill_id=skill_id,
                slots=slots,
                waiting_for_user=True
            )
            return orchestration_result
        
        skill_state_manager.clear_state(session_id)
        return orchestration_result
    
    def _execute_tool(self, tool_name: str, tool_params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具调用"""
        user_id = context.get("user_id", "unknown")
        session_id = context.get("session_id", "default")
        user_role = context.get("user_role", "user")
        
        validation_result = security_gateway.validate_tool_call(
            tool_name=tool_name,
            params=tool_params,
            user_role=user_role,
            user_id=user_id
        )
        
        if not validation_result["valid"]:
            return {
                "tool": tool_name,
                "params": tool_params,
                "result": validation_result["message"],
                "status": "error"
            }
        
        tool_result = tool_executor.execute_tool(tool_name, validation_result.get("params", tool_params))
        callback_result = tool_callback.callback(tool_result, context)
        tool_callback.sync_state(tool_result, context)
        
        return tool_result
    
    def _direct_answer(self, user_input: str, context: Dict[str, Any], memory_context: str = "") -> Dict[str, Any]:
        """直接回答用户"""
        prompt = f"""请回答用户的问题：

用户输入：{user_input}

记忆上下文：{memory_context}

当前上下文：{context}

请提供准确、有用的回答。"""
        
        request = {
            "model": settings.model_type,
            "messages": [{
                "role": "user",
                "content": prompt
            }],
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
        if isinstance(results, list):
            results_str = "\n".join([f"步骤结果: {str(result)}" for result in results])
        else:
            results_str = str(results)
        
        prompt = f"""请整合以下工具执行结果，生成自然、友好的回答：

工具执行结果：
{results_str}

当前上下文：{context}

请将结果整理成易于理解的自然语言。"""
        
        request = {
            "model": settings.model_type,
            "messages": [{
                "role": "user",
                "content": prompt
            }],
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
    
    def _execute_rag(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行RAG检索"""
        start_time = time.time()
        
        def rag_task():
            try:
                from src.rag.retriever import retriever
                from src.rag.reranker import reranker
                from src.rag.prompt_builder import prompt_builder
                
                print("=== 开始RAG检索 ===")
                print(f"检索相关文档: {user_input}")
                
                retrieved_docs = retriever.retrieve(user_input, k=3)
                print(f"检索结果: {len(retrieved_docs)} 个文档")
                
                if not retrieved_docs:
                    print("知识库中没有找到相关信息")
                    return {"status": "error", "message": "知识库中没有找到相关信息"}
                
                print("开始重排")
                reranked_docs = reranker.rerank(user_input, retrieved_docs, top_k=3)
                print(f"重排结果: {len(reranked_docs)} 个文档")
                
                print("构建上下文")
                prompt = prompt_builder.build_prompt(user_input, reranked_docs)
                
                print("生成回答")
                request = {
                    "model": settings.model_type,
                    "messages": [{
                        "role": "user",
                        "content": prompt
                    }],
                    "stream": context.get("stream", False),
                    "user_id": context.get("user_id", "unknown")
                }
                
                response = model_engine.generate(request)
                
                return {
                    "status": "completed",
                    "answer": response.get("content", ""),
                    "usage": response.get("usage", {})
                }
            except Exception as e:
                print(f"RAG执行失败: {e}")
                import traceback
                traceback.print_exc()
                return {
                    "status": "error",
                    "message": str(e)
                }
        
        result = {"status": "error", "message": "RAG检索超时"}
        
        def target():
            nonlocal result
            result = rag_task()
        
        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        thread.join(timeout=600)
        
        if thread.is_alive():
            print("RAG检索超时，跳过RAG检索")
            return {"status": "timeout", "message": "RAG检索超时"}
        
        return result


execution_controller = ExecutionController()