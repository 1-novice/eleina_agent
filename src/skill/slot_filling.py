from typing import Dict, List, Optional, Any, Tuple
import re


class SlotFilling:
    def __init__(self):
        # 定义槽位配置
        self.slot_configs = {
            "weather_skill": {
                "city": {
                    "type": "string",
                    "required": True,
                    "question": "请问你想查询哪个城市的天气？",
                    "patterns": [r"(北京|上海|广州|深圳|杭州|成都|武汉|西安|南京|重庆)"]
                },
                "date": {
                    "type": "string",
                    "required": False,
                    "question": "请问你想查询哪一天的天气？",
                    "patterns": [r"(今天|明天|后天|\d{4}-\d{2}-\d{2}|\d{2}-\d{2})"]
                }
            },
            "search_skill": {
                "query": {
                    "type": "string",
                    "required": True,
                    "question": "请问你想搜索什么内容？",
                    "patterns": [r".+"]
                }
            }
        }
    
    def extract_slots(self, user_input: str, skill_id: str) -> Dict[str, Any]:
        """提取槽位
        
        Args:
            user_input: 用户输入
            skill_id: Skill ID
            
        Returns:
            Dict[str, Any]: 槽位信息
        """
        slots = {}
        
        # 获取Skill的槽位配置
        slot_config = self.slot_configs.get(skill_id, {})
        
        for slot_name, config in slot_config.items():
            # 尝试从用户输入中提取槽位
            for pattern in config.get("patterns", []):
                matches = re.findall(pattern, user_input)
                if matches:
                    slots[slot_name] = matches[0]
                    break
        
        return slots
    
    def check_missing_slots(self, slots: Dict[str, Any], skill_id: str) -> List[str]:
        """检查缺失的槽位
        
        Args:
            slots: 槽位信息
            skill_id: Skill ID
            
        Returns:
            List[str]: 缺失的槽位列表
        """
        missing_slots = []
        
        # 获取Skill的槽位配置
        slot_config = self.slot_configs.get(skill_id, {})
        
        for slot_name, config in slot_config.items():
            if config.get("required", False) and slot_name not in slots:
                missing_slots.append(slot_name)
        
        return missing_slots
    
    def generate_clarification_questions(self, missing_slots: List[str], skill_id: str) -> List[str]:
        """生成澄清问题
        
        Args:
            missing_slots: 缺失的槽位列表
            skill_id: Skill ID
            
        Returns:
            List[str]: 澄清问题列表
        """
        questions = []
        
        # 获取Skill的槽位配置
        slot_config = self.slot_configs.get(skill_id, {})
        
        for slot_name in missing_slots:
            if slot_name in slot_config:
                question = slot_config[slot_name].get("question", f"请问你想{slot_name}？")
                questions.append(question)
        
        return questions
    
    def fill_slots(self, user_input: str, skill_id: str, existing_slots: Dict[str, Any] = None) -> Tuple[Dict[str, Any], List[str]]:
        """填充槽位
        
        Args:
            user_input: 用户输入
            skill_id: Skill ID
            existing_slots: 现有槽位信息
            
        Returns:
            Tuple[Dict[str, Any], List[str]]: (槽位信息, 缺失的槽位列表)
        """
        if existing_slots is None:
            existing_slots = {}
        
        # 提取槽位
        new_slots = self.extract_slots(user_input, skill_id)
        
        # 合并槽位
        combined_slots = {**existing_slots, **new_slots}
        
        # 检查缺失的槽位
        missing_slots = self.check_missing_slots(combined_slots, skill_id)
        
        return combined_slots, missing_slots


# 全局槽位填充实例
slot_filling = SlotFilling()