"""医疗RAG检索器 - 支持科室级别的独立Collection检索，集成BM25混合检索和重排"""
from typing import Dict, List, Optional, Any, Tuple
import hashlib
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document

from src.rag.text2vec_embedding import text2vec_embedding
from src.rag.medical_vector_store import medical_vector_store
from src.rag.medical_knowledge_manager import medical_knowledge_manager
from src.rag.department_intent_recognizer import department_intent_recognizer
from src.rag.reranker import reranker


class MedicalRetriever:
    """医疗领域专用RAG检索器 - 支持科室级别路由、BM25混合检索和重排"""
    
    def __init__(self, bm25_weight: float = 0.5):
        self.embedding_engine = text2vec_embedding
        self.vector_store = medical_vector_store
        self.knowledge_manager = medical_knowledge_manager
        self.department_recognizer = department_intent_recognizer
        self.reranker = reranker
        self.embedding_dim = self.embedding_engine.get_embedding_dim()
        self.bm25_weight = bm25_weight
        self.bm25_retrievers: Dict[str, BM25Retriever] = {}
        self._init_bm25_retrievers()
    
    def _init_bm25_retrievers(self):
        """初始化各科室的BM25检索器"""
        departments = ["儿科", "妇产科", "男科", "内科", "外科", "肿瘤科"]
        
        for dept in departments:
            docs = self._get_docs_for_department(dept)
            if docs:
                langchain_docs = [
                    Document(
                        page_content=doc.get('content', ''),
                        metadata=doc.get('metadata', {})
                    ) for doc in docs
                ]
                bm25_retriever = BM25Retriever.from_documents(langchain_docs)
                bm25_retriever.k = 15
                self.bm25_retrievers[dept] = bm25_retriever
                print(f"✓ 初始化{dept} BM25检索器: {len(docs)}条文档")
    
    def _get_docs_for_department(self, department: str) -> List[Dict[str, Any]]:
        """获取指定科室的所有文档"""
        try:
            collection = self.vector_store.get_collection(department)
            
            # 加载Collection（幂等操作，已加载时不会重复加载）
            collection.load()
            
            # 获取所有实体
            results = collection.query(
                expr="",
                output_fields=["id", "content", "metadata", "source_type", "department"],
                limit=10000
            )
            
            docs = []
            for res in results:
                # 解析metadata（可能是JSON字符串）
                metadata = res.get("metadata", "")
                if isinstance(metadata, str):
                    try:
                        import json
                        metadata = json.loads(metadata)
                    except:
                        metadata = {}
                
                docs.append({
                    "id": res.get("id", ""),
                    "content": res.get("content", ""),
                    "metadata": metadata if isinstance(metadata, dict) else {},
                    "source_type": res.get("source_type", ""),
                    "department": res.get("department", "")
                })
            
            return docs
        except Exception as e:
            print(f"获取{department}文档失败: {e}")
            return []
    
    def retrieve(self, query: str, k: int = 5, departments: Optional[List[str]] = None, 
                 use_rerank: bool = True, keep_loaded: bool = True) -> List[Dict[str, Any]]:
        """检索医疗知识库（支持BM25混合检索和重排）
        
        Args:
            query: 用户查询
            k: 返回数量
            departments: 指定检索的科室列表（可选，不指定则自动识别）
            use_rerank: 是否使用重排
            keep_loaded: 是否保持Collection加载状态（True适合测试，False适合释放内存）
            
        Returns:
            包含来源标注的检索结果列表
        """
        active_kb = self.knowledge_manager.get_active_knowledge_base()
        if not active_kb:
            return []
        
        if departments is None or len(departments) == 0:
            departments, confidence = self.department_recognizer.recognize_department(query)
            print(f"[医疗RAG] 自动识别科室: {departments}, 置信度: {confidence}")
        
        if not departments:
            departments = self.department_recognizer.get_all_departments()
            print(f"[医疗RAG] 未识别到科室，搜索所有科室: {departments}")
        
        query_vector = self.embedding_engine.embed(query)
        
        # 混合检索：向量检索 + BM25检索
        all_results = []
        
        for dept in departments:
            # 向量检索
            vector_results = self.vector_store.search(dept, query_vector, top_k=k, keep_loaded=keep_loaded)
            for res in vector_results:
                res['retrieval_type'] = 'vector'
            
            # BM25检索
            bm25_results = []
            if dept in self.bm25_retrievers:
                bm25_docs = self.bm25_retrievers[dept].invoke(query)
                for doc in bm25_docs:
                    bm25_results.append({
                        "id": doc.metadata.get("id", ""),
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "source_type": doc.metadata.get("source_type", "document"),
                        "department": dept,
                        "retrieval_type": 'bm25'
                    })
            
            # 合并结果
            all_results.extend(vector_results)
            all_results.extend(bm25_results)
        
        # 去重
        seen = set()
        unique_results = []
        for result in all_results:
            content = result.get("content", "")
            if content not in seen and content:
                seen.add(content)
                unique_results.append(result)
        
        # 重排
        if use_rerank and unique_results:
            unique_results = self.reranker.rerank(query, unique_results, top_k=min(k * 2, len(unique_results)))
        
        # 最终筛选和格式化
        output = []
        for i, result in enumerate(unique_results[:k]):
            doc_id = self._generate_doc_id(result)
            source_info = self._extract_source_info(result)
            
            output.append({
                "id": doc_id,
                "content": result.get("content", ""),
                "metadata": result.get("metadata", {}),
                "source": source_info["source"],
                "source_type": source_info["source_type"],
                "department": result.get("department", ""),
                "confidence": self._calculate_confidence(i, len(unique_results)),
                "rerank_score": result.get("rerank_score", 0.0),
                "retrieval_type": result.get("retrieval_type", "unknown")
            })
        
        return output
    
    def retrieve_by_department(self, query: str, department: str, k: int = 5, 
                               use_rerank: bool = True, keep_loaded: bool = True) -> List[Dict[str, Any]]:
        """检索指定科室的知识库
        
        Args:
            query: 用户查询
            department: 科室名称
            k: 返回数量
            use_rerank: 是否使用重排
            keep_loaded: 是否保持Collection加载状态
        """
        active_kb = self.knowledge_manager.get_active_knowledge_base()
        if not active_kb:
            return []
        
        query_vector = self.embedding_engine.embed(query)
        
        # 向量检索
        vector_results = self.vector_store.search(department, query_vector, k=k, keep_loaded=keep_loaded)
        for res in vector_results:
            res['retrieval_type'] = 'vector'
        
        # BM25检索
        bm25_results = []
        if department in self.bm25_retrievers:
            bm25_docs = self.bm25_retrievers[department].invoke(query)
            for doc in bm25_docs:
                bm25_results.append({
                    "id": doc.metadata.get("id", ""),
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "source_type": doc.metadata.get("source_type", "document"),
                    "department": department,
                    "retrieval_type": 'bm25'
                })
        
        # 合并去重
        all_results = vector_results + bm25_results
        seen = set()
        unique_results = []
        for result in all_results:
            content = result.get("content", "")
            if content not in seen and content:
                seen.add(content)
                unique_results.append(result)
        
        # 重排
        if use_rerank and unique_results:
            unique_results = self.reranker.rerank(query, unique_results, top_k=min(k * 2, len(unique_results)))
        
        # 格式化输出
        output = []
        for i, result in enumerate(unique_results[:k]):
            doc_id = self._generate_doc_id(result)
            source_info = self._extract_source_info(result)
            
            output.append({
                "id": doc_id,
                "content": result.get("content", ""),
                "metadata": result.get("metadata", {}),
                "source": source_info["source"],
                "source_type": source_info["source_type"],
                "department": department,
                "confidence": self._calculate_confidence(i, len(unique_results)),
                "rerank_score": result.get("rerank_score", 0.0),
                "retrieval_type": result.get("retrieval_type", "unknown")
            })
        
        return output
    
    def recognize_department(self, query: str) -> Tuple[List[str], float]:
        """识别用户问题所属科室"""
        return self.department_recognizer.recognize_department(query)
    
    def _generate_doc_id(self, result: Dict[str, Any]) -> str:
        """生成文档唯一ID"""
        content = result.get("content", "") or ""
        content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()[:8]
        source = result.get("metadata", {}).get("source", "unknown") or "unknown"
        source_hash = hashlib.md5(source.encode('utf-8')).hexdigest()[:4]
        return f"MED-{content_hash}-{source_hash}"
    
    def _extract_source_info(self, result: Dict[str, Any]) -> Dict[str, str]:
        """提取来源信息"""
        metadata = result.get("metadata", {}) or {}
        source = metadata.get("source", "") or ""
        source_type = result.get("source_type", "unknown") or "unknown"
        
        if not source or source == 'unknown':
            source = metadata.get("filename", "未知来源")
        
        source_type_mapping = {
            'guideline': '医学指南',
            'manual': '诊疗手册',
            'prescription': '药品说明书',
            'nursing': '护理规范',
            'public_health': '公共卫生知识',
            'document': '文档'
        }
        
        return {
            "source": source,
            "source_type": source_type_mapping.get(source_type.lower(), source_type)
        }
    
    def _calculate_confidence(self, rank: int, total: int) -> float:
        """计算置信度（基于排名）"""
        if total == 0:
            return 0.0
        base_score = (total - rank) / total
        return round(base_score * 0.8 + 0.2, 2)
    
    def get_collection_size(self, department: Optional[str] = None) -> int:
        """获取医疗向量库文档数量"""
        return self.vector_store.get_size(department)
    
    def get_collections(self) -> List[str]:
        """获取所有科室Collection列表"""
        return self.vector_store.get_collections()
    
    def check_collection_exists(self) -> bool:
        """检查医疗向量库是否存在"""
        try:
            collections = self.get_collections()
            return len(collections) > 0
        except Exception:
            return False
    
    def refresh_bm25_index(self, department: str = None):
        """刷新BM25索引"""
        if department:
            if department in self.bm25_retrievers:
                del self.bm25_retrievers[department]
            docs = self._get_docs_for_department(department)
            if docs:
                langchain_docs = [
                    Document(
                        page_content=doc.get('content', ''),
                        metadata=doc.get('metadata', {})
                    ) for doc in docs
                ]
                bm25_retriever = BM25Retriever.from_documents(langchain_docs)
                bm25_retriever.k = 15
                self.bm25_retrievers[department] = bm25_retriever
                print(f"✓ 刷新{department} BM25检索器: {len(docs)}条文档")
        else:
            self.bm25_retrievers.clear()
            self._init_bm25_retrievers()
    
    def release_collections(self, department: str = None):
        """释放Collection以释放内存
        
        Args:
            department: 科室名称，为None则释放所有已加载的Collection
        """
        self.vector_store.release_collection(department)
    
    def get_collection_status(self) -> Dict[str, str]:
        """获取所有Collection的加载状态
        
        Returns:
            Dict[str, str]: 科室名称 -> 状态描述
        """
        status = {}
        for dept in ["儿科", "妇产科", "男科", "内科", "外科", "肿瘤科"]:
            try:
                collection = self.vector_store.get_collection(dept)
                status[dept] = "已加载"
            except Exception as e:
                status[dept] = f"错误: {str(e)[:20]}"
        return status


# 全局医疗检索器实例
medical_retriever = MedicalRetriever(bm25_weight=0.5)