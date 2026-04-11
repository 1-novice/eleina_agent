from typing import Dict, List, Optional, Any, Generator
import os
from src.agent.model_engine import model_engine
from src.agent.intent_parser import intent_parser
from src.agent.reasoning_engine import reasoning_engine
from src.tools import tool_registry, tool_selector, param_parser, tool_executor, result_formatter, security_gateway, tool_callback
from src.skill import intent_registry as skill_intent_registry, intent_recognizer, skill_orchestrator, slot_filling, skill_tool_router, skill_state_manager
from src.config.config import settings


class ExecutionController:
    def __init__(self):
        self.execution_history = {}
        self._init_rag()
    
    def _init_rag(self):
        """初始化RAG系统"""
        try:
            # 导入RAG模块
            from src.rag.doc_manager import doc_manager
            from src.rag.doc_parser import doc_parser
            from src.rag.text_chunker import text_chunker
            from src.rag.embedding_engine import embedding_engine
            from src.rag.vector_store import vector_store
            from src.config.config import settings
            
            print("=== 初始化RAG系统 ===")
            
            # 1. 加载PDF文档
            pdf_path = settings.pdf_document_path
            print(f"PDF文档路径: {pdf_path}")
            
            if not pdf_path or not os.path.exists(pdf_path):
                print("警告: PDF文档不存在，RAG功能将不可用")
                return
            
            print(f"处理文档: {pdf_path}")
            
            # 2. 直接从文件路径解析文档
            parse_result = doc_parser.parse_document_by_path(pdf_path)
            print(f"处理结果: {parse_result.get('status')}")
            
            if parse_result.get('status') != 'success':
                print(f"警告: 文档解析失败 - {parse_result.get('message')}, RAG功能将不可用")
                return
            
            content = parse_result.get('content', '')
            if not content:
                print("警告: 文档内容为空，RAG功能将不可用")
                return
            
            # 3. 文本分块
            print("开始文本分块")
            chunks = text_chunker.chunk_text(content, strategy="semantic")
            print(f"分块结果: {len(chunks)} 个分块")
            
            # 4. 向量化
            print("开始向量化")
            embeddings = embedding_engine.embed_batch([chunk.get('text', '') for chunk in chunks])
            print(f"向量化结果: {len(embeddings)} 个向量")
            
            # 5. 存储向量
            print("存储向量")
            
            # 清空旧数据，确保只使用新的PDF内容
            vector_store.clear()
            
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                chunk['vector'] = embedding
                chunk['id'] = f"chunk_{i}"
            
            vector_store.add_batch(chunks)
            vector_store.save()  # 保存到文件
            print("向量存储完成")
            print("=== RAG系统初始化完成 ===")
        except Exception as e:
            print(f"RAG系统初始化失败: {e}")
            import traceback
            traceback.print_exc()
    
    def execute(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行用户请求"""
        user_id = context.get("user_id", "unknown")
        session_id = context.get("session_id", "default")
        request_id = context.get("request_id", f"{user_id}_{session_id}_{hash(user_input)}")
        
        print(f"[执行控制器] 开始处理请求: {request_id}")
        
        # 检查是否正在处理同一请求（防止重复调用）
        if request_id in self.execution_history.get(user_id, {}).get(session_id, {}):
            print(f"[执行控制器] 检测到重复请求，跳过处理: {request_id}")
            return {"status": "error", "message": "请求正在处理中"}
        
        # 初始化执行历史
        if user_id not in self.execution_history:
            self.execution_history[user_id] = {}
        if session_id not in self.execution_history[user_id]:
            self.execution_history[user_id][session_id] = {
                "steps": [],
                "current_step": 0,
                "status": "running"
            }
        
        # 标记请求正在处理
        self.execution_history[user_id][session_id]["current_request"] = request_id
        
        # 记录开始时间
        import time
        start_time = time.time()
        
        try:
            # 首先执行RAG检索
            print("[执行控制器] 开始执行RAG检索")
            rag_result = self._execute_rag(user_input, context)
            
            # 如果RAG检索成功并返回了回答，直接返回（避免重复调用大模型）
            if rag_result and rag_result.get("status") == "completed" and rag_result.get("answer"):
                print(f"[执行控制器] RAG检索成功，直接返回结果，耗时: {(time.time() - start_time):.2f}秒")
                return {
                    "status": "completed",
                    "answer": rag_result.get("answer", ""),
                    "rag_result": rag_result,
                    "usage": rag_result.get("usage", {})
                }
            
            # 从记忆系统获取上下文
            from src.memory import memory_manager
            memory_context = memory_manager.get_context_memory(user_id, session_id)
            
            # 检查是否有正在执行的Skill
            skill_state = skill_state_manager.get_state(session_id)
            if skill_state and skill_state.get("waiting_for_user"):
                # 继续执行Skill
                print("[执行控制器] 继续执行Skill")
                return self._continue_skill_execution(user_input, context, skill_state)
            
            # 识别Skill意图
            skill_intent_result = intent_recognizer.recognize(user_input)
            if not skill_intent_result["is_rejected"]:
                # 执行Skill
                print("[执行控制器] 执行Skill")
                skill_result = self._execute_skill(skill_intent_result, user_input, context)
                # 检查Skill是否需要工具
                if skill_result.get("status") == "needs_tool":
                    # 执行工具调用
                    tool_call = skill_result.get("tool_call")
                    if tool_call:
                        tool_result = self._execute_tool(
                            tool_call.get("tool_choice"),
                            tool_call.get("tool_params"),
                            context
                        )
                        # 恢复执行Skill
                        return skill_orchestrator.resume_execution(session_id, tool_result)
                return skill_result
            
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
                    tool_result = self._execute_tool(thinking_result["tool_choice"], thinking_result["tool_params"], context)
                    # 整合结果
                    return self._integrate_results(tool_result, context)
            
            # 直接回答（如果RAG没有返回结果）
            print("[执行控制器] RAG未返回结果，执行直接回答")
            return self._direct_answer(user_input, context, memory_context)
        except Exception as e:
            print(f"[执行控制器] 执行失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "message": str(e)
            }
        finally:
            # 清除请求标记
            if user_id in self.execution_history and session_id in self.execution_history[user_id]:
                self.execution_history[user_id][session_id].pop("current_request", None)
            print(f"[执行控制器] 请求处理完成，耗时: {(time.time() - start_time):.2f}秒")
    
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
    
    def _execute_skill(self, skill_intent_result: Dict[str, Any], user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行Skill"""
        user_id = context.get("user_id", "unknown")
        session_id = context.get("session_id", "default")
        skill_id = skill_intent_result.get("skill_id")
        
        # 提取槽位
        slots, missing_slots = slot_filling.fill_slots(user_input, skill_id)
        
        # 检查是否需要澄清
        if missing_slots:
            questions = slot_filling.generate_clarification_questions(missing_slots, skill_id)
            # 更新状态
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
        
        # 执行Skill编排
        orchestration_result = skill_orchestrator.orchestrate(skill_id, slots, context)
        
        # 处理编排结果
        if orchestration_result.get("status") == "needs_tool":
            # 执行工具调用
            tool_call = orchestration_result.get("tool_call")
            if tool_call:
                tool_result = self._execute_tool(
                    tool_call.get("tool_choice"),
                    tool_call.get("tool_params"),
                    context
                )
                # 恢复执行
                return skill_orchestrator.resume_execution(session_id, tool_result)
        elif orchestration_result.get("status") == "needs_clarification":
            # 更新状态
            skill_state_manager.update_state(
                session_id=session_id,
                skill_id=skill_id,
                slots=slots,
                waiting_for_user=True
            )
            return orchestration_result
        
        # 清除状态
        skill_state_manager.clear_state(session_id)
        return orchestration_result
    
    def _continue_skill_execution(self, user_input: str, context: Dict[str, Any], skill_state: Dict[str, Any]) -> Dict[str, Any]:
        """继续执行Skill"""
        session_id = context.get("session_id", "default")
        skill_id = skill_state.get("skill_id")
        existing_slots = skill_state.get("slots", {})
        
        # 填充槽位
        slots, missing_slots = slot_filling.fill_slots(user_input, skill_id, existing_slots)
        
        # 检查是否需要澄清
        if missing_slots:
            questions = slot_filling.generate_clarification_questions(missing_slots, skill_id)
            # 更新状态
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
        
        # 执行Skill编排
        orchestration_result = skill_orchestrator.orchestrate(skill_id, slots, context)
        
        # 处理编排结果
        if orchestration_result.get("status") == "needs_tool":
            # 执行工具调用
            tool_call = orchestration_result.get("tool_call")
            if tool_call:
                tool_result = self._execute_tool(
                    tool_call.get("tool_choice"),
                    tool_call.get("tool_params"),
                    context
                )
                # 恢复执行
                result = skill_orchestrator.resume_execution(session_id, tool_result)
                # 清除状态
                skill_state_manager.clear_state(session_id)
                return result
        elif orchestration_result.get("status") == "needs_clarification":
            # 更新状态
            skill_state_manager.update_state(
                session_id=session_id,
                skill_id=skill_id,
                slots=slots,
                waiting_for_user=True
            )
            return orchestration_result
        
        # 清除状态
        skill_state_manager.clear_state(session_id)
        return orchestration_result
    
    def _execute_tool(self, tool_name: str, tool_params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具调用"""
        user_id = context.get("user_id", "unknown")
        session_id = context.get("session_id", "default")
        user_role = context.get("user_role", "user")
        
        # 验证工具调用
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
        
        # 执行工具
        tool_result = tool_executor.execute_tool(tool_name, validation_result.get("params", tool_params))
        
        # 回调处理
        callback_result = tool_callback.callback(tool_result, context)
        
        # 同步状态
        tool_callback.sync_state(tool_result, context)
        
        return tool_result
    
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

请将结果整理成易于理解的自然语言，并确保包含以下详细信息（如果工具执行结果中有的话）：
1. 具体的温度数值
2. 湿度数据
3. 风速信息
4. 天气状况描述
5. 其他相关的天气数据

请以友好、自然的语气回答，让用户能够清晰地了解天气情况。"""
        
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
    
    def _execute_rag(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行RAG检索"""
        import time
        start_time = time.time()
        
        def rag_task():
            try:
                # 导入RAG模块
                from src.rag.retriever import retriever
                from src.rag.reranker import reranker
                from src.rag.prompt_builder import prompt_builder
                from src.config.config import settings
                
                print("=== 开始RAG检索 ===")
                
                # 1. 检索相关文档
                print(f"检索相关文档: {user_input}")
                retrieved_docs = retriever.retrieve(user_input, k=3)
                print(f"检索结果: {len(retrieved_docs)} 个文档")
                
                if not retrieved_docs:
                    print("错误: 知识库中没有找到相关信息")
                    return {"status": "error", "message": "知识库中没有找到相关信息"}
                
                # 2. 重排
                print("开始重排")
                reranked_docs = reranker.rerank(user_input, retrieved_docs, top_k=3)
                print(f"重排结果: {len(reranked_docs)} 个文档")
                
                # 3. 构建上下文
                print("构建上下文")
                prompt = prompt_builder.build_prompt(user_input, reranked_docs)
                
                # 4. 生成回答
                print("生成回答")
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
                
                from src.agent.model_engine import model_engine
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
        
        # 执行RAG任务并检查超时
        import threading
        result = {"status": "error", "message": "RAG检索超时"}
        
        def target():
            nonlocal result
            result = rag_task()
        
        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        thread.join(timeout=600)  # 600秒超时
        
        # 检查是否超时
        if thread.is_alive():
            print("RAG检索超时，跳过RAG检索")
            return {"status": "timeout", "message": "RAG检索超时"}
        
        return result


# 全局执行控制器实例
execution_controller = ExecutionController()