from typing import Dict, List, Optional, Any


class ResponseTemplate:
    def __init__(self):
        # 定义回复模板
        self.templates = {
            "weather_skill": {
                "success": "{city}{date}天气{weather}，气温{temp}℃，湿度{humidity}%，{wind}。",
                "failure": "暂时无法获取天气信息，请稍后再试。",
                "clarification": {
                    "city": "请问你想查询哪个城市的天气？",
                    "date": "请问你想查询哪一天的天气？"
                },
                "progress": "正在查询{city}的天气信息..."
            },
            "search_skill": {
                "success": "关于'{query}'的搜索结果如下：\n{results}",
                "failure": "暂时无法获取搜索结果，请稍后再试。",
                "clarification": {
                    "query": "请问你想搜索什么内容？"
                },
                "progress": "正在搜索'{query}'..."
            }
        }
    
    def get_template(self, skill_id: str, template_type: str, slot_name: Optional[str] = None) -> str:
        """获取回复模板
        
        Args:
            skill_id: Skill ID
            template_type: 模板类型 (success/failure/clarification/progress)
            slot_name: 槽位名称 (仅用于clarification模板)
            
        Returns:
            str: 回复模板
        """
        if skill_id not in self.templates:
            return ""
        
        skill_templates = self.templates[skill_id]
        
        if template_type == "clarification" and slot_name:
            return skill_templates.get(template_type, {}).get(slot_name, "")
        
        return skill_templates.get(template_type, "")
    
    def format_response(self, skill_id: str, template_type: str, data: Dict[str, Any], slot_name: Optional[str] = None) -> str:
        """格式化回复
        
        Args:
            skill_id: Skill ID
            template_type: 模板类型 (success/failure/clarification/progress)
            data: 数据
            slot_name: 槽位名称 (仅用于clarification模板)
            
        Returns:
            str: 格式化后的回复
        """
        template = self.get_template(skill_id, template_type, slot_name)
        
        if not template:
            return ""
        
        try:
            return template.format(**data)
        except Exception:
            return template


# 全局回复模板实例
response_template = ResponseTemplate()