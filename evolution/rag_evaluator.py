"""RAG检索测评器"""
from typing import Dict, List, Any, Optional
import time
import json
import os
from datetime import datetime

class RagEvaluator:
    """RAG检索测评器"""
    
    def __init__(self):
        self.evaluation_history = []
        self.metrics = {
            'total_queries': 0,
            'total_retrieval_time': 0.0,
            'avg_retrieval_time': 0.0,
            'total_rerank_time': 0.0,
            'avg_rerank_time': 0.0,
            'total_quality_score': 0.0,
            'avg_quality_score': 0.0,
            'total_relevance_score': 0.0,
            'avg_relevance_score': 0.0,
            'total_diversity_score': 0.0,
            'avg_diversity_score': 0.0,
            'success_rate': 0.0,
            'failures': 0
        }
        
    def evaluate_retrieval(self, query: str, retrieved_docs: List[Dict[str, Any]], 
                          retrieval_time: float, rerank_time: float = 0.0) -> Dict[str, Any]:
        """评估单次检索
        
        Args:
            query: 查询文本
            retrieved_docs: 检索到的文档列表
            retrieval_time: 检索耗时（秒）
            rerank_time: 重排耗时（秒）
            
        Returns:
            Dict[str, Any]: 评估结果
        """
        # 计算各项指标
        quality_scores = self._evaluate_document_quality(retrieved_docs)
        relevance_score = self._evaluate_relevance(query, retrieved_docs)
        diversity_score = self._evaluate_diversity(retrieved_docs)
        
        # 综合评分
        overall_score = self._calculate_overall_score(quality_scores, relevance_score, diversity_score)
        
        # 构建评估结果
        evaluation_result = {
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'retrieved_docs_count': len(retrieved_docs),
            'retrieval_time_ms': retrieval_time * 1000,
            'rerank_time_ms': rerank_time * 1000,
            'total_time_ms': (retrieval_time + rerank_time) * 1000,
            'document_quality_scores': quality_scores,
            'avg_document_quality': sum(quality_scores) / len(quality_scores) if quality_scores else 0.0,
            'relevance_score': relevance_score,
            'diversity_score': diversity_score,
            'overall_score': overall_score,
            'retrieved_docs': [{'id': doc.get('id'), 'score': doc.get('score', 0), 'text_length': len(doc.get('text', ''))} 
                              for doc in retrieved_docs]
        }
        
        # 更新统计指标
        self._update_metrics(evaluation_result)
        
        # 保存到历史记录
        self.evaluation_history.append(evaluation_result)
        
        return evaluation_result
    
    def _evaluate_document_quality(self, docs: List[Dict[str, Any]]) -> List[float]:
        """评估文档质量
        
        质量维度：
        1. 文本长度（避免过短或过长）
        2. 文本完整性
        3. 语义密度
        """
        scores = []
        for doc in docs:
            text = doc.get('text', '')
            score = 0.0
            
            # 1. 文本长度评分（最佳长度：100-500字符）
            text_length = len(text)
            if text_length >= 100 and text_length <= 500:
                length_score = 1.0
            elif text_length >= 50 and text_length <= 800:
                length_score = 0.7
            elif text_length >= 20 and text_length <= 1000:
                length_score = 0.5
            else:
                length_score = 0.2
            
            # 2. 文本完整性（基于标点符号和句子结构）
            punctuation_count = text.count('。') + text.count('！') + text.count('？') + text.count('.')
            sentence_count = max(punctuation_count, 1)
            avg_sentence_length = text_length / sentence_count if sentence_count > 0 else 0
            if 15 <= avg_sentence_length <= 50:
                completeness_score = 1.0
            elif 10 <= avg_sentence_length <= 70:
                completeness_score = 0.7
            else:
                completeness_score = 0.4
            
            # 3. 语义密度（基于独特词比例）
            words = text.split()
            unique_words = set(words)
            if len(words) > 0:
                density_score = min(len(unique_words) / len(words), 1.0)
            else:
                density_score = 0.0
            
            # 综合评分
            doc_score = (length_score * 0.3 + completeness_score * 0.4 + density_score * 0.3)
            scores.append(doc_score)
        
        return scores
    
    def _evaluate_relevance(self, query: str, docs: List[Dict[str, Any]]) -> float:
        """评估文档相关性
        
        使用关键词匹配和语义相似度来评估
        """
        if not docs:
            return 0.0
        
        query_tokens = set(query.lower().split())
        total_relevance = 0.0
        
        for doc in docs:
            text = doc.get('text', '').lower()
            text_tokens = set(text.split())
            
            # 计算关键词匹配率
            if query_tokens:
                matched_tokens = query_tokens.intersection(text_tokens)
                match_rate = len(matched_tokens) / len(query_tokens)
            else:
                match_rate = 0.0
            
            # 获取检索分数
            retrieval_score = doc.get('score', 0.0)
            
            # 综合相关性
            relevance = (match_rate * 0.6 + retrieval_score * 0.4)
            total_relevance += relevance
        
        return total_relevance / len(docs)
    
    def _evaluate_diversity(self, docs: List[Dict[str, Any]]) -> float:
        """评估文档多样性
        
        确保返回的文档不是重复或高度相似的内容
        """
        if len(docs) < 2:
            return 1.0
        
        total_diversity = 0.0
        comparisons = 0
        
        # 比较每对文档的相似度
        for i in range(len(docs)):
            for j in range(i + 1, len(docs)):
                text1 = docs[i].get('text', '')
                text2 = docs[j].get('text', '')
                
                # 计算Jaccard相似度
                tokens1 = set(text1.split())
                tokens2 = set(text2.split())
                
                if tokens1 or tokens2:
                    intersection = tokens1.intersection(tokens2)
                    union = tokens1.union(tokens2)
                    similarity = len(intersection) / len(union) if union else 0
                    diversity = 1 - similarity
                    total_diversity += diversity
                    comparisons += 1
        
        return total_diversity / comparisons if comparisons > 0 else 1.0
    
    def _calculate_overall_score(self, quality_scores: List[float], 
                                relevance_score: float, diversity_score: float) -> float:
        """计算综合评分"""
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        
        # 权重分配
        # - 文档质量: 30%
        # - 相关性: 50%
        # - 多样性: 20%
        overall = (avg_quality * 0.3 + relevance_score * 0.5 + diversity_score * 0.2)
        
        return round(overall, 4)
    
    def _update_metrics(self, result: Dict[str, Any]):
        """更新统计指标"""
        self.metrics['total_queries'] += 1
        self.metrics['total_retrieval_time'] += result['retrieval_time_ms']
        self.metrics['total_rerank_time'] += result['rerank_time_ms']
        self.metrics['total_quality_score'] += result['avg_document_quality']
        self.metrics['total_relevance_score'] += result['relevance_score']
        self.metrics['total_diversity_score'] += result['diversity_score']
        
        # 计算平均值
        count = self.metrics['total_queries']
        self.metrics['avg_retrieval_time'] = self.metrics['total_retrieval_time'] / count
        self.metrics['avg_rerank_time'] = self.metrics['total_rerank_time'] / count
        self.metrics['avg_quality_score'] = self.metrics['total_quality_score'] / count
        self.metrics['avg_relevance_score'] = self.metrics['total_relevance_score'] / count
        self.metrics['avg_diversity_score'] = self.metrics['total_diversity_score'] / count
        
        # 更新成功率
        if result['retrieved_docs_count'] > 0:
            self.metrics['success_rate'] = (self.metrics['total_queries'] - self.metrics['failures']) / self.metrics['total_queries']
        else:
            self.metrics['failures'] += 1
            self.metrics['success_rate'] = (self.metrics['total_queries'] - self.metrics['failures']) / max(self.metrics['total_queries'], 1)
    
    def get_summary(self) -> Dict[str, Any]:
        """获取测评摘要"""
        return {
            'metrics': self.metrics,
            'evaluation_count': len(self.evaluation_history),
            'last_evaluation': self.evaluation_history[-1] if self.evaluation_history else None
        }
    
    def save_report(self, filename: str = None):
        """保存测评报告"""
        if filename is None:
            filename = f"rag_evaluation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'summary': self.get_summary(),
            'full_history': self.evaluation_history
        }
        
        # 确保目录存在
        os.makedirs('evolution/reports', exist_ok=True)
        filepath = os.path.join('evolution/reports', filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        return filepath
    
    def print_report(self):
        """打印测评报告"""
        summary = self.get_summary()
        metrics = summary['metrics']
        
        print("=" * 60)
        print("RAG检索测评报告")
        print("=" * 60)
        print(f"测评次数: {metrics['total_queries']}")
        print(f"成功率: {metrics['success_rate'] * 100:.2f}%")
        print("-" * 60)
        print("【耗时统计】")
        print(f"  平均检索耗时: {metrics['avg_retrieval_time']:.2f} ms")
        print(f"  平均重排耗时: {metrics['avg_rerank_time']:.2f} ms")
        print("-" * 60)
        print("【质量统计】")
        print(f"  平均文档质量: {metrics['avg_quality_score']:.4f}")
        print(f"  平均相关性: {metrics['avg_relevance_score']:.4f}")
        print(f"  平均多样性: {metrics['avg_diversity_score']:.4f}")
        print("=" * 60)
    
    def reset(self):
        """重置测评数据"""
        self.evaluation_history = []
        self.metrics = {
            'total_queries': 0,
            'total_retrieval_time': 0.0,
            'avg_retrieval_time': 0.0,
            'total_rerank_time': 0.0,
            'avg_rerank_time': 0.0,
            'total_quality_score': 0.0,
            'avg_quality_score': 0.0,
            'total_relevance_score': 0.0,
            'avg_relevance_score': 0.0,
            'total_diversity_score': 0.0,
            'avg_diversity_score': 0.0,
            'success_rate': 0.0,
            'failures': 0
        }


# 全局测评器实例
rag_evaluator = RagEvaluator()
