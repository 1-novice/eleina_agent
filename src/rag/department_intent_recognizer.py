"""科室意图识别器 - 根据用户问题识别所属科室"""
from typing import Dict, List, Optional, Tuple
import re


class DepartmentIntentRecognizer:
    """科室意图识别器"""
    
    def __init__(self):
        # 科室关键词词典
        self.department_keywords = {
            "儿科": ["儿童", "孩子", "小孩", "婴儿", "宝宝", "小儿", "儿科", "新生儿", "婴幼儿"],
            "妇产科": ["怀孕", "孕妇", "产妇", "妇科", "产科", "月经", "分娩", "哺乳", "产检", "妇科疾病"],
            "男科": ["男性", "男科", "前列腺", "阳痿", "早泄", "遗精", "性功能"],
            "内科": ["内科", "呼吸", "消化", "心脏", "血压", "血糖", "肾脏", "肝脏", "糖尿病", "高血压"],
            "外科": ["手术", "外科", "骨折", "创伤", "肿瘤", "癌症", "切除", "缝合"],
            "肿瘤科": ["肿瘤", "癌症", "癌", "瘤", "肿", "化疗", "放疗", "癌细胞", "肿瘤医院", 
                      "骨癌", "肺癌", "胃癌", "肝癌", "乳腺癌", "肠癌", "胰腺癌", "甲状腺癌",
                      "鼻咽癌", "前列腺癌", "淋巴瘤", "脑癌", "食管癌", "胆囊癌", "胆管癌"]
        }
        
        # 症状关键词与科室映射
        self.symptom_department_map = {
            # 儿科症状
            "发烧": "儿科",
            "咳嗽": "儿科",
            "腹泻": "儿科",
            "感冒": "儿科",
            # 妇产科症状
            "停经": "妇产科",
            "腹痛": "妇产科",
            "胎动": "妇产科",
            # 男科症状
            "尿频": "男科",
            "尿急": "男科",
            # 内科症状
            "胸闷": "内科",
            "气短": "内科",
            "头晕": "内科",
            "头痛": "内科",
            "恶心": "内科",
            "呕吐": "内科",
            # 外科症状
            "伤口": "外科",
            "疼痛": "外科",
            "肿胀": "外科",
            # 肿瘤科症状
            "肿块": "肿瘤科",
            "消瘦": "肿瘤科"
        }
    
    def recognize_department(self, query: str) -> Tuple[List[str], float]:
        """识别用户问题所属科室
        
        Args:
            query: 用户问题
            
        Returns:
            (departments, confidence) - 科室列表和置信度
        """
        query_lower = query.lower()
        
        department_scores = {}
        
        # 检查科室关键词
        for department, keywords in self.department_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in query_lower:
                    score += 1
            
            if score > 0:
                # 计算置信度：基于匹配关键词数量，但使用更宽松的公式
                # 至少匹配1个关键词就有基础置信度0.3，每多匹配一个增加0.1
                base_confidence = 0.3
                confidence_increment = min(score * 0.1, 0.7)
                confidence = min(base_confidence + confidence_increment, 1.0)
                department_scores[department] = confidence
        
        # 检查症状关键词
        for symptom, department in self.symptom_department_map.items():
            if symptom in query_lower:
                if department not in department_scores:
                    department_scores[department] = 0.3
                else:
                    department_scores[department] += 0.2
        
        # 按置信度排序
        sorted_departments = sorted(
            department_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # 返回置信度 >= 0.3 的科室
        result = [(dept, score) for dept, score in sorted_departments if score >= 0.3]
        
        if not result:
            return [], 0.0
        
        departments = [dept for dept, _ in result]
        max_confidence = max(score for _, score in result)
        
        return departments, max_confidence
    
    def extract_symptoms(self, query: str) -> List[str]:
        """提取用户问题中的症状"""
        symptoms = []
        query_lower = query.lower()
        
        for symptom in self.symptom_department_map.keys():
            if symptom in query_lower:
                symptoms.append(symptom)
        
        return symptoms
    
    def get_all_departments(self) -> List[str]:
        """获取所有科室列表"""
        return list(self.department_keywords.keys())


# 全局科室意图识别器实例
department_intent_recognizer = DepartmentIntentRecognizer()