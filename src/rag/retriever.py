"""检索引擎模块 - 使用LangChain的EnsembleRetriever混合检索"""
from typing import Dict, List, Optional, Any
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from src.rag.embedding_engine import embedding_engine
from src.rag.vector_store import vector_store


class MilvusVectorRetriever(BaseRetriever):
    """基于Milvus的向量检索器 - 适配LangChain接口"""
    
    vector_store: Any
    embedding_engine: Any
    k: int = 5
    
    def __init__(self, vector_store, embedding_engine, k: int = 5):
        super().__init__()
        self.__dict__['vector_store'] = vector_store
        self.__dict__['embedding_engine'] = embedding_engine
        self.__dict__['k'] = k
    
    def _get_relevant_documents(self, query: str, run_manager: Optional[CallbackManagerForRetrieverRun] = None) -> List[Document]:
        """检索相关文档"""
        query_vector = self.embedding_engine.embed(query)
        results = self.vector_store.search(query_vector, k=self.k)
        
        documents = []
        for result in results:
            documents.append(Document(
                page_content=result.get('text', ''),
                metadata=result.get('metadata', {})
            ))
        
        return documents


class Retriever:
    """基于LangChain EnsembleRetriever的混合检索引擎"""
    
    def __init__(self):
        """初始化检索引擎"""
        self.embedding_engine = embedding_engine
        self.vector_store = vector_store
        
        # 加载所有文档
        self.all_docs = self.vector_store.get_all()
        self.total_docs = len(self.all_docs)
        
        # 初始化LangChain检索器
        self._init_retrievers()
        
        print(f"✓ 检索器初始化完成: 文档数={self.total_docs}")
    
    def _init_retrievers(self):
        """初始化LangChain检索器"""
        if self.total_docs == 0:
            self.ensemble_retriever = None
            return
        
        # 将文档转换为LangChain Document格式
        langchain_docs = []
        for doc in self.all_docs:
            langchain_docs.append(Document(
                page_content=doc.get('text', ''),
                metadata=doc.get('metadata', {})
            ))
        
        # 初始化BM25检索器
        self.bm25_retriever = BM25Retriever.from_documents(langchain_docs)
        self.bm25_retriever.k = 5
        
        # 初始化Milvus向量检索器（使用自定义实现适配LangChain）
        self.milvus_retriever = MilvusVectorRetriever(self.vector_store, self.embedding_engine, k=5)
        
        # 创建EnsembleRetriever混合检索器
        self.ensemble_retriever = EnsembleRetriever(
            retrievers=[self.bm25_retriever, self.milvus_retriever],
            weights=[0.3, 0.7]
        )
    
    def retrieve(self, query: str, k: int = 3, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """检索相关文档"""
        if self.total_docs == 0 or self.ensemble_retriever is None:
            return []
        
        # 使用EnsembleRetriever进行混合检索
        results = self.ensemble_retriever.invoke(query)
        
        # 转换结果格式
        output = []
        for doc in results[:k]:
            output.append({
                "id": doc.metadata.get('id', ''),
                "text": doc.page_content,
                "metadata": doc.metadata,
                "score": doc.metadata.get('score', 0.0)
            })
        
        # 应用过滤
        if filters:
            output = self._filter_results(output, filters)
        
        return output
    
    def _filter_results(self, results: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """过滤结果"""
        filtered = []
        
        for result in results:
            metadata = result.get('metadata', {})
            match = True
            
            if 'tags' in filters:
                doc_tags = metadata.get('tags', [])
                if not any(tag in doc_tags for tag in filters['tags']):
                    match = False
            
            if 'permissions' in filters:
                doc_permissions = metadata.get('permissions', ['public'])
                if not any(perm in doc_permissions for perm in filters['permissions']):
                    match = False
            
            if match:
                filtered.append(result)
        
        return filtered


retriever = Retriever()