"""基于LangGraph的状态机引擎"""
from typing import Dict, Any, Optional, List, Generator
from enum import Enum
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import json

class State(Enum):
    """Agent状态枚举"""
    INIT = "INIT"
    UNDERSTAND = "UNDERSTAND"
    RETRIEVING = "RETRIEVING"
    TOOL_CALL = "TOOL_CALL"
    WAIT_USER = "WAIT_USER"
    GENERATING = "GENERATING"
    DONE = "DONE"
    ERROR = "ERROR"

def create_initial_state(user_input: str = "", user_id: str = "", session_id: str = "", stream: bool = False, context_memory: str = "") -> Dict[str, Any]:
    """创建初始状态字典"""
    return {
        "user_input": user_input,
        "user_id": user_id,
        "session_id": session_id,
        "context": "",
        "context_memory": context_memory,
        "retrieved_docs": [],
        "tool_result": {},
        "answer": "",
        "status": "running",
        "error_message": "",
        "needs_retrieval": False,
        "needs_tool": False,
        "needs_clarification": False,
        "answer_generated": False,
        "retrieval_error": False,
        "generation_error": False,
        "tool_error": False,
        "stream": stream
    }


class LangGraphStateMachine:
    """基于LangGraph的状态机引擎"""
    
    def __init__(self):
        self.workflow = self._build_workflow()
        self.checkpointer = MemorySaver()
        self.app = self.workflow.compile(checkpointer=self.checkpointer)
    
    def _build_workflow(self) -> StateGraph:
        """构建工作流图"""
        workflow = StateGraph(dict)
        
        workflow.add_node(State.INIT.value, self._init_node)
        workflow.add_node(State.UNDERSTAND.value, self._understand_node)
        workflow.add_node(State.RETRIEVING.value, self._retrieving_node)
        workflow.add_node(State.TOOL_CALL.value, self._tool_call_node)
        workflow.add_node(State.WAIT_USER.value, self._wait_user_node)
        workflow.add_node(State.GENERATING.value, self._generating_node)
        workflow.add_node(State.DONE.value, self._done_node)
        workflow.add_node(State.ERROR.value, self._error_node)
        
        workflow.set_entry_point(State.INIT.value)
        
        workflow.add_edge(State.INIT.value, State.UNDERSTAND.value)
        
        workflow.add_conditional_edges(
            State.UNDERSTAND.value,
            self._decide_next_step,
            {
                State.RETRIEVING.value: State.RETRIEVING.value,
                State.TOOL_CALL.value: State.TOOL_CALL.value,
                State.WAIT_USER.value: State.WAIT_USER.value,
                State.GENERATING.value: State.GENERATING.value,
                State.ERROR.value: State.ERROR.value
            }
        )
        
        workflow.add_conditional_edges(
            State.RETRIEVING.value,
            self._check_retrieval_result,
            {
                State.GENERATING.value: State.GENERATING.value,
                State.ERROR.value: State.ERROR.value
            }
        )
        
        workflow.add_conditional_edges(
            State.TOOL_CALL.value,
            self._check_tool_result,
            {
                State.GENERATING.value: State.GENERATING.value,
                State.WAIT_USER.value: State.WAIT_USER.value,
                State.ERROR.value: State.ERROR.value
            }
        )
        
        workflow.add_edge(State.WAIT_USER.value, State.UNDERSTAND.value)
        
        workflow.add_conditional_edges(
            State.GENERATING.value,
            self._check_generation_result,
            {
                State.DONE.value: State.DONE.value,
                State.ERROR.value: State.ERROR.value
            }
        )
        
        workflow.add_edge(State.DONE.value, END)
        
        workflow.add_edge(State.ERROR.value, END)
        
        return workflow
    
    def _init_node(self, state: Dict) -> Dict:
        """初始态节点"""
        print(f"[状态机] 进入初始态: {state.get('session_id')}")
        return state
    
    def _understand_node(self, state: Dict) -> Dict:
        """理解意图节点"""
        print(f"[状态机] 理解意图: {state.get('user_input')}")
        
        user_input = state.get("user_input", "")
        
        if "【图片" in user_input or "图片内容" in user_input:
            print(f"[状态机] 检测到多模态输入，跳过RAG检索")
            state["needs_retrieval"] = False
            state["needs_tool"] = False
            state["needs_clarification"] = False
            return state
        
        if "天气" in user_input or "气温" in user_input:
            state["needs_tool"] = True
            print(f"[状态机] 检测到天气查询请求")
        elif any(keyword in user_input for keyword in ["生成图片", "画一幅", "画一张", "画个", "帮我画", "生成一幅", "生成一张", "生成个", "创作图片", "创作一幅", "创作一张"]):
            state["needs_tool"] = True
            print(f"[状态机] 检测到图片生成请求")
        elif any(keyword in user_input for keyword in ["资料", "文档", "知识库", "查找", "搜索", "查询", "谁", "什么", "哪里", "何时", "如何", "为什么"]):
            state["needs_retrieval"] = True
            print(f"[状态机] 检测到需要知识检索的关键词")
        elif len(user_input) > 10 and ("？" in user_input or "?" in user_input):
            state["needs_retrieval"] = True
            print(f"[状态机] 较长的问题，进行RAG检索")
        elif "？" in user_input and len(user_input) < 10:
            state["needs_clarification"] = True
        else:
            state["needs_retrieval"] = True
            print(f"[状态机] 默认进行RAG检索")
        
        return state
    
    def _decide_next_step(self, state: Dict) -> str:
        """决定下一步"""
        if state.get("needs_retrieval"):
            return State.RETRIEVING.value
        elif state.get("needs_tool"):
            return State.TOOL_CALL.value
        elif state.get("needs_clarification"):
            return State.WAIT_USER.value
        else:
            return State.GENERATING.value
    
    def _retrieving_node(self, state: Dict) -> Dict:
        """检索知识节点"""
        print(f"[状态机] 检索知识: {state.get('user_input')}")
        
        try:
            from src.rag.retriever import retriever
            from src.rag.reranker import reranker
            
            retrieved_docs = retriever.retrieve(state.get("user_input", ""), k=3)
            print(f"[状态机] 检索到 {len(retrieved_docs)} 个文档")
            
            if retrieved_docs:
                reranked_docs = reranker.rerank(state.get("user_input", ""), retrieved_docs, top_k=3)
                state["retrieved_docs"] = reranked_docs
                state["retrieval_error"] = False
            else:
                state["retrieved_docs"] = []
                state["retrieval_error"] = True
                
        except Exception as e:
            print(f"[状态机] 检索失败: {e}")
            state["retrieval_error"] = True
            state["error_message"] = str(e)
        
        return state
    
    def _check_retrieval_result(self, state: Dict) -> str:
        """检查检索结果"""
        if state.get("retrieval_error"):
            return State.ERROR.value
        return State.GENERATING.value
    
    def _tool_call_node(self, state: Dict) -> Dict:
        """调用工具节点"""
        print(f"[状态机] 调用工具: {state.get('user_input')}")
        
        try:
            from src.tools import tool_executor
            
            user_input = state.get("user_input", "")
            
            # 判断调用哪种工具
            if self._is_image_generation_request(user_input):
                # 图片生成请求
                prompt = self._extract_image_prompt(user_input)
                tool_result = tool_executor.execute_tool("generate_image", {"prompt": prompt})
                print(f"[状态机] 图片生成工具调用成功: {tool_result}")
            else:
                # 天气查询请求（默认）
                # 从用户输入中提取城市名
                city_names = ["北京", "上海", "广州", "深圳", "杭州", "成都", "重庆", "武汉", "西安", "南京"]
                city = None
                for name in city_names:
                    if name in user_input:
                        city = name
                        break
                
                # 如果没有找到城市，使用默认值
                if not city:
                    city = "北京"
                
                # 调用天气工具
                tool_result = tool_executor.execute_tool("get_weather", {"city": city, "date": "今天"})
                print(f"[状态机] 天气工具调用成功: {tool_result}")
            
            state["tool_result"] = tool_result
            state["tool_error"] = False
            
        except Exception as e:
            print(f"[状态机] 工具调用失败: {e}")
            state["tool_error"] = True
            state["error_message"] = str(e)
        
        return state
    
    def _is_image_generation_request(self, user_input: str) -> bool:
        """判断是否为图片生成请求"""
        image_keywords = ["生成图片", "画一幅", "画一张", "画个", "帮我画", "生成一幅", "生成一张", "生成个", "创作图片", "创作一幅", "创作一张"]
        return any(keyword in user_input for keyword in image_keywords)
    
    def _extract_image_prompt(self, user_input: str) -> str:
        """从用户输入中提取图片描述"""
        # 只移除触发词，保留"生成"等词
        image_triggers = ["帮我画", "帮我"]
        
        # 移除触发词，保留描述部分
        prompt = user_input
        for trigger in image_triggers:
            prompt = prompt.replace(trigger, "").strip()
        
        # 如果提取后为空，使用原输入
        if not prompt:
            prompt = user_input
        
        return prompt
    
    def _check_tool_result(self, state: Dict) -> str:
        """检查工具调用结果"""
        if state.get("tool_error"):
            return State.ERROR.value
        return State.GENERATING.value
    
    def _wait_user_node(self, state: Dict) -> Dict:
        """等待用户输入节点"""
        print(f"[状态机] 等待用户输入")
        state["needs_clarification"] = False
        return state
    
    def _generating_node(self, state: Dict) -> Dict:
        """生成回答节点"""
        print(f"[状态机] 生成回答")
        
        try:
            from src.agent.model_engine import model_engine
            from src.rag.prompt_builder import prompt_builder
            
            user_input = state.get("user_input", "")
            stream = state.get("stream", False)
            context_memory = state.get("context_memory", "")
            retrieved_docs = state.get("retrieved_docs", [])
            
            print(f"[状态机] 检索到的文档数: {len(retrieved_docs)}")
            
            if "【图片" in user_input or "图片内容" in user_input:
                print(f"[状态机] 多模态输入，直接生成回答")
                user_content = f"""请根据用户提供的图片内容回答问题：

{user_input}

请提供详细、准确的回答。"""
            else:
                user_content = prompt_builder.build_prompt(user_input, retrieved_docs)
            
            # 提取RAG检索到的文档内容
            rag_content = ""
            if retrieved_docs:
                # 只提取参考资料部分
                references = []
                for i, doc in enumerate(retrieved_docs):
                    text = doc.get('text', '')
                    title = doc.get('metadata', {}).get('title', f'文档{i+1}')
                    references.append(f"{i+1}. [{title}]\n{text}")
                rag_content = "\n".join(references)
                print(f"[状态机] RAG检索到的参考资料: {len(rag_content)} 字符")
            
            # 检查是否有图片生成请求并调用工具
            tool_result_str = ""
            if any(keyword in user_input for keyword in ["生成图片", "画一幅", "画一张", "画个", "帮我画", "生成一幅", "生成一张", "生成个", "创作图片", "创作一幅", "创作一张"]):
                print(f"[状态机] 检测到图片生成请求")
                from src.tools import tool_executor
                
                # 提取图片描述
                image_triggers = ["帮我画", "帮我"]
                prompt = user_input
                for trigger in image_triggers:
                    prompt = prompt.replace(trigger, "").strip()
                
                # 调用图片生成工具
                tool_result = tool_executor.execute_tool("generate_image", {"prompt": prompt})
                print(f"[状态机] 图片生成工具调用结果: {tool_result}")
                
                result_data = tool_result.get('result', tool_result)
                if result_data.get("status") == "success":
                    tool_result_str = f"图片生成成功！\nURL: {result_data['url']}\n描述: {result_data.get('prompt', '')}\n尺寸: {result_data.get('size', '')}\n风格: {result_data.get('style', '')}"
                else:
                    tool_result_str = f"图片生成失败: {result_data.get('message', '未知错误')}"
            
            if context_memory:
                # 包含历史对话、工具结果和RAG检索结果
                user_content = f"""根据历史对话、工具结果和参考资料回答当前问题：

【历史对话】
{context_memory}

【当前问题】
{user_input}

【工具结果】
{tool_result_str if tool_result_str else '无'}

【参考资料】
{rag_content if rag_content else '无'}

【回答要求】
1. 请根据历史对话、工具结果和参考资料内容，准确回答用户的当前问题
2. 如果工具结果中有答案，请优先使用工具结果中的信息
3. 如果参考资料中有答案，请使用参考资料中的信息回答
4. 如果都没有相关信息，请直接说"根据现有资料无法回答"，不要编造答案
5. 如果工具结果中有图片URL,请直接将URL返回给用户,并且说这就是你通过调用工具生成的图片，而不是说你无法生成图片，不要省略任何信息"""
            else:
                # 只有工具结果和RAG检索结果，没有历史对话
                user_content = f"""请根据工具结果和参考资料回答用户的问题：

【用户问题】
{user_input}

【工具结果】
{tool_result_str if tool_result_str else '无'}

【参考资料】
{rag_content if rag_content else '无'}

【回答要求】
1. 请根据工具结果和参考资料内容，准确回答用户的问题
2. 如果工具结果中有答案，请优先使用工具结果中的信息
3. 如果参考资料中有答案，请使用参考资料中的信息回答
4. 如果都没有相关信息，请直接说"根据现有资料无法回答"，不要编造答案"""
            
            messages = [
                {
                    "role": "system",
                    "content": self._get_system_prompt()
                },
                {
                    "role": "user",
                    "content": user_content
                }
            ]
            
            print(f"[状态机] 消息结构: {len(messages)} 条消息")
            
            request = {
                "model": "local_api",
                "messages": messages,
                "stream": stream,
                "user_id": state.get("user_id", "unknown"),
                "add_system_prompt": False
            }
            
            response = model_engine.generate(request)
            
            if stream and response.get("stream"):
                state["answer"] = response.get("content", "")
            else:
                state["answer"] = response.get("content", "")
            
            state["answer_generated"] = True
            state["generation_error"] = False
            
        except Exception as e:
            print(f"[状态机] 生成失败: {e}")
            state["generation_error"] = True
            state["error_message"] = str(e)
        
        return state
    
    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        try:
            with open("src/prompt/system_prompt.txt", "r", encoding="utf-8") as f:
                system_prompt = f.read().strip()
            
            system_prompt = system_prompt.replace("<|im_start|>system", "").replace("<|im_end|>", "").strip()
            return system_prompt
        except Exception as e:
            print(f"[状态机] 读取系统提示词失败: {e}")
            return "你是灰之魔女伊蕾娜，一位游历诸国、见多识广的旅行者。"
    
    def _check_generation_result(self, state: Dict) -> str:
        """检查生成结果"""
        if state.get("generation_error"):
            return State.ERROR.value
        return State.DONE.value
    
    def _done_node(self, state: Dict) -> Dict:
        """任务完成节点"""
        print(f"[状态机] 任务完成")
        state["status"] = "completed"
        return state
    
    def _error_node(self, state: Dict) -> Dict:
        """异常/兜底节点"""
        print(f"[状态机] 异常状态: {state.get('error_message')}")
        state["status"] = "error"
        if not state.get("answer"):
            state["answer"] = "抱歉，处理过程中遇到了问题，请稍后重试。"
        return state
    
    def run(self, user_input: str, user_id: str = "unknown", session_id: str = "default", stream: bool = False, context_memory: str = "") -> Dict[str, Any]:
        """运行状态机"""
        initial_state = create_initial_state(user_input, user_id, session_id, stream, context_memory)
        
        config = {"configurable": {"thread_id": session_id}}
        
        try:
            final_state = None
            for state in self.app.stream(initial_state, config=config):
                final_state = state
            
            if final_state:
                last_state = list(final_state.values())[-1]
                return {
                    "status": last_state.get("status", "error"),
                    "answer": last_state.get("answer", ""),
                    "error_message": last_state.get("error_message", ""),
                    "retrieved_docs": last_state.get("retrieved_docs", []),
                    "tool_result": last_state.get("tool_result", {}),
                    "stream": stream
                }
            
            return {"status": "error", "answer": "执行失败"}
            
        except Exception as e:
            print(f"[状态机] 运行失败: {e}")
            return {"status": "error", "answer": f"执行失败: {str(e)}"}
    
    def run_stream(self, user_input: str, user_id: str = "unknown", session_id: str = "default", context_memory: str = "") -> Generator[str, None, None]:
        """流式运行状态机"""
        from src.agent.model_engine import model_engine
        from src.rag.prompt_builder import prompt_builder
        
        print(f"[状态机] 流式输出模式 - 已修复版本")
        print(f"[状态机] 用户输入: {user_input}")
        
        try:
            # 检查是否需要调用天气工具
            if "天气" in user_input or "气温" in user_input or "温度" in user_input:
                print(f"[状态机] 检测到天气查询请求")
                
                # 从用户输入中提取城市名
                city_names = ["北京", "上海", "广州", "深圳", "杭州", "成都", "重庆", "武汉", "西安", "南京"]
                city = None
                for name in city_names:
                    if name in user_input:
                        city = name
                        break
                
                if not city:
                    city = "北京"
                
                # 调用天气工具
                from src.tools import tool_executor
                tool_result = tool_executor.execute_tool("get_weather", {"city": city, "date": "今天"})
                print(f"[状态机] 天气工具调用结果: {tool_result}")
                
                # 获取天气数据
                result_data = tool_result.get('result', tool_result)
                
                # 将天气数据拼入提示词，让大模型用伊蕾娜的语气回复
                user_content = f"""请以灰之魔女伊蕾娜的身份回答用户的问题。

【参考资料】
城市: {result_data.get('city', '')}
日期: {result_data.get('date', '')}
天气: {result_data.get('weather', '')}
温度: {result_data.get('temperature', '')}
风速: {result_data.get('wind_speed', '')}

【用户问题】
{user_input}

【回答要求】
1. 以灰之魔女伊蕾娜的身份回答，语气优雅、从容、友善
2. 开头要说"亲爱的旅者"
3. 根据提供的天气数据回答用户的问题
4. 回答要自然、亲切，符合伊蕾娜的性格"""
                
                # 构建消息
                messages = [
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": user_content
                    }
                ]
                
                request = {
                    "model": "local_api",
                    "messages": messages,
                    "stream": True,
                    "user_id": user_id,
                    "add_system_prompt": False
                }
                
                print(f"[状态机] 天气查询 - 发送请求到大模型处理")
                yield from model_engine.generate_stream(request)
                return
            
            # 检查是否有图片生成请求
            is_image_request = any(keyword in user_input for keyword in ["生成图片", "画一幅", "画一张", "画个", "帮我画", "生成一幅", "生成一张", "生成个", "创作图片", "创作一幅", "创作一张"])
            
            # 检查是否有图片生成请求并调用工具（跳过RAG检索）
            tool_result_str = ""
            if is_image_request:
                print(f"[状态机] 检测到图片生成请求，跳过RAG检索")
                from src.tools import tool_executor
                
                # 提取图片描述
                image_triggers = ["帮我画", "帮我"]
                prompt = user_input
                for trigger in image_triggers:
                    prompt = prompt.replace(trigger, "").strip()
                
                # 调用图片生成工具
                tool_result = tool_executor.execute_tool("generate_image", {"prompt": prompt})
                print(f"[状态机] 图片生成工具调用结果: {tool_result}")
                
                result_data = tool_result.get('result', tool_result)
                if result_data.get("status") == "success":
                    tool_result_str = f"图片生成成功！\nURL: {result_data['url']}\n描述: {result_data.get('prompt', '')}\n尺寸: {result_data.get('size', '')}\n风格: {result_data.get('style', '')}"
                else:
                    tool_result_str = f"图片生成失败: {result_data.get('message', '未知错误')}"
            
            # 只有非图片请求时才进行RAG检索
            retrieved_docs = []
            rag_content = ""
            if not is_image_request:
                if "【图片" in user_input or "图片内容" in user_input:
                    print(f"[状态机] 多模态输入，直接生成回答")
                    user_content = f"""请根据用户提供的图片内容回答问题：

{user_input}

请提供详细、准确的回答。"""
                else:
                    try:
                        from src.rag.retriever import retriever
                        from src.rag.reranker import reranker
                        
                        retrieved_docs = retriever.retrieve(user_input, k=3)
                        print(f"[状态机] 流式检索到 {len(retrieved_docs)} 个文档")
                        
                        if retrieved_docs:
                            reranked_docs = reranker.rerank(user_input, retrieved_docs, top_k=3)
                            user_content = prompt_builder.build_prompt(user_input, reranked_docs)
                        else:
                            user_content = f"""请回答用户的问题：

{user_input}

请提供准确、有用的回答。"""
                    except Exception as e:
                        print(f"[状态机] RAG检索失败，使用直接回答: {e}")
                        user_content = f"""请回答用户的问题：

{user_input}

请提供准确、有用的回答。"""
            
                # 提取RAG检索到的文档内容
                if retrieved_docs:
                    # 只提取参考资料部分
                    references = []
                    for i, doc in enumerate(retrieved_docs):
                        text = doc.get('text', '')
                        title = doc.get('metadata', {}).get('title', f'文档{i+1}')
                        references.append(f"{i+1}. [{title}]\n{text}")
                    rag_content = "\n".join(references)
                    print(f"[状态机] RAG检索到的参考资料: {len(rag_content)} 字符")
            
            if context_memory:
                # 包含历史对话、工具结果和RAG检索结果
                user_content = f"""根据历史对话、工具结果和参考资料回答当前问题：

【历史对话】
{context_memory}

【当前问题】
{user_input}

【工具结果】
{tool_result_str if tool_result_str else '无'}

【参考资料】
{rag_content if rag_content else '无'}

【回答要求】
1. 请根据历史对话、工具结果和参考资料内容，准确回答用户的当前问题
2. 如果工具结果中有答案，请优先使用工具结果中的信息
3. 如果参考资料中有答案，请使用参考资料中的信息回答
4. 如果都没有相关信息，请直接说"根据现有资料无法回答"，不要编造答案"""
            else:
                # 只有工具结果和RAG检索结果，没有历史对话
                user_content = f"""请根据工具结果和参考资料回答用户的问题：

【用户问题】
{user_input}

【工具结果】
{tool_result_str if tool_result_str else '无'}

【参考资料】
{rag_content if rag_content else '无'}

【回答要求】
1. 请根据工具结果和参考资料内容，准确回答用户的问题
2. 如果工具结果中有答案，请优先使用工具结果中的信息
3. 如果参考资料中有答案，请使用参考资料中的信息回答
4. 如果都没有相关信息，请直接说"根据现有资料无法回答"，不要编造答案"""
            
            messages = [
                {
                    "role": "system",
                    "content": self._get_system_prompt()
                },
                {
                    "role": "user",
                    "content": user_content
                }
            ]
            
            print(f"[状态机] 流式消息结构: {len(messages)} 条消息")
            
            request = {
                "model": "local_api",
                "messages": messages,
                "stream": True,
                "user_id": user_id,
                "add_system_prompt": False
            }
            
            print(f"[状态机] 发送请求 - 消息数: {len(request['messages'])}")
            print(f"[状态机] 消息1角色: {request['messages'][0]['role']}")
            print(f"[状态机] 消息1内容长度: {len(request['messages'][0]['content'])}")
            if len(request['messages']) > 1:
                print(f"[状态机] 消息2角色: {request['messages'][1]['role']}")
            
            yield from model_engine.generate_stream(request)
            
        except Exception as e:
            print(f"[状态机] 流式运行失败: {e}")
            yield f"执行失败: {str(e)}"
    
    def get_state_history(self, session_id: str) -> Optional[List[str]]:
        """获取状态历史"""
        try:
            checkpoint = self.checkpointer.get({"configurable": {"thread_id": session_id}})
            if checkpoint:
                return checkpoint.get("history", [])
        except:
            pass
        return None
    
    def reset(self):
        """重置状态机"""
        self.app = self.workflow.compile(checkpointer=self.checkpointer)


langgraph_state_machine = LangGraphStateMachine()