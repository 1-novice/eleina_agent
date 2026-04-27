"""医疗回答生成器 - 基于医疗知识库生成合规的医疗回答"""
from typing import Dict, List, Optional, Any

from src.prompt import prompt_manager


class MedicalResponseGenerator:
    """医疗回答生成器"""
    
    def __init__(self):
        self.rag_prompt_template = prompt_manager.get_prompt("rag") or """
请根据下面的参考资料回答用户问题，不要编造。
如果资料中没有答案，请直接说"根据现有资料无法回答"。

【参考资料】
{references}

【用户问题】
{query}

【回答】
"""
        self.compliance_reminder = "\n\n本回答仅基于当前接入的医疗知识库内容，不构成诊疗建议、用药指导，具体医疗问题请咨询专业医护人员。"
    
    def generate_response(self, query: str, retrieved_docs: List[Dict[str, Any]], domain_name: str) -> Dict[str, Any]:
        """生成医疗回答
        
        Args:
            query: 用户问题
            retrieved_docs: 检索到的文档列表
            domain_name: 当前医疗领域名称
            
        Returns:
            包含回答内容、来源列表、合规提醒的字典
        """
        # 无检索结果处理
        if not retrieved_docs:
            return {
                "answer": f"当前接入的【{domain_name}】知识库中无相关医疗信息，无法为你解答该问题，建议咨询专业医护人员。",
                "sources": [],
                "has_knowledge": False,
                "compliance_reminder": ""
            }
        
        # 整合多个知识片段
        integrated_content = self._integrate_documents(retrieved_docs)
        
        # 构建提示词
        references = self._format_references(retrieved_docs)
        prompt = self.rag_prompt_template.format(
            references=references,
            query=query
        )
        
        # 提取来源列表
        sources = self._extract_sources(retrieved_docs)
        
        # 构建最终回答（这里简化处理，直接使用检索到的内容）
        answer = self._build_answer(integrated_content, query)
        
        return {
            "answer": answer + self.compliance_reminder,
            "sources": sources,
            "has_knowledge": True,
            "compliance_reminder": self.compliance_reminder
        }
    
    def _integrate_documents(self, docs: List[Dict[str, Any]]) -> str:
        """整合多个文档内容（按置信度排序，去重）"""
        # 按置信度排序
        sorted_docs = sorted(docs, key=lambda x: x.get('confidence', 0), reverse=True)
        
        # 去重并保留关键内容
        seen = set()
        integrated = []
        
        for doc in sorted_docs:
            content = doc.get('content', '')
            if content not in seen:
                seen.add(content)
                integrated.append(content)
        
        return "\n\n".join(integrated)
    
    def _format_references(self, docs: List[Dict[str, Any]]) -> str:
        """格式化参考资料"""
        references = []
        for i, doc in enumerate(docs, 1):
            source = doc.get('source', '未知来源')
            doc_id = doc.get('id', f"MED-{i}")
            content = doc.get('content', '')
            
            reference = f"{i}. 【来源：{source}】【ID：{doc_id}】\n{content}"
            references.append(reference)
        
        return "\n\n".join(references)
    
    def _extract_sources(self, docs: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """提取来源列表"""
        sources = []
        seen_sources = set()
        
        for doc in docs:
            source_key = (doc.get('source', ''), doc.get('id', ''))
            if source_key not in seen_sources:
                seen_sources.add(source_key)
                sources.append({
                    "id": doc.get('id', ''),
                    "source": doc.get('source', ''),
                    "source_type": doc.get('source_type', '')
                })
        
        return sources
    
    def _build_answer(self, content: str, query: str) -> str:
        """构建回答内容"""
        # 简单处理：直接使用整合后的内容
        # 实际应用中可以调用LLM进行内容总结和回答生成
        return content


medical_response_generator = MedicalResponseGenerator()