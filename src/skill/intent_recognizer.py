from typing import Dict, List, Optional, Any, Tuple
from src.skill.intent_registry import intent_registry
import re


class IntentRecognizer:
    def __init__(self):
        pass
    
    def recognize(self, user_input: str) -> Dict[str, Any]:
        """识别意图
        
        Args:
            user_input: 用户输入
            
        Returns:
            Dict[str, Any]: 识别结果
        """
        # 预处理用户输入
        processed_input = self._preprocess(user_input)
        
        # 规则匹配
        rule_matches = self._rule_based_matching(processed_input)
        
        # 计算置信度
        best_match = None
        highest_confidence = 0.0
        
        for match in rule_matches:
            if match['confidence'] > highest_confidence:
                highest_confidence = match['confidence']
                best_match = match
        
        # 检查是否达到置信度阈值
        if best_match and best_match['confidence'] >= best_match['threshold']:
            return {
                "intent": best_match['intent'],
                "confidence": best_match['confidence'],
                "skill_id": best_match['skill_id'],
                "is_rejected": False
            }
        else:
            # 拒识
            return {
                "intent": None,
                "confidence": 0.0,
                "skill_id": None,
                "is_rejected": True
            }
    
    def recognize_multiple(self, user_input: str) -> List[Dict[str, Any]]:
        """识别多个意图
        
        Args:
            user_input: 用户输入
            
        Returns:
            List[Dict[str, Any]]: 识别结果列表
        """
        # 预处理用户输入
        processed_input = self._preprocess(user_input)
        
        # 规则匹配
        rule_matches = self._rule_based_matching(processed_input)
        
        # 过滤并排序
        valid_matches = [match for match in rule_matches if match['confidence'] >= match['threshold']]
        valid_matches.sort(key=lambda x: x['confidence'], reverse=True)
        
        # 转换为标准格式
        results = []
        for match in valid_matches:
            results.append({
                "intent": match['intent'],
                "confidence": match['confidence'],
                "skill_id": match['skill_id']
            })
        
        return results
    
    def _preprocess(self, text: str) -> str:
        """预处理文本
        
        Args:
            text: 原始文本
            
        Returns:
            str: 预处理后的文本
        """
        # 转为小写
        text = text.lower()
        # 去除标点
        text = re.sub(r'[\p{P}\p{S}]', ' ', text)
        # 去除多余空格
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def _rule_based_matching(self, text: str) -> List[Dict[str, Any]]:
        """基于规则的匹配
        
        Args:
            text: 预处理后的文本
            
        Returns:
            List[Dict[str, Any]]: 匹配结果
        """
        matches = []
        
        # 获取所有意图
        intents = intent_registry.get_all_intents()
        
        for intent_name, intent_info in intents.items():
            patterns = intent_info.get('patterns', [])
            skill_id = intent_info.get('skill_id', '')
            threshold = intent_info.get('confidence_threshold', 0.7)
            
            # 计算匹配度
            confidence = 0.0
            for pattern in patterns:
                pattern_lower = pattern.lower()
                if pattern_lower in text:
                    # 简单的匹配度计算
                    match_length = len(pattern_lower)
                    text_length = len(text)
                    confidence = max(confidence, match_length / text_length)
            
            if confidence > 0:
                matches.append({
                    'intent': intent_name,
                    'skill_id': skill_id,
                    'confidence': confidence,
                    'threshold': threshold
                })
        
        # 按优先级排序
        matches.sort(key=lambda x: x.get('priority', 0), reverse=True)
        
        return matches


# 全局意图识别引擎实例
intent_recognizer = IntentRecognizer()