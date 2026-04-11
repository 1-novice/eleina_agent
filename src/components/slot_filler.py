"""槽位填充器 - 从自然语言中抽取结构化字段"""
from typing import Dict, List, Optional, Any, Callable
import re

class Slot:
    """槽位定义"""
    
    def __init__(self, name: str, required: bool = False, 
                 entity_type: str = None, validator: Callable = None,
                 prompt: str = None):
        self.name = name
        self.required = required
        self.entity_type = entity_type
        self.validator = validator
        self.prompt = prompt or f"请提供{name}"
        self.value = None
        self.confirmed = False

class SlotFiller:
    """槽位填充器"""
    
    def __init__(self):
        self.slots: Dict[str, Slot] = {}
        self.current_slot_index = 0
        self.intent = None
    
    def define_slot(self, name: str, required: bool = False, 
                   entity_type: str = None, validator: Callable = None,
                   prompt: str = None):
        """定义槽位"""
        self.slots[name] = Slot(name, required, entity_type, validator, prompt)
    
    def define_slots(self, slots_def: List[Dict[str, Any]]):
        """批量定义槽位"""
        for slot_def in slots_def:
            self.define_slot(
                name=slot_def["name"],
                required=slot_def.get("required", False),
                entity_type=slot_def.get("entity_type"),
                validator=slot_def.get("validator"),
                prompt=slot_def.get("prompt")
            )
    
    def extract_slots(self, text: str) -> Dict[str, Any]:
        """从文本中抽取槽位"""
        extracted = {}
        
        for name, slot in self.slots.items():
            if slot.entity_type:
                value = self._extract_by_entity_type(text, slot.entity_type)
            else:
                value = self._extract_by_pattern(text, name)
            
            if value:
                extracted[name] = value
                slot.value = value
        
        return extracted
    
    def _extract_by_entity_type(self, text: str, entity_type: str) -> Optional[str]:
        """按实体类型抽取"""
        patterns = {
            "city": r"([\u4e00-\u9fa5]{2,5}(市|省|区|县))",
            "date": r"(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日号]?)|(\d{1,2}[月]\d{1,2}[日号]?)",
            "time": r"(\d{1,2}[:点]\d{2}([分秒]?)?)",
            "number": r"(\d+(?:\.\d+)?)",
            "name": r"([\u4e00-\u9fa5]{2,4})"
        }
        
        pattern = patterns.get(entity_type)
        if pattern:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_by_pattern(self, text: str, slot_name: str) -> Optional[str]:
        """按模式抽取"""
        pattern_map = {
            "from": r"(从|自|出发地|起点)\s*([\u4e00-\u9fa5]{2,5}(市|省|区|县))",
            "to": r"(到|去|目的地|终点)\s*([\u4e00-\u9fa5]{2,5}(市|省|区|县))",
            "departure_date": r"(出发|离开)\s*(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日号]?)",
            "return_date": r"(返回|回来)\s*(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日号]?)"
        }
        
        pattern = pattern_map.get(slot_name)
        if pattern:
            match = re.search(pattern, text)
            if match:
                return match.group(2)
        
        return None
    
    def validate_slot(self, slot_name: str, value: Any) -> bool:
        """验证槽位值"""
        slot = self.slots.get(slot_name)
        if not slot:
            return False
        
        if slot.validator:
            return slot.validator(value)
        
        return True
    
    def get_missing_slots(self) -> List[str]:
        """获取缺失的必填槽位"""
        missing = []
        for name, slot in self.slots.items():
            if slot.required and slot.value is None:
                missing.append(name)
        return missing
    
    def get_next_missing_slot(self) -> Optional[Slot]:
        """获取下一个缺失的槽位"""
        missing_slots = self.get_missing_slots()
        if missing_slots:
            return self.slots[missing_slots[0]]
        return None
    
    def fill_slot(self, slot_name: str, value: Any, confirmed: bool = False) -> bool:
        """填充槽位"""
        slot = self.slots.get(slot_name)
        if not slot:
            return False
        
        if self.validate_slot(slot_name, value):
            slot.value = value
            slot.confirmed = confirmed
            return True
        
        return False
    
    def is_complete(self) -> bool:
        """检查是否所有必填槽位都已填充"""
        return len(self.get_missing_slots()) == 0
    
    def get_slot_values(self) -> Dict[str, Any]:
        """获取所有槽位值"""
        return {name: slot.value for name, slot in self.slots.items()}
    
    def get_slot_prompt(self, slot_name: str) -> str:
        """获取槽位的提示语"""
        slot = self.slots.get(slot_name)
        return slot.prompt if slot else ""
    
    def reset(self):
        """重置槽位填充器"""
        for slot in self.slots.values():
            slot.value = None
            slot.confirmed = False
        self.current_slot_index = 0
        self.intent = None


# 全局槽位填充器实例
slot_filler = SlotFiller()
