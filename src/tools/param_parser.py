from typing import Dict, List, Optional, Any, Tuple
from src.tools.tool_registry import tool_registry


class ParamParser:
    def __init__(self):
        pass
    
    def parse_and_validate(self, tool_name: str, params: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], List[str]]:
        """解析和校验参数
        
        Args:
            tool_name: 工具名称
            params: 参数字典
            
        Returns:
            Tuple[bool, Dict[str, Any], List[str]]: (是否有效, 解析后的参数, 错误信息)
        """
        # 获取工具信息
        tool = tool_registry.get_tool(tool_name)
        if not tool:
            return False, {}, ["工具不存在"]
        
        # 校验参数
        required_params = [k for k, v in tool["parameters"].items() if v.get("required", False)]
        missing_params = [param for param in required_params if param not in params]
        
        if missing_params:
            return False, {}, [f"缺少必填参数: {', '.join(missing_params)}"]
        
        # 类型校验
        errors = []
        validated_params = {}
        
        for param_name, param_info in tool["parameters"].items():
            if param_name in params:
                param_value = params[param_name]
                expected_type = param_info.get("type", "string")
                
                # 类型转换和校验
                if expected_type == "string" and not isinstance(param_value, str):
                    errors.append(f"参数 {param_name} 应为字符串类型")
                elif expected_type == "integer" and not isinstance(param_value, int):
                    try:
                        param_value = int(param_value)
                    except Exception:
                        errors.append(f"参数 {param_name} 应为整数类型")
                elif expected_type == "number" and not isinstance(param_value, (int, float)):
                    try:
                        param_value = float(param_value)
                    except Exception:
                        errors.append(f"参数 {param_name} 应为数字类型")
                elif expected_type == "boolean" and not isinstance(param_value, bool):
                    if isinstance(param_value, str):
                        param_value = param_value.lower() == "true"
                    else:
                        errors.append(f"参数 {param_name} 应为布尔类型")
                elif expected_type == "array" and not isinstance(param_value, list):
                    errors.append(f"参数 {param_name} 应为数组类型")
                elif expected_type == "object" and not isinstance(param_value, dict):
                    errors.append(f"参数 {param_name} 应为对象类型")
                
                validated_params[param_name] = param_value
        
        if errors:
            return False, {}, errors
        
        return True, validated_params, []
    
    def generate_clarification_questions(self, tool_name: str, params: Dict[str, Any]) -> List[str]:
        """生成澄清问题
        
        Args:
            tool_name: 工具名称
            params: 参数字典
            
        Returns:
            List[str]: 澄清问题列表
        """
        # 获取工具信息
        tool = tool_registry.get_tool(tool_name)
        if not tool:
            return []
        
        # 检查缺失的必填参数
        required_params = [k for k, v in tool["parameters"].items() if v.get("required", False)]
        missing_params = [param for param in required_params if param not in params]
        
        # 生成澄清问题
        questions = []
        for param in missing_params:
            param_info = tool["parameters"][param]
            description = param_info.get("description", param)
            questions.append(f"请问你想{description}？")
        
        return questions
    
    def parse_tool_call(self, tool_call: Dict[str, Any]) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """解析工具调用
        
        Args:
            tool_call: 工具调用字典
            
        Returns:
            Tuple[Optional[str], Optional[Dict[str, Any]]]: (工具名称, 参数)
        """
        try:
            if isinstance(tool_call, dict):
                # 处理 OpenAI 格式的工具调用
                if "function" in tool_call:
                    function = tool_call["function"]
                    return function.get("name"), function.get("arguments")
                # 处理其他格式的工具调用
                elif "name" in tool_call:
                    return tool_call["name"], tool_call.get("parameters", {})
            return None, None
        except Exception as e:
            print(f"解析工具调用失败: {e}")
            return None, None


# 全局参数解析器实例
param_parser = ParamParser()