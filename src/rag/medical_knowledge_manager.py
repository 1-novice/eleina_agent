"""医疗知识库管理器 - 支持动态接入/切换不同医疗知识库"""
from typing import Dict, List, Optional, Any
import os
import json

class MedicalKnowledgeBase:
    """医疗知识库对象"""
    
    def __init__(self, domain: str, name: str, description: str, vector_store_path: str, document_paths: List[str]):
        self.domain = domain  # 医疗细分领域标识
        self.name = name      # 知识库名称
        self.description = description  # 知识库描述
        self.vector_store_path = vector_store_path  # 向量存储路径
        self.document_paths = document_paths  # 原始文档路径列表
        self.activated = False  # 是否激活
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain,
            "name": self.name,
            "description": self.description,
            "vector_store_path": self.vector_store_path,
            "document_paths": self.document_paths,
            "activated": self.activated
        }


class MedicalKnowledgeManager:
    """医疗知识库管理器 - 支持动态接入/切换"""
    
    def __init__(self):
        self.knowledge_bases: Dict[str, MedicalKnowledgeBase] = {}  # domain -> MedicalKnowledgeBase
        self.active_domain: Optional[str] = None  # 当前激活的领域
        self.config_path = os.path.join(os.path.dirname(__file__), "medical_kb_config.json")
        self._load_config()
    
    def _load_config(self):
        """加载知识库配置"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    for domain, kb_data in config.items():
                        self.knowledge_bases[domain] = MedicalKnowledgeBase(
                            domain=kb_data["domain"],
                            name=kb_data["name"],
                            description=kb_data["description"],
                            vector_store_path=kb_data["vector_store_path"],
                            document_paths=kb_data["document_paths"]
                        )
                print(f"✓ 加载医疗知识库配置: {list(self.knowledge_bases.keys())}")
            except Exception as e:
                print(f"✗ 加载知识库配置失败: {e}")
    
    def _save_config(self):
        """保存知识库配置"""
        config = {kb.domain: kb.to_dict() for kb in self.knowledge_bases.values()}
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    def add_knowledge_base(self, domain: str, name: str, description: str, 
                          vector_store_path: str, document_paths: List[str]) -> bool:
        """添加新的医疗知识库"""
        if domain in self.knowledge_bases:
            print(f"⚠ 领域 {domain} 已存在")
            return False
        
        kb = MedicalKnowledgeBase(
            domain=domain,
            name=name,
            description=description,
            vector_store_path=vector_store_path,
            document_paths=document_paths
        )
        self.knowledge_bases[domain] = kb
        self._save_config()
        print(f"✓ 添加医疗知识库: {domain}")
        return True
    
    def remove_knowledge_base(self, domain: str) -> bool:
        """移除医疗知识库"""
        if domain not in self.knowledge_bases:
            print(f"⚠ 领域 {domain} 不存在")
            return False
        
        # 如果移除的是当前激活的领域，需要取消激活
        if self.active_domain == domain:
            self.active_domain = None
        
        del self.knowledge_bases[domain]
        self._save_config()
        print(f"✓ 移除医疗知识库: {domain}")
        return True
    
    def activate_domain(self, domain: str) -> bool:
        """激活指定医疗领域"""
        if domain not in self.knowledge_bases:
            print(f"⚠ 领域 {domain} 不存在")
            return False
        
        # 取消之前激活的领域
        if self.active_domain and self.active_domain != domain:
            self.knowledge_bases[self.active_domain].activated = False
        
        self.active_domain = domain
        self.knowledge_bases[domain].activated = True
        print(f"✓ 激活医疗领域: {domain}")
        return True
    
    def deactivate_domain(self) -> bool:
        """取消当前激活的医疗领域"""
        if not self.active_domain:
            print("⚠ 没有激活的领域")
            return False
        
        self.knowledge_bases[self.active_domain].activated = False
        self.active_domain = None
        print("✓ 已取消激活所有医疗领域")
        return True
    
    def get_active_knowledge_base(self) -> Optional[MedicalKnowledgeBase]:
        """获取当前激活的知识库"""
        if not self.active_domain:
            return None
        return self.knowledge_bases.get(self.active_domain)
    
    def get_all_domains(self) -> List[str]:
        """获取所有已接入的医疗领域"""
        return list(self.knowledge_bases.keys())
    
    def get_knowledge_base(self, domain: str) -> Optional[MedicalKnowledgeBase]:
        """获取指定领域的知识库"""
        return self.knowledge_bases.get(domain)


medical_knowledge_manager = MedicalKnowledgeManager()