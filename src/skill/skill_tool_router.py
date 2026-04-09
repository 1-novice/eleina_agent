from typing import Dict, List, Optional, Any


class SkillToolRouter:
    def __init__(self):
        # 定义Skill到工具的映射
        self.skill_tool_mapping = {
            "weather_skill": ["get_weather"],
            "search_skill": ["search_web"]
        }
    
    def get_tools_for_skill(self, skill_id: str) -> List[str]:
        """获取Skill对应的工具列表
        
        Args:
            skill_id: Skill ID
            
        Returns:
            List[str]: 工具列表
        """
        return self.skill_tool_mapping.get(skill_id, [])
    
    def route_tool_call(self, skill_id: str, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """路由工具调用
        
        Args:
            skill_id: Skill ID
            tool_call: 工具调用信息
            
        Returns:
            Dict[str, Any]: 路由后的工具调用信息
        """
        tool_name = tool_call.get("tool_choice")
        
        # 验证工具是否属于Skill
        allowed_tools = self.get_tools_for_skill(skill_id)
        if tool_name not in allowed_tools:
            return {
                "valid": False,
                "message": f"工具 {tool_name} 不属于Skill {skill_id}"
            }
        
        return {
            "valid": True,
            "tool_call": tool_call
        }
    
    def handle_tool_result(self, skill_id: str, tool_result: Dict[str, Any]) -> Dict[str, Any]:
        """处理工具执行结果
        
        Args:
            skill_id: Skill ID
            tool_result: 工具执行结果
            
        Returns:
            Dict[str, Any]: 处理后的结果
        """
        # 这里可以根据Skill ID对工具执行结果进行特殊处理
        # 目前返回原始结果
        return tool_result


# 全局Skill工具路由实例
skill_tool_router = SkillToolRouter()