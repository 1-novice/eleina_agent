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
    k: int = 10

    def __init__(self, vector_store, embedding_engine, k: int = 10):
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
            # ====================== 修复 BUG：字段名从 text → content ======================
            content = result.get('content', '')
            documents.append(Document(
                page_content=content,
                metadata=result.get('metadata', {})
            ))
        return documents


class Retriever:
    """基于LangChain EnsembleRetriever的混合检索引擎"""
    
    def __init__(self, bm25_weight: float = 0.5):
        self.embedding_engine = embedding_engine
        self.vector_store = vector_store
        self.bm25_weight = bm25_weight
        self.all_docs = self.vector_store.get_all()
        self.total_docs = len(self.all_docs)
        self._init_retrievers()
        print(f"✓ 检索器初始化完成: 文档数={self.total_docs}, BM25权重={bm25_weight}")

    def _init_retrievers(self):
        if self.total_docs == 0:
            self.ensemble_retriever = None
            return

        langchain_docs = []
        for doc in self.all_docs:
            # ====================== 修复 BUG：text → content ======================
            langchain_docs.append(Document(
                page_content=doc.get('content', ''),
                metadata=doc.get('metadata', {})
            ))

        self.bm25_retriever = BM25Retriever.from_documents(langchain_docs)
        self.bm25_retriever.k = 15

        self.milvus_retriever = MilvusVectorRetriever(self.vector_store, self.embedding_engine, k=15)

        # 混合检索：BM25 + 向量各 0.5
        self.ensemble_retriever = EnsembleRetriever(
            retrievers=[self.bm25_retriever, self.milvus_retriever],
            weights=[self.bm25_weight, 1 - self.bm25_weight]
        )

    def retrieve(self, query: str, k: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        if not self.ensemble_retriever:
            return []

        # 混合检索
        results = self.ensemble_retriever.invoke(query)

        # 去重
        seen = set()
        unique = []
        for doc in results:
            if doc.page_content not in seen:
                seen.add(doc.page_content)
                unique.append(doc)
            if len(unique) >= 20:
                break

        # 格式转换
        output = []
        for doc in unique[:k]:
            output.append({
                "id": doc.metadata.get("id", ""),
                "content": doc.page_content,  # 🔥 修复：content 不是 text
                "metadata": doc.metadata,
                "score": doc.metadata.get("score", 0.0)
            })
        return output

    def _filter_results(self, results, filters):
        return results


retriever = Retriever(bm25_weight=0.5)