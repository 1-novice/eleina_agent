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

def create_initial_state(user_input: str = "", user_id: str = "", session_id: str = "", stream: bool = False) -> Dict[str, Any]:
    """创建初始状态字典"""
    return {
        "user_input": user_input,
        "user_id": user_id,
        "session_id": session_id,
        "context": "",
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
        elif "师傅" in user_input or "老师" in user_input:
            state["needs_retrieval"] = True
        elif "谁" in user_input or "什么" in user_input:
            state["needs_retrieval"] = True
        elif "？" in user_input and len(user_input) < 10:
            state["needs_clarification"] = True
        
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
            
            tool_result = {
                "tool": "get_weather",
                "result": "模拟天气数据：晴，25度"
            }
            state["tool_result"] = tool_result
            state["tool_error"] = False
            
        except Exception as e:
            print(f"[状态机] 工具调用失败: {e}")
            state["tool_error"] = True
            state["error_message"] = str(e)
        
        return state
    
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
            
            if "【图片" in user_input or "图片内容" in user_input:
                print(f"[状态机] 多模态输入，直接生成回答")
                prompt = f"""请根据用户提供的图片内容回答问题：

{user_input}

请提供详细、准确的回答。"""
            else:
                prompt = prompt_builder.build_prompt(user_input, state.get("retrieved_docs", []))
            
            request = {
                "model": "local_api",
                "messages": [{"role": "user", "content": prompt}],
                "stream": stream,
                "user_id": state.get("user_id", "unknown")
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
    
    def run(self, user_input: str, user_id: str = "unknown", session_id: str = "default", stream: bool = False) -> Dict[str, Any]:
        """运行状态机"""
        initial_state = create_initial_state(user_input, user_id, session_id, stream)
        
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
    
    def run_stream(self, user_input: str, user_id: str = "unknown", session_id: str = "default") -> Generator[str, None, None]:
        """流式运行状态机"""
        from src.agent.model_engine import model_engine
        from src.rag.prompt_builder import prompt_builder
        
        print(f"[状态机] 流式输出模式")
        
        try:
            if "【图片" in user_input or "图片内容" in user_input:
                prompt = f"""请根据用户提供的图片内容回答问题：

{user_input}

请提供详细、准确的回答。"""
            else:
                try:
                    from src.rag.retriever import retriever
                    from src.rag.reranker import reranker
                    
                    retrieved_docs = retriever.retrieve(user_input, k=3)
                    if retrieved_docs:
                        reranked_docs = reranker.rerank(user_input, retrieved_docs, top_k=3)
                        prompt = prompt_builder.build_prompt(user_input, reranked_docs)
                    else:
                        prompt = f"""请回答用户的问题：

{user_input}

请提供准确、有用的回答。"""
                except Exception as e:
                    print(f"[状态机] RAG检索失败，使用直接回答: {e}")
                    prompt = f"""请回答用户的问题：

{user_input}

请提供准确、有用的回答。"""
            
            request = {
                "model": "local_api",
                "messages": [{"role": "user", "content": prompt}],
                "stream": True,
                "user_id": user_id
            }
            
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