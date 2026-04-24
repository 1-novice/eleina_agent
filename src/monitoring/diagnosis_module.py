from typing import Dict, List
from collections import defaultdict
from datetime import datetime

class DiagnosisResult:
    def __init__(self):
        self.bad_cases = []
        self.knowledge_gaps = []
        self.tool_failures = defaultdict(int)
        self.intent_failures = defaultdict(int)
        self.frequent_complaints = []
        self.suggestions = []
    
    def to_dict(self) -> Dict:
        return {
            "bad_cases": self.bad_cases,
            "knowledge_gaps": self.knowledge_gaps,
            "tool_failures": dict(self.tool_failures),
            "intent_failures": dict(self.intent_failures),
            "frequent_complaints": self.frequent_complaints,
            "suggestions": self.suggestions,
            "generated_at": datetime.now().isoformat()
        }

class DiagnosisAnalyzer:
    def __init__(self):
        self.intent_failure_patterns = [
            ("无法理解", "意图识别"),
            ("不知道", "知识盲区"),
            ("抱歉", "拒绝回答"),
            ("错误", "系统错误")
        ]
    
    def analyze_bad_cases(self, bad_cases: List[Dict]) -> List[Dict]:
        categorized = defaultdict(list)
        
        for case in bad_cases:
            tags = case.get("tags", [])
            if "hallucination" in tags:
                categorized["幻觉"].append(case)
            elif "off_topic" in tags:
                categorized["答非所问"].append(case)
            elif "format_error" in tags:
                categorized["格式错误"].append(case)
            elif "safety_violation" in tags:
                categorized["安全违规"].append(case)
            else:
                categorized["其他"].append(case)
        
        result = []
        for category, cases in sorted(categorized.items(), key=lambda x: len(x[1]), reverse=True)[:5]:
            result.append({
                "category": category,
                "count": len(cases),
                "examples": cases[:3]
            })
        
        return result
    
    def detect_knowledge_gaps(self, conversations: List[Dict]) -> List[Dict]:
        gap_keywords = ["不知道", "不清楚", "不了解", "无法回答", "没有相关信息"]
        gaps = defaultdict(int)
        
        for conv in conversations:
            response = conv.get("response", "")
            for keyword in gap_keywords:
                if keyword in response:
                    user_input = conv.get("user_input", "")
                    topic = self._extract_topic(user_input)
                    gaps[topic] += 1
        
        return [
            {"topic": topic, "count": count}
            for topic, count in sorted(gaps.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
    
    def analyze_tool_failures(self, tool_calls: List[Dict]) -> Dict[str, int]:
        failures = defaultdict(int)
        
        for call in tool_calls:
            if not call.get("success", True):
                tool_name = call.get("tool_name", "unknown")
                failures[tool_name] += 1
        
        return dict(failures)
    
    def analyze_intent_failures(self, intents: List[Dict]) -> Dict[str, int]:
        failures = defaultdict(int)
        
        for intent in intents:
            confidence = intent.get("confidence", 0)
            if confidence < 0.5:
                intent_name = intent.get("intent", "unknown")
                failures[intent_name] += 1
        
        return dict(failures)
    
    def identify_frequent_complaints(self, feedbacks: List[Dict]) -> List[Dict]:
        complaints = defaultdict(int)
        
        for feedback in feedbacks:
            content = feedback.get("content", "")
            complaint_type = self._classify_complaint(content)
            complaints[complaint_type] += 1
        
        return [
            {"type": complaint_type, "count": count}
            for complaint_type, count in sorted(complaints.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
    
    def generate_suggestions(self, diagnosis: DiagnosisResult) -> List[str]:
        suggestions = []
        
        for case_type in diagnosis.bad_cases:
            if case_type["category"] == "幻觉" and case_type["count"] > 10:
                suggestions.append("建议增强 RAG 检索质量，增加事实核查环节")
            if case_type["category"] == "答非所问" and case_type["count"] > 10:
                suggestions.append("建议优化意图识别模型，增加上下文理解能力")
        
        if len(diagnosis.knowledge_gaps) > 5:
            suggestions.append(f"建议补充以下知识点：{', '.join([g['topic'] for g in diagnosis.knowledge_gaps[:3]])}")
        
        for tool, count in diagnosis.tool_failures.items():
            if count > 5:
                suggestions.append(f"建议检查 {tool} 工具配置，当前失败次数较多")
        
        return suggestions
    
    def _extract_topic(self, text: str) -> str:
        return text[:30].strip()
    
    def _classify_complaint(self, content: str) -> str:
        complaint_patterns = [
            ("慢", "响应慢"),
            ("错误", "出错"),
            ("不对", "回答错误"),
            ("差", "质量差"),
            ("贵", "成本高")
        ]
        
        for pattern, category in complaint_patterns:
            if pattern in content:
                return category
        
        return "其他"

    def run_full_diagnosis(self, data: Dict) -> DiagnosisResult:
        diagnosis = DiagnosisResult()
        
        diagnosis.bad_cases = self.analyze_bad_cases(data.get("bad_cases", []))
        diagnosis.knowledge_gaps = self.detect_knowledge_gaps(data.get("conversations", []))
        diagnosis.tool_failures = self.analyze_tool_failures(data.get("tool_calls", []))
        diagnosis.intent_failures = self.analyze_intent_failures(data.get("intents", []))
        diagnosis.frequent_complaints = self.identify_frequent_complaints(data.get("feedbacks", []))
        diagnosis.suggestions = self.generate_suggestions(diagnosis)
        
        return diagnosis

def generate_review_report(diagnosis: DiagnosisResult) -> str:
    report = f"""
========================================
        AI Agent 诊断复盘报告
========================================
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

一、Bad Case 分析
----------------
"""
    
    for case in diagnosis.bad_cases:
        report += f"  {case['category']}: {case['count']} 例\n"
    
    report += """
二、知识盲区 TOP10
------------------
"""
    
    for gap in diagnosis.knowledge_gaps:
        report += f"  • {gap['topic']}: {gap['count']} 次\n"
    
    report += """
三、工具调用失败统计
-------------------
"""
    
    for tool, count in diagnosis.tool_failures.items():
        report += f"  • {tool}: {count} 次失败\n"
    
    report += """
四、优化建议
-----------
"""
    
    for suggestion in diagnosis.suggestions:
        report += f"  • {suggestion}\n"
    
    report += """
========================================
"""
    
    return report