from typing import Dict, List, Optional, Any
import re


class IntentParser:
    def __init__(self):
        # 意图模式匹配规则
        self.intent_patterns = {
            "问答": [
                r"什么是.*",
                r"如何.*",
                r"为什么.*",
                r"有哪些.*",
                r"怎么.*",
                r"哪里.*",
                r"什么时候.*",
                r"谁.*"
            ],
            "创作": [
                r"写.*",
                r"创作.*",
                r"生成.*",
                r"编.*",
                r"设计.*",
                r"制作.*"
            ],
            "任务执行": [
                r"帮我.*",
                r"请.*",
                r"查.*",
                r"搜索.*",
                r"计算.*",
                r"分析.*"
            ],
            "闲聊": [
                r"你好",
                r"嗨",
                r"在吗",
                r"在不在",
                r"最近怎么样",
                r"今天天气",
                r"聊聊天"
            ],
            "投诉/人工": [
                r"投诉",
                r"人工",
                r"转人工",
                r"联系客服",
                r"不满意",
                r"退款",
                r"退货"
            ],
            "多轮复杂任务": [
                r"首先.*然后.*",
                r"第一步.*第二步.*",
                r"先.*再.*",
                r"需要.*还需要.*"
            ]
        }
        
        # 槽位抽取规则
        self.slot_patterns = {
            "date": [
                r"(今天|明天|后天|昨天|前天)",
                r"(\d{4}-\d{2}-\d{2})",
                r"(\d{2}/\d{2}/\d{4})",
                r"(\d{2}/\d{2})"
            ],
            "city": [
                r"(北京|上海|广州|深圳|杭州|成都|武汉|西安|南京|重庆|天津|苏州|郑州|长沙|沈阳|青岛|宁波|东莞|佛山)"
            ],
            "time": [
                r"(\d{2}:\d{2})",
                r"(上午|下午|晚上|凌晨)"
            ],
            "number": [
                r"(\d+)"
            ],
            "product": [
                r"(手机|电脑|平板|耳机|手表|相机)"
            ],
            "action": [
                r"(查询|搜索|计算|分析|生成|创建|删除|修改)"
            ]
        }
    
    def parse(self, user_input: str) -> Dict[str, Any]:
        """解析用户输入，识别意图和槽位"""
        result = {
            "intent": "未知",
            "slots": {},
            "needs_tool": False,
            "needs_rag": False,
            "needs_multistep": False,
            "needs_clarification": False,
            "clarification_questions": []
        }
        
        # 识别意图
        result["intent"] = self._identify_intent(user_input)
        
        # 抽取槽位
        result["slots"] = self._extract_slots(user_input)
        
        # 判断任务类型
        result["needs_tool"] = self._needs_tool(result["intent"], result["slots"])
        result["needs_rag"] = self._needs_rag(result["intent"], user_input)
        result["needs_multistep"] = self._needs_multistep(result["intent"], user_input)
        
        # 检查是否需要澄清
        result["needs_clarification"], result["clarification_questions"] = self._needs_clarification(
            result["intent"], result["slots"]
        )
        
        return result
    
    def _identify_intent(self, user_input: str) -> str:
        """识别用户意图"""
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, user_input):
                    return intent
        return "未知"
    
    def _extract_slots(self, user_input: str) -> Dict[str, Any]:
        """抽取槽位信息"""
        slots = {}
        for slot_name, patterns in self.slot_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, user_input)
                if matches:
                    slots[slot_name] = matches[0]
                    break
        return slots
    
    def _needs_tool(self, intent: str, slots: Dict[str, Any]) -> bool:
        """判断是否需要工具"""
        tool_intents = ["任务执行", "多轮复杂任务"]
        if intent in tool_intents:
            return True
        
        # 特定槽位需要工具
        if "action" in slots:
            return True
        
        return False
    
    def _needs_rag(self, intent: str, user_input: str) -> bool:
        """判断是否需要RAG"""
        rag_keywords = ["资料", "文档", "知识库", "信息", "数据", "详情"]
        if intent == "问答" and any(keyword in user_input for keyword in rag_keywords):
            return True
        return False
    
    def _needs_multistep(self, intent: str, user_input: str) -> bool:
        """判断是否需要多步执行"""
        if intent == "多轮复杂任务":
            return True
        
        multistep_keywords = ["首先", "然后", "第一步", "第二步", "先", "再", "需要", "还需要"]
        if sum(1 for keyword in multistep_keywords if keyword in user_input) >= 2:
            return True
        
        return False
    
    def _needs_clarification(self, intent: str, slots: Dict[str, Any]):
        """判断是否需要澄清
        
        Returns:
            tuple[bool, List[str]]: (是否需要澄清, 澄清问题列表)
        """
        questions = []
        
        if intent == "任务执行":
            if "action" not in slots:
                questions.append("请问您具体需要我做什么操作？")
            if intent == "查询天气" and "city" not in slots:
                questions.append("请问您想查询哪个城市的天气？")
            if intent == "查询天气" and "date" not in slots:
                questions.append("请问您想查询哪一天的天气？")
        
        elif intent == "创作":
            if len(slots) == 0:
                questions.append("请问您希望我创作什么内容？")
        
        return len(questions) > 0, questions


# 全局意图解析器实例
intent_parser = IntentParser()