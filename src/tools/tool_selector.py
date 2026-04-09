from typing import Dict, List, Optional, Any
from src.tools.tool_registry import tool_registry
from src.agent.model_engine import model_engine
from src.config.config import settings


class ToolSelector:
    def __init__(self):
        pass
    
    def select_tool(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """选择工具
        
        Args:
            user_input: 用户输入
            context: 上下文信息
            
        Returns:
            Dict[str, Any]: 工具选择结果
        """
        # 获取所有工具
        tools = tool_registry.get_all_tools()
        if not tools:
            return {"tool_choice": None, "reason": "无可用工具"}
        
        # 构建工具选择提示词
        tools_str = "\n".join([f"{name}: {info['description']}" for name, info in tools.items()])
        prompt = f"""请根据用户的问题，从以下工具中选择一个最合适的工具来解决问题：

工具列表：
{tools_str}

用户问题：{user_input}

请输出：
1. 工具名称（如果不需要工具，输出"none"）
2. 选择理由
3. 如果需要工具，输出所需参数

输出格式：
工具名称: [工具名]
选择理由: [理由]
参数: [参数JSON]"""
        
        # 调用模型进行工具选择
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
            content = response.get("content", "")
            
            # 解析模型输出
            tool_choice = None
            reason = ""
            tool_params = {}
            
            lines = content.split("\n")
            for line in lines:
                line = line.strip()
                if line.startswith("工具名称:"):
                    tool_choice = line.split(":", 1)[1].strip()
                elif line.startswith("选择理由:"):
                    reason = line.split(":", 1)[1].strip()
                elif line.startswith("参数:"):
                    import json
                    try:
                        params_str = line.split(":", 1)[1].strip()
                        tool_params = json.loads(params_str)
                    except Exception:
                        tool_params = {}
            
            # 处理不需要工具的情况
            if tool_choice == "none":
                return {"tool_choice": None, "reason": reason}
            
            # 验证工具是否存在
            if tool_choice not in tools:
                return {"tool_choice": None, "reason": "所选工具不存在"}
            
            return {
                "tool_choice": tool_choice,
                "reason": reason,
                "tool_params": tool_params
            }
        except Exception as e:
            print(f"工具选择失败: {e}")
            return {"tool_choice": None, "reason": "工具选择失败"}
    
    def select_parallel_tools(self, user_input: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """选择多个并行工具
        
        Args:
            user_input: 用户输入
            context: 上下文信息
            
        Returns:
            List[Dict[str, Any]]: 工具选择结果列表
        """
        # 构建并行工具选择提示词
        tools = tool_registry.get_all_tools()
        if not tools:
            return []
        
        tools_str = "\n".join([f"{name}: {info['description']}" for name, info in tools.items()])
        prompt = f"""请根据用户的问题，从以下工具中选择一个或多个最合适的工具来解决问题：

工具列表：
{tools_str}

用户问题：{user_input}

请输出需要使用的所有工具，每个工具包括：
1. 工具名称
2. 选择理由
3. 所需参数

输出格式：
工具1名称: [工具名]
工具1理由: [理由]
工具1参数: [参数JSON]

工具2名称: [工具名]
工具2理由: [理由]
工具2参数: [参数JSON]
..."""
        
        # 调用模型进行工具选择
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
            content = response.get("content", "")
            
            # 解析模型输出
            tool_results = []
            lines = content.split("\n")
            current_tool = {}
            
            for line in lines:
                line = line.strip()
                if line.startswith("工具") and "名称:" in line:
                    if current_tool:
                        tool_results.append(current_tool)
                        current_tool = {}
                    current_tool["tool_choice"] = line.split(":", 1)[1].strip()
                elif line.startswith("工具") and "理由:" in line:
                    current_tool["reason"] = line.split(":", 1)[1].strip()
                elif line.startswith("工具") and "参数:" in line:
                    import json
                    try:
                        params_str = line.split(":", 1)[1].strip()
                        current_tool["tool_params"] = json.loads(params_str)
                    except Exception:
                        current_tool["tool_params"] = {}
            
            if current_tool:
                tool_results.append(current_tool)
            
            # 验证工具是否存在
            valid_tool_results = []
            for tool_result in tool_results:
                if tool_result.get("tool_choice") in tools:
                    valid_tool_results.append(tool_result)
            
            return valid_tool_results
        except Exception as e:
            print(f"并行工具选择失败: {e}")
            return []


# 全局工具选择器实例
tool_selector = ToolSelector()