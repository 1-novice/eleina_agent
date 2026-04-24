from typing import Dict, List, Optional, Any
from src.agent.model_engine import model_engine
from src.config.config import settings


class ReasoningEngine:
    def __init__(self):
        pass
    
    def think(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """思考过程，使用CoT"""
        try:
            # 构建思考提示词
            prompt = self._build_thinking_prompt(user_input, context)
            
            # 调用模型进行思考
            request = {
                "model": model_engine.current_model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "stream": False,
                "user_id": context.get("user_id", "unknown")
            }
            
            response = model_engine.generate(request)
            thinking_content = response.get("content", "")
            
            # 解析思考结果
            result = self._parse_thinking_result(thinking_content)
            return result
        except Exception as e:
            print(f"思考过程失败: {e}")
            return {
                "thought": "思考过程失败",
                "tool_choice": None,
                "tool_params": {},
                "next_step": "answer",
                "confidence": 0.5
            }
    
    def _build_thinking_prompt(self, user_input: str, context: Dict[str, Any]) -> str:
        """构建思考提示词"""
        prompt = f"""你是一个全能的智能体动漫角色，现在需要分析用户的请求并进行思考。

用户输入：{user_input}

当前上下文：{context}

请按照以下步骤进行思考：
1. 我现在要做什么？
2. 我缺什么信息？
3. 我该用什么工具？
4. 结果对不对？

请以自然、清晰的语言表达你的思考过程，最后给出你的决策。"""
        return prompt
    
    def _parse_thinking_result(self, thinking_content: str) -> Dict[str, Any]:
        """解析思考结果"""
        result = {
            "thought": thinking_content,
            "tool_choice": None,
            "tool_params": {},
            "next_step": "",
            "confidence": 0.8
        }
        
        # 简单的工具选择逻辑
        if "搜索" in thinking_content:
            result["tool_choice"] = "search_tool"
            result["tool_params"] = {"query": "需要搜索的内容"}
        elif "计算" in thinking_content:
            result["tool_choice"] = "calculator_tool"
            result["tool_params"] = {"expression": "需要计算的表达式"}
        elif "文件" in thinking_content:
            result["tool_choice"] = "file_tool"
            result["tool_params"] = {"file_path": "文件路径"}
        
        # 确定下一步
        if "需要追问" in thinking_content:
            result["next_step"] = "clarify"
        elif "需要工具" in thinking_content:
            result["next_step"] = "use_tool"
        elif "可以直接回答" in thinking_content:
            result["next_step"] = "answer"
        
        return result
    
    def plan(self, complex_task: str) -> List[Dict[str, Any]]:
        """规划复杂任务"""
        try:
            # 构建规划提示词
            prompt = f"""你是一个全能的智能体动漫角色，现在需要对复杂任务进行规划。

复杂任务：{complex_task}

请将该任务分解为具体的步骤，并为每个步骤提供详细的说明。

示例格式：
步骤1：明确需求
- 了解用户的具体需求
- 确认任务的目标和范围

步骤2：收集信息
- 搜索相关资料
- 分析现有数据

..."""
            
            # 调用模型生成规划
            request = {
                "model": model_engine.current_model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "stream": False,
                "user_id": "system"
            }
            
            response = model_engine.generate(request)
            plan_content = response.get("content", "")
            
            # 解析规划结果
            steps = self._parse_plan(plan_content)
            return steps
        except Exception as e:
            print(f"规划失败: {e}")
            # 返回默认规划
            return [
                {
                    "step": "步骤1：理解任务",
                    "description": "- 分析用户需求\n- 明确任务目标"
                },
                {
                    "step": "步骤2：执行任务",
                    "description": "- 完成任务内容\n- 确保任务质量"
                },
                {
                    "step": "步骤3：总结结果",
                    "description": "- 整理执行结果\n- 向用户报告"
                }
            ]
    
    def _parse_plan(self, plan_content: str) -> List[Dict[str, Any]]:
        """解析规划结果"""
        steps = []
        lines = plan_content.split("\n")
        
        current_step = None
        current_description = []
        
        for line in lines:
            line = line.strip()
            if line.startswith("步骤"):
                # 保存上一个步骤
                if current_step:
                    steps.append({
                        "step": current_step,
                        "description": "\n".join(current_description)
                    })
                
                # 开始新步骤
                current_step = line
                current_description = []
            elif line and current_step:
                current_description.append(line)
        
        # 保存最后一个步骤
        if current_step:
            steps.append({
                "step": current_step,
                "description": "\n".join(current_description)
            })
        
        return steps
    
    def react(self, user_input: str, context: Dict[str, Any], tool_results: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """使用ReAct模式进行推理"""
        try:
            if tool_results is None:
                tool_results = []
            
            # 构建ReAct提示词
            prompt = self._build_react_prompt(user_input, context, tool_results)
            
            # 调用模型进行推理
            request = {
                "model": model_engine.current_model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "stream": False,
                "user_id": context.get("user_id", "unknown")
            }
            
            response = model_engine.generate(request)
            react_content = response.get("content", "")
            
            # 解析ReAct结果
            result = self._parse_react_result(react_content)
            return result
        except Exception as e:
            print(f"ReAct推理失败: {e}")
            return {
                "thought": "推理过程失败",
                "action": None,
                "action_params": {},
                "observation": "",
                "final_decision": "抱歉，我暂时无法处理您的请求，请稍后再试。"
            }
    
    def _build_react_prompt(self, user_input: str, context: Dict[str, Any], tool_results: List[Dict[str, Any]]) -> str:
        """构建ReAct提示词"""
        tool_results_str = "\n".join([f"工具结果: {str(result)}" for result in tool_results])
        
        prompt = f"""你是一个全能的智能体动漫角色，使用ReAct模式进行推理。

用户输入：{user_input}

当前上下文：{context}

工具结果：
{tool_results_str}

请按照以下格式进行思考和决策：

思考：[你的思考过程]
行动：[选择的工具] [工具参数]
观察：[工具执行结果]
思考：[基于结果的思考]
决策：[最终决策]
"""
        return prompt
    
    def _parse_react_result(self, react_content: str) -> Dict[str, Any]:
        """解析ReAct结果"""
        result = {
            "thought": "",
            "action": None,
            "action_params": {},
            "observation": "",
            "final_decision": ""
        }
        
        lines = react_content.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("思考："):
                result["thought"] = line[3:]
            elif line.startswith("行动："):
                action_part = line[3:]
                # 简单解析工具和参数
                parts = action_part.split(" ", 1)
                if len(parts) == 2:
                    result["action"] = parts[0]
                    result["action_params"] = {"query": parts[1]}
            elif line.startswith("观察："):
                result["observation"] = line[3:]
            elif line.startswith("决策："):
                result["final_decision"] = line[3:]
        
        return result


# 全局推理引擎实例
reasoning_engine = ReasoningEngine()