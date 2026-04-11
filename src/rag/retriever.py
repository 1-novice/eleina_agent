"""检索引擎模块"""
from typing import Dict, List, Optional, Any
import re
import math
from src.rag.embedding_engine import embedding_engine
from src.rag.vector_store import vector_store


class Retriever:
    """检索引擎类"""
    
    def __init__(self):
        """初始化检索引擎"""
        self.embedding_engine = embedding_engine
        self.vector_store = vector_store
        
        # 全局预缓存
        self._precache()
    
    def _precache(self):
        """预缓存数据，提高检索速度"""
        # 1. 加载所有文档
        self.all_docs = self.vector_store.get_all()
        self.total_docs = len(self.all_docs)
        
        # 2. 预计算文档长度
        self.doc_lengths = []
        total_length = 0
        for doc in self.all_docs:
            length = len(doc.get('text', '').split())
            self.doc_lengths.append(length)
            total_length += length
        
        # 3. 计算平均文档长度
        self.avg_doc_length = total_length / self.total_docs if self.total_docs > 0 else 0
        
        # 4. 缓存停用词（先定义，再使用）
        self.stop_words = set([
            '的', '了', '和', '是', '在', '有', '我', '他', '她', '它', '们',
            '这', '那', '你', '我', '他', '她', '它', '我们', '你们', '他们',
            '是', '在', '有', '为', '以', '于', '上', '下', '时', '中', '间',
            '到', '从', '向', '对', '就', '都', '而', '及', '与', '着', '或',
            '一个', '一种', '一些', '这个', '那个', '这些', '那些'
        ])
        
        # 5. 预建BM25倒排索引
        self.inverted_index = self._build_inverted_index()
        
        print(f"预缓存完成: 文档数={self.total_docs}, 平均长度={self.avg_doc_length:.2f}")
    
    def _build_inverted_index(self):
        """构建BM25倒排索引"""
        inverted_index = {}
        
        for doc_id, doc in enumerate(self.all_docs):
            text = doc.get('text', '').lower()
            words = text.split()
            # 去除停用词
            words = [word for word in words if word not in self.stop_words and len(word) > 1]
            
            for word in words:
                if word not in inverted_index:
                    inverted_index[word] = set()
                inverted_index[word].add(doc_id)
        
        return inverted_index
    
    def retrieve(self, query: str, k: int = 3, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """检索相关文档
        
        Args:
            query: 查询文本
            k: 返回结果数量
            filters: 过滤条件
            
        Returns:
            List[Dict[str, Any]]: 检索结果
        """
        # 1. 查询理解
        processed_query = self._process_query(query)
        
        # 2. 并行执行向量召回和关键词召回
        import concurrent.futures
        vector_results = []
        keyword_results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            # 提交向量检索任务
            vector_future = executor.submit(self._vector_retrieval, processed_query, k * 2)
            # 提交关键词检索任务
            keyword_future = executor.submit(self._keyword_retrieval, processed_query, k * 2)
            
            # 获取结果
            vector_results = vector_future.result()
            keyword_results = keyword_future.result()
        
        # 3. 多路召回融合
        merged_results = self._merge_results(vector_results, keyword_results)
        
        # 4. 过滤
        if filters:
            merged_results = self._filter_results(merged_results, filters)
        
        # 5. 排序
        sorted_results = self._sort_results(merged_results, k)
        
        return sorted_results
    
    def _process_query(self, query: str) -> str:
        """处理查询
        
        Args:
            query: 查询文本
            
        Returns:
            str: 处理后的查询
        """
        # 去除标点符号（使用Python兼容的正则表达式）
        query = re.sub(r'[\W_]', ' ', query)
        # 转为小写
        query = query.lower()
        # 去除多余空格
        query = ' '.join(query.split())
        return query
    
    def _vector_retrieval(self, query: str, k: int) -> List[Dict[str, Any]]:
        """向量检索
        
        Args:
            query: 查询文本
            k: 返回结果数量
            
        Returns:
            List[Dict[str, Any]]: 检索结果
        """
        try:
            # 向量化查询
            query_vector = self.embedding_engine.embed(query)
            # 搜索
            results = self.vector_store.search(query_vector, k)
            # 添加检索类型
            for result in results:
                result['retrieval_type'] = 'vector'
            return results
        except Exception as e:
            print(f"向量检索失败: {e}")
            return []
    
    def _keyword_retrieval(self, query: str, k: int) -> List[Dict[str, Any]]:
        """关键词检索
        
        Args:
            query: 查询文本
            k: 返回结果数量
            
        Returns:
            List[Dict[str, Any]]: 检索结果
        """
        try:
            # 提取关键词
            keywords = self._extract_keywords(query)
            
            if not keywords:
                return []
            
            # 使用倒排索引获取相关文档
            relevant_doc_ids = set()
            for keyword in keywords:
                if keyword in self.inverted_index:
                    relevant_doc_ids.update(self.inverted_index[keyword])
            
            if not relevant_doc_ids:
                return []
            
            # 计算BM25得分
            results = []
            for doc_id in relevant_doc_ids:
                if doc_id < len(self.all_docs):
                    doc = self.all_docs[doc_id]
                    text = doc.get('text', '')
                    score = self._bm25_score(text, keywords, doc_id)
                    if score > 0:
                        results.append({
                            "id": doc.get('id', ''),
                            "text": text,
                            "metadata": doc.get('metadata', {}),
                            "score": score,
                            "retrieval_type": "keyword"
                        })
            
            # 按得分排序
            results.sort(key=lambda x: x.get('score', 0), reverse=True)
            
            # 限制返回数量
            return results[:k]
        except Exception as e:
            print(f"关键词检索失败: {e}")
            return []
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词
        
        Args:
            text: 文本
            
        Returns:
            List[str]: 关键词列表
        """
        # 简单的关键词提取
        words = text.split()
        # 去除停用词（使用预缓存的停用词）
        keywords = [word for word in words if word not in self.stop_words and len(word) > 1]
        return keywords[:5]  # 取前5个关键词
    
    def _bm25_score(self, text: str, keywords: List[str], doc_id: int) -> float:
        """计算BM25得分
        
        Args:
            text: 文本
            keywords: 关键词列表
            doc_id: 文档ID
            
        Returns:
            float: BM25得分
        """
        if not keywords:
            return 0.0
        
        # 使用预缓存的文档长度和平均文档长度
        doc_length = self.doc_lengths[doc_id] if doc_id < len(self.doc_lengths) else 0
        avg_doc_length = self.avg_doc_length
        
        if avg_doc_length == 0:
            return 0.0
        
        # BM25参数
        k1 = 1.5
        b = 0.75
        
        score = 0.0
        for keyword in keywords:
            # 关键词在文档中的出现次数
            term_freq = text.lower().count(keyword.lower())
            if term_freq == 0:
                continue
            
            # 包含关键词的文档数（使用倒排索引）
            doc_count = len(self.inverted_index.get(keyword, set()))
            # 总文档数
            total_docs = self.total_docs
            # 逆文档频率
            if doc_count == 0:
                idf = 0
            else:
                idf = math.log((total_docs - doc_count + 0.5) / (doc_count + 0.5) + 1.0)
            
            # BM25得分
            numerator = term_freq * (k1 + 1)
            denominator = term_freq + k1 * (1 - b + b * doc_length / avg_doc_length)
            score += idf * (numerator / denominator)
        
        return score
    
    def _normalize_scores(self, results: List[Dict[str, Any]], score_key: str) -> List[Dict[str, Any]]:
        """归一化分数
        
        Args:
            results: 结果列表
            score_key: 分数键名
            
        Returns:
            List[Dict[str, Any]]: 归一化后的结果
        """
        if not results:
            return results
        
        # 提取分数
        scores = [result.get(score_key, 0.0) for result in results]
        max_score = max(scores) if scores else 1.0
        min_score = min(scores) if scores else 0.0
        
        # 归一化
        score_range = max_score - min_score
        if score_range > 0:
            for result in results:
                score = result.get(score_key, 0.0)
                normalized_score = (score - min_score) / score_range
                result['score'] = normalized_score
        else:
            # 如果所有分数相同，设置为0.5
            for result in results:
                result['score'] = 0.5
        
        return results
    
    def _merge_results(self, vector_results: List[Dict[str, Any]], keyword_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """融合结果
        
        Args:
            vector_results: 向量检索结果
            keyword_results: 关键词检索结果
            
        Returns:
            List[Dict[str, Any]]: 融合结果
        """
        # 归一化分数
        vector_results = self._normalize_scores(vector_results, 'similarity')
        keyword_results = self._normalize_scores(keyword_results, 'score')
        
        # 去重
        merged = {}
        
        # 添加向量检索结果
        for result in vector_results:
            doc_id = result.get('id')
            if doc_id:
                merged[doc_id] = result
        
        # 添加关键词检索结果
        for result in keyword_results:
            doc_id = result.get('id')
            if doc_id:
                if doc_id in merged:
                    # 融合得分
                    merged[doc_id]['score'] = (merged[doc_id]['score'] + result.get('score', 0.0)) / 2
                    merged[doc_id]['retrieval_type'] = 'hybrid'
                else:
                    merged[doc_id] = result
        
        return list(merged.values())
    
    def _filter_results(self, results: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """过滤结果
        
        Args:
            results: 检索结果
            filters: 过滤条件
            
        Returns:
            List[Dict[str, Any]]: 过滤结果
        """
        filtered = []
        
        for result in results:
            metadata = result.get('metadata', {})
            match = True
            
            # 按标签过滤
            if 'tags' in filters:
                doc_tags = metadata.get('tags', [])
                if not any(tag in doc_tags for tag in filters['tags']):
                    match = False
            
            # 按时间过滤
            if 'time_range' in filters:
                doc_time = metadata.get('time', '')
                time_range = filters['time_range']
                if doc_time:
                    # 简单的时间范围过滤
                    pass
            
            # 按权限过滤
            if 'permissions' in filters:
                doc_permissions = metadata.get('permissions', ['public'])
                if not any(perm in doc_permissions for perm in filters['permissions']):
                    match = False
            
            if match:
                filtered.append(result)
        
        return filtered
    
    def _sort_results(self, results: List[Dict[str, Any]], k: int) -> List[Dict[str, Any]]:
        """排序结果
        
        Args:
            results: 检索结果
            k: 返回结果数量
            
        Returns:
            List[Dict[str, Any]]: 排序结果
        """
        # 按得分排序
        results.sort(key=lambda x: x.get('score', 0.0), reverse=True)
        
        # 限制返回数量
        return results[:k]


# 全局检索引擎实例
retriever = Retriever()