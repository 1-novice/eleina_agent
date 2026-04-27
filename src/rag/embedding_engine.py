"""向量化引擎模块 - 使用text2vec模型"""
from typing import List, Dict, Optional, Any
import os
import json

from src.rag.text2vec_embedding import text2vec_embedding


class EmbeddingEngine:
    """向量化引擎类 - 基于text2vec模型"""
    
    def __init__(self):
        """初始化向量化引擎"""
        self.text2vec = text2vec_embedding
        self.embedding_dim = self.text2vec.get_embedding_dim()
        print(f"✓ 向量化引擎初始化完成，向量维度: {self.embedding_dim}")
    
    def embed(self, text: str) -> List[float]:
        """向量化单个文本
        
        Args:
            text: 文本
            
        Returns:
            List[float]: 向量
        """
        return self.text2vec.embed(text)
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量向量化
        
        Args:
            texts: 文本列表
            
        Returns:
            List[List[float]]: 向量列表
        """
        return self.text2vec.embed_batch(texts)
    
    def get_embedding_dim(self) -> int:
        """获取向量维度
        
        Returns:
            int: 向量维度
        """
        return self.embedding_dim
    
    def clear_cache(self):
        """清空缓存"""
        self.text2vec.clear_cache()
    
    def get_cache_size(self) -> int:
        """获取缓存大小
        
        Returns:
            int: 缓存大小
        """
        return self.text2vec.get_cache_size()


# 全局向量化引擎实例
embedding_engine = EmbeddingEngine()