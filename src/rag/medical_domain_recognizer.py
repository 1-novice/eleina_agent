"""医疗领域识别器 - 判断用户问题是否属于医疗领域"""
from typing import Dict, List, Optional, Tuple
import re

class MedicalDomainRecognizer:
    """医疗领域识别器"""
    
    def __init__(self):
        # 医疗领域关键词词典
        self.medical_keywords = {
            # 疾病相关
            "disease": ["高血压", "糖尿病", "心脏病", "癌症", "癌", "肿瘤", "肺炎", "感冒", "发烧", "头痛", 
                       "咳嗽", "胃痛", "关节炎", "哮喘", "抑郁症", "失眠", "贫血", "过敏",
                       "骨癌", "肺癌", "胃癌", "肝癌", "乳腺癌", "肠癌", "胰腺癌", "甲状腺癌",
                       "鼻咽癌", "前列腺癌", "淋巴瘤", "脑癌", "食管癌", "胆囊癌", "胆管癌"],
            # 症状相关
            "symptom": ["症状", "疼痛", "发烧", "咳嗽", "头痛", "头晕", "恶心", "呕吐", 
                       "乏力", "心悸", "胸闷", "呼吸困难", "腹泻", "便秘", "皮疹"],
            # 药品相关
            "medicine": ["药", "药物", "阿莫西林", "阿司匹林", "布洛芬", "抗生素", 
                        "感冒药", "退烧药", "止痛药", "降压药", "降糖药", "处方"],
            # 诊疗相关
            "treatment": ["治疗", "手术", "化疗", "放疗", "针灸", "按摩", "理疗", 
                         "康复", "诊断", "检查", "化验", "B超", "CT", "MRI"],
            # 护理相关
            "nursing": ["护理", "护理操作", "术后护理", "康复护理", "居家护理", 
                       "伤口护理", "饮食护理", "用药指导"],
            # 医学检查相关
            "examination": ["检查", "化验", "血常规", "尿常规", "心电图", "血压", 
                           "血糖", "血脂", "肝功能", "肾功能"],
            # 医疗术语
            "medical_term": ["血压", "血糖", "血脂", "心率", "脉搏", "体温", "血氧", 
                           "白细胞", "红细胞", "血小板", "胆固醇", "尿酸"]
        }
        
        # 医疗问题模式
        self.medical_patterns = [
            r".*什么是.*病",
            r".*如何治疗.*",
            r".*怎么治.*",
            r".*吃什么药.*",
            r".*用药.*",
            r".*副作用.*",
            r".*禁忌.*",
            r".*注意事项.*",
            r".*诊断.*",
            r".*检查.*",
            r".*症状.*",
            r".*并发症.*",
            r".*术后.*",
            r".*护理.*",
            r".*预防.*",
            r".*疫苗.*"
        ]
    
    def detect_medical_domain(self, query: str) -> Tuple[bool, Optional[str], float]:
        """检测用户问题是否属于医疗领域
        
        Args:
            query: 用户输入
            
        Returns:
            (is_medical, domain, confidence)
        """
        query_lower = query.lower()
        
        # 检查医疗问题模式
        pattern_matches = 0
        for pattern in self.medical_patterns:
            if re.search(pattern, query_lower):
                pattern_matches += 1
        
        # 检查医疗关键词
        keyword_matches = 0
        matched_categories = set()
        for category, keywords in self.medical_keywords.items():
            for keyword in keywords:
                if keyword in query_lower:
                    keyword_matches += 1
                    matched_categories.add(category)
        
        # 计算置信度
        total_matches = pattern_matches + keyword_matches
        confidence = min(total_matches / 5.0, 1.0)
        
        # 判断是否为医疗问题
        is_medical = (pattern_matches >= 1 or keyword_matches >= 2) or confidence >= 0.3
        
        # 确定具体领域
        domain = self._determine_domain(matched_categories)
        
        return is_medical, domain, confidence
    
    def _determine_domain(self, categories: set) -> Optional[str]:
        """根据匹配的关键词类别确定具体医疗领域"""
        if not categories:
            return None
        
        # 优先级排序
        domain_priority = [
            ("medicine", "用药指导"),
            ("treatment", "疾病诊疗"),
            ("nursing", "护理规范"),
            ("examination", "检查解读"),
            ("disease", "疾病知识"),
            ("symptom", "症状咨询"),
            ("medical_term", "医学术语")
        ]
        
        for category, domain_name in domain_priority:
            if category in categories:
                return domain_name
        
        return "医疗常识"
    
    def extract_medical_entities(self, query: str) -> Dict[str, List[str]]:
        """提取医疗实体"""
        entities = {
            "diseases": [],
            "symptoms": [],
            "medicines": [],
            "treatments": []
        }
        
        for category, keywords in self.medical_keywords.items():
            entity_list = entities.get(category, [])
            if category == "disease":
                entity_list = entities["diseases"]
            elif category == "symptom":
                entity_list = entities["symptoms"]
            elif category == "medicine":
                entity_list = entities["medicines"]
            elif category == "treatment":
                entity_list = entities["treatments"]
            
            for keyword in keywords:
                if keyword in query and keyword not in entity_list:
                    entity_list.append(keyword)
        
        return entities


medical_domain_recognizer = MedicalDomainRecognizer()