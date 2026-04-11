"""重排模块"""
from typing import Dict, List, Optional, Any
import os
import time
from src.config.config import settings

# 尝试导入requests模块
has_requests = False
try:
    import requests
    has_requests = True
    print("已导入requests模块")
except ImportError:
    print("警告: 无法导入requests模块，将使用urllib替代")
    has_requests = False


class Reranker:
    """重排器类"""
    
    def __init__(self, model_name: str = "gte-rerank-v2"):
        """初始化重排器
        
        Args:
            model_name: 模型名称
        """
        self.model_name = model_name
        self.api_key = self._get_api_key()
        self.api_url = "https://dashscope.aliyuncs.com/api/v1/services/rerank/text-rerank/text-rerank"
    
    def _get_api_key(self) -> str:
        """获取API密钥
        
        Returns:
            str: API密钥
        """
        # 优先使用DASHSCOPE_API_KEY
        api_key = os.getenv('DASHSCOPE_API_KEY')
        if api_key:
            return api_key
        
        # 其次使用QIANWEN_API_KEY
        api_key = os.getenv('QIANWEN_API_KEY')
        if api_key:
            return api_key
        
        # 最后使用配置文件中的密钥
        return getattr(settings, 'dashscope_api_key', '') or getattr(settings, 'qianwen_api_key', '')
    
    def rerank(self, query: str, documents: List[Dict[str, Any]], top_k: int = 3) -> List[Dict[str, Any]]:
        """重排文档
        
        Args:
            query: 查询文本
            documents: 文档列表
            top_k: 返回结果数量
            
        Returns:
            List[Dict[str, Any]]: 重排结果
        """
        if not documents:
            return []
        
        # 尝试使用API重排
        try:
            return self._api_rerank(query, documents, top_k)
        except Exception as e:
            print(f"API重排失败: {e}")
            # 尝试使用LLM重排
            try:
                return self._llm_rerank(query, documents, top_k)
            except Exception as e:
                print(f"LLM重排失败: {e}")
                # 使用本地重排
                return self._local_rerank(query, documents, top_k)
    
    def _api_rerank(self, query: str, documents: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        """使用API重排
        
        Args:
            query: 查询文本
            documents: 文档列表
            top_k: 返回结果数量
            
        Returns:
            List[Dict[str, Any]]: 重排结果
        """
        if not self.api_key:
            raise ValueError("未配置API密钥")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 准备文档
        rerank_docs = []
        for doc in documents:
            rerank_docs.append(doc.get('text', ''))
        
        # 根据模型类型使用不同的请求格式
        if self.model_name == "gte-rerank-v2":
            # gte-rerank-v2模型使用input和parameters对象
            data = {
                "model": self.model_name,
                "input": {
                    "query": query,
                    "documents": rerank_docs
                },
                "parameters": {
                    "top_n": top_k,
                    "return_documents": False
                }
            }
        else:
            # qwen3-rerank模型直接在顶层设置参数
            data = {
                "model": self.model_name,
                "query": query,
                "documents": rerank_docs,
                "top_n": top_k
            }
        
        # 重试机制
        max_retries = 3
        for i in range(max_retries):
            try:
                if has_requests:
                    # 使用requests
                    response = requests.post(self.api_url, headers=headers, json=data, timeout=30)
                    response.raise_for_status()
                    result = response.json()
                else:
                    # 使用urllib替代
                    import urllib.request
                    import urllib.error
                    import urllib.parse
                    import json
                    
                    data_json = json.dumps(data).encode('utf-8')
                    req = urllib.request.Request(
                        self.api_url,
                        data=data_json,
                        headers=headers,
                        method='POST'
                    )
                    with urllib.request.urlopen(req, timeout=30) as response:
                        result = json.loads(response.read().decode('utf-8'))
                
                # 解析响应
                reranked = []
                for item in result.get('output', {}).get('results', []):
                    # 找到原始文档
                    original_doc = None
                    doc_index = item.get('index', -1)
                    if 0 <= doc_index < len(documents):
                        original_doc = documents[doc_index]
                    
                    if original_doc:
                        original_doc['rerank_score'] = item.get('relevance_score', 0.0)
                        reranked.append(original_doc)
                
                return reranked
            except Exception as e:
                print(f"API调用失败 (尝试 {i+1}/{max_retries}): {e}")
                if i < max_retries - 1:
                    time.sleep(2 ** i)  # 指数退避
                else:
                    raise
    
    def _llm_rerank(self, query: str, documents: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        """使用LLM重排
        
        Args:
            query: 查询文本
            documents: 文档列表
            top_k: 返回结果数量
            
        Returns:
            List[Dict[str, Any]]: 重排结果
        """
        from src.agent.model_engine import model_engine
        
        # 构建提示词
        prompt = f"请对以下文档与查询的相关性进行评分，评分范围为0-10，10表示最相关。\n\n查询: {query}\n\n文档:\n"
        
        for i, doc in enumerate(documents):
            prompt += f"{i+1}. {doc.get('text', '')}\n\n"
        
        prompt += "请按照相关性从高到低的顺序返回文档编号和评分，格式为：\n1. 文档编号: 评分\n2. 文档编号: 评分\n..."
        
        # 调用大模型
        request = {
            "model": settings.model_type,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "stream": False,
            "user_id": "system"
        }
        
        response = model_engine.generate(request)
        content = response.get("content", "")
        
        # 解析响应
        scores = {}
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if ': ' in line:
                parts = line.split(': ')
                if len(parts) == 2:
                    try:
                        doc_idx = int(parts[0].split('.')[0]) - 1
                        score = float(parts[1])
                        if 0 <= doc_idx < len(documents):
                            scores[doc_idx] = score
                    except Exception:
                        pass
        
        # 排序
        reranked = []
        for idx, score in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]:
            documents[idx]['rerank_score'] = score / 10.0  # 归一化到0-1
            reranked.append(documents[idx])
        
        return reranked
    
    def _local_rerank(self, query: str, documents: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        """本地重排
        
        Args:
            query: 查询文本
            documents: 文档列表
            top_k: 返回结果数量
            
        Returns:
            List[Dict[str, Any]]: 重排结果
        """
        # 计算文本相似度
        import re
        from src.rag.embedding_engine import embedding_engine
        
        # 向量化查询
        query_vector = embedding_engine.embed(query)
        
        # 计算每个文档与查询的相似度
        for doc in documents:
            text = doc.get('text', '')
            doc_vector = embedding_engine.embed(text)
            
            # 计算余弦相似度
            similarity = self._cosine_similarity(query_vector, doc_vector)
            doc['rerank_score'] = similarity
        
        # 排序
        documents.sort(key=lambda x: x.get('rerank_score', 0.0), reverse=True)
        
        return documents[:top_k]
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度
        
        Args:
            vec1: 向量1
            vec2: 向量2
            
        Returns:
            float: 余弦相似度
        """
        # 计算点积
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        
        # 计算模长
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        
        # 避免除以零
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)


# 全局重排器实例
reranker = Reranker()