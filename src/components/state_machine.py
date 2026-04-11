"""状态机引擎 - 管理Agent的状态流转"""
from typing import Dict, Callable, Optional, Any
from enum import Enum
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

class Transition:
    """状态转换"""
    def __init__(self, from_state: State, to_state: State, condition: Optional[Callable] = None):
        self.from_state = from_state
        self.to_state = to_state
        self.condition = condition or (lambda *args, **kwargs: True)

class StateMachine:
    """状态机引擎"""
    
    def __init__(self):
        self.state = State.INIT
        self.transitions: Dict[State, list[Transition]] = {}
        self.state_history: list[State] = []
        self.context: Dict[str, Any] = {}
        self._register_transitions()
    
    def _register_transitions(self):
        """注册状态转换规则"""
        # 初始态 -> 理解意图
        self.add_transition(State.INIT, State.UNDERSTAND)
        
        # 理解意图 -> 检索知识
        self.add_transition(State.UNDERSTAND, State.RETRIEVING, 
                          lambda ctx: ctx.get("need_retrieval", False))
        
        # 理解意图 -> 调用工具
        self.add_transition(State.UNDERSTAND, State.TOOL_CALL,
                          lambda ctx: ctx.get("need_tool", False))
        
        # 理解意图 -> 等待用户输入
        self.add_transition(State.UNDERSTAND, State.WAIT_USER,
                          lambda ctx: ctx.get("need_more_info", False))
        
        # 理解意图 -> 生成回答
        self.add_transition(State.UNDERSTAND, State.GENERATING)
        
        # 检索知识 -> 生成回答
        self.add_transition(State.RETRIEVING, State.GENERATING)
        
        # 检索知识 -> 错误
        self.add_transition(State.RETRIEVING, State.ERROR,
                          lambda ctx: ctx.get("retrieval_error", False))
        
        # 调用工具 -> 生成回答
        self.add_transition(State.TOOL_CALL, State.GENERATING)
        
        # 调用工具 -> 等待用户输入
        self.add_transition(State.TOOL_CALL, State.WAIT_USER,
                          lambda ctx: ctx.get("need_more_info", False))
        
        # 调用工具 -> 错误
        self.add_transition(State.TOOL_CALL, State.ERROR,
                          lambda ctx: ctx.get("tool_error", False))
        
        # 等待用户输入 -> 理解意图
        self.add_transition(State.WAIT_USER, State.UNDERSTAND)
        
        # 生成回答 -> 完成
        self.add_transition(State.GENERATING, State.DONE,
                          lambda ctx: ctx.get("answer_generated", False))
        
        # 生成回答 -> 错误
        self.add_transition(State.GENERATING, State.ERROR,
                          lambda ctx: ctx.get("generation_error", False))
        
        # 任何状态 -> 错误（异常情况）
        self.add_transition(State.INIT, State.ERROR)
        self.add_transition(State.UNDERSTAND, State.ERROR)
        self.add_transition(State.RETRIEVING, State.ERROR)
        self.add_transition(State.TOOL_CALL, State.ERROR)
        self.add_transition(State.WAIT_USER, State.ERROR)
        self.add_transition(State.GENERATING, State.ERROR)
        
        # 错误 -> 初始态（重置）
        self.add_transition(State.ERROR, State.INIT)
        
        # 完成 -> 初始态（新对话）
        self.add_transition(State.DONE, State.INIT)
    
    def add_transition(self, from_state: State, to_state: State, condition: Callable = None):
        """添加状态转换"""
        if from_state not in self.transitions:
            self.transitions[from_state] = []
        self.transitions[from_state].append(Transition(from_state, to_state, condition))
    
    def can_transition(self, to_state: State) -> bool:
        """检查是否可以转换到指定状态"""
        transitions = self.transitions.get(self.state, [])
        for transition in transitions:
            if transition.to_state == to_state:
                return transition.condition(self.context)
        return False
    
    def transition(self, to_state: State, **kwargs) -> bool:
        """执行状态转换"""
        if self.can_transition(to_state):
            self.state_history.append(self.state)
            self.state = to_state
            self.context.update(kwargs)
            return True
        return False
    
    def step(self, **kwargs) -> State:
        """执行一步状态转换"""
        self.context.update(kwargs)
        
        transitions = self.transitions.get(self.state, [])
        for transition in transitions:
            if transition.condition(self.context):
                self.state_history.append(self.state)
                self.state = transition.to_state
                break
        
        return self.state
    
    def reset(self):
        """重置状态机"""
        self.state = State.INIT
        self.state_history = []
        self.context = {}
    
    def get_state(self) -> State:
        """获取当前状态"""
        return self.state
    
    def get_history(self) -> list[State]:
        """获取状态历史"""
        return self.state_history
    
    def get_context(self) -> Dict[str, Any]:
        """获取上下文"""
        return self.context
    
    def save_state(self) -> str:
        """保存状态机状态"""
        state_data = {
            "current_state": self.state.value,
            "state_history": [s.value for s in self.state_history],
            "context": self.context
        }
        return json.dumps(state_data)
    
    def load_state(self, state_json: str):
        """加载状态机状态"""
        state_data = json.loads(state_json)
        self.state = State(state_data["current_state"])
        self.state_history = [State(s) for s in state_data["state_history"]]
        self.context = state_data.get("context", {})


# 全局状态机实例
state_machine = StateMachine()
