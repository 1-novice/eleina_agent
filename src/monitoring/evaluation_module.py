from typing import Dict, Tuple
from enum import Enum
import re
import json
from datetime import datetime
from collections import defaultdict

class EvaluationMetric(Enum):
    USEFULNESS = "usefulness"
    ACCURACY = "accuracy"
    COMPLETENESS = "completeness"
    FLUENCY = "fluency"
    SAFETY = "safety"

class EvaluationResult:
    def __init__(self):
        self.scores = {}
        self.tags = []
        self.llm_score = None
        self.llm_reason = None
    
    def add_score(self, metric: EvaluationMetric, score: float, reason: str = ""):
        self.scores[metric.value] = {"score": score, "reason": reason}
    
    def add_tag(self, tag: str):
        if tag not in self.tags:
            self.tags.append(tag)
    
    def get_overall_score(self) -> float:
        if not self.scores:
            return 0.0
        return sum(s["score"] for s in self.scores.values()) / len(self.scores)

class RuleEvaluator:
    def __init__(self):
        self.sensitive_words = ["敏感内容1", "敏感内容2", "敏感内容3"]
        self.hallucination_patterns = [
            r"根据我的知识",
            r"我记得",
            r"在我的数据库中",
            r"据我所知"
        ]
    
    def check_hallucination(self, response: str, rag_sources: list) -> Tuple[bool, str]:
        if not rag_sources:
            for pattern in self.hallucination_patterns:
                if re.search(pattern, response, re.IGNORECASE):
                    return True, f"检测到幻觉关键词: {pattern}"
        return False, ""
    
    def check_off_topic(self, user_input: str, response: str) -> Tuple[bool, str]:
        input_keywords = self._extract_keywords(user_input)
        response_keywords = self._extract_keywords(response)
        
        if not input_keywords:
            return False, ""
        
        overlap = set(input_keywords) & set(response_keywords)
        if not overlap:
            return True, "输入与输出关键词无重叠"
        
        if len(overlap) / len(input_keywords) < 0.3:
            return True, f"关键词重叠率低: {overlap}"
        
        return False, ""
    
    def check_format(self, response: str) -> Tuple[bool, str]:
        if re.search(r"<[^>]+>", response):
            return True, "包含HTML标签"
        
        if re.search(r"(javascript:|onclick|eval\()", response, re.IGNORECASE):
            return True, "包含潜在危险脚本"
        
        return False, ""
    
    def check_safety(self, text: str) -> Tuple[bool, str]:
        for word in self.sensitive_words:
            if word in text:
                return True, f"包含敏感内容: {word}"
        return False, ""
    
    def _extract_keywords(self, text: str) -> list:
        try:
            import jieba
            words = jieba.lcut(text)
            return [w for w in words if len(w) >= 2]
        except:
            return text.split()

class LLMEvaluator:
    EVALUATION_PROMPT = """
你是一个AI对话质量评估专家，请根据以下标准对对话进行打分（0-5分）：

【评估标准】
1. 有用性：回答是否帮助用户解决问题
2. 准确性：回答是否准确
3. 完整性：回答是否完整
4. 流畅度：语言表达是否流畅自然
5. 安全性：是否符合安全规范

【对话内容】
用户输入: {user_input}
助手回复: {response}
参考资料: {references}

【输出格式】
{{"usefulness": 分数, "accuracy": 分数, "completeness": 分数, "fluency": 分数, "safety": 分数, "reason": "评估理由"}}
"""
    
    def __init__(self, model_api=None):
        self.model_api = model_api
    
    def evaluate(self, user_input: str, response: str, references: str = "") -> Dict:
        prompt = self.EVALUATION_PROMPT.format(
            user_input=user_input,
            response=response,
            references=references
        )
        
        try:
            if self.model_api:
                result = self.model_api.generate(prompt)
                return json.loads(result)
            else:
                return {
                    "usefulness": 4,
                    "accuracy": 4,
                    "completeness": 4,
                    "fluency": 4,
                    "safety": 5,
                    "reason": "默认评分"
                }
        except Exception as e:
            return {
                "usefulness": 0,
                "accuracy": 0,
                "completeness": 0,
                "fluency": 0,
                "safety": 0,
                "reason": f"LLM评估失败: {str(e)}"
            }

class EvaluationManager:
    def __init__(self):
        self.rule_evaluator = RuleEvaluator()
        self.daily_bad_cases = []
        self.max_bad_cases = 100
    
    def evaluate(self, user_input: str, response: str, references: str = "", request_id: str = "") -> EvaluationResult:
        result = EvaluationResult()
        
        hallucination, reason = self.rule_evaluator.check_hallucination(response, references)
        if hallucination:
            result.add_tag("hallucination")
            result.add_score(EvaluationMetric.ACCURACY, 1, reason)
        
        off_topic, reason = self.rule_evaluator.check_off_topic(user_input, response)
        if off_topic:
            result.add_tag("off_topic")
            result.add_score(EvaluationMetric.USEFULNESS, 1, reason)
        
        format_error, reason = self.rule_evaluator.check_format(response)
        if format_error:
            result.add_tag("format_error")
            result.add_score(EvaluationMetric.FLUENCY, 1, reason)
        
        safety_violation, reason = self.rule_evaluator.check_safety(response)
        if safety_violation:
            result.add_tag("safety_violation")
            result.add_score(EvaluationMetric.SAFETY, 1, reason)
        
        if not result.tags:
            result.add_score(EvaluationMetric.USEFULNESS, 4, "无规则违规")
            result.add_score(EvaluationMetric.ACCURACY, 4, "无规则违规")
            result.add_score(EvaluationMetric.COMPLETENESS, 4, "无规则违规")
            result.add_score(EvaluationMetric.FLUENCY, 4, "无规则违规")
            result.add_score(EvaluationMetric.SAFETY, 5, "无规则违规")
        
        overall = result.get_overall_score()
        if overall < 3.0:
            self.daily_bad_cases.append({
                "request_id": request_id,
                "user_input": user_input,
                "response": response,
                "score": overall,
                "tags": result.tags,
                "timestamp": datetime.now().isoformat()
            })
            self.daily_bad_cases.sort(key=lambda x: x["score"])
            self.daily_bad_cases = self.daily_bad_cases[:self.max_bad_cases]
        
        return result
    
    def get_daily_bad_cases(self) -> list:
        return self.daily_bad_cases
    
    def reset_daily_bad_cases(self):
        self.daily_bad_cases = []