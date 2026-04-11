"""向量存储层模块"""
from typing import Dict, List, Optional, Any, Tuple
import os
import json

# 尝试导入numpy和sklearn模块
has_numpy = False
has_sklearn = False
try:
    import numpy as np
    has_numpy = True
    print("已导入numpy模块")
except ImportError:
    print("警告: 无法导入numpy模块，将使用纯Python实现")
    has_numpy = False

try:
    from sklearn.neighbors import NearestNeighbors
    has_sklearn = True
    print("已导入sklearn模块")
except ImportError:
    print("警告: 无法导入sklearn模块，将使用纯Python实现")
    has_sklearn = False


class VectorStore:
    """向量存储类"""
    
    def __init__(self, embedding_dim: int = 1024):
        """初始化向量存储
        
        Args:
            embedding_dim: 向量维度
        """
        self.embedding_dim = embedding_dim
        self.vectors = []  # 向量列表
        self.texts = []  # 文本列表
        self.metadata = []  # 元数据列表
        self.ids = []  # ID列表
        self.index = None  # 近邻索引
        self.data_dir = "data/vector_store"
        os.makedirs(self.data_dir, exist_ok=True)
    
    def add(self, text: str, vector: List[float], metadata: Optional[Dict[str, Any]] = None, doc_id: Optional[str] = None):
        """添加向量
        
        Args:
            text: 文本
            vector: 向量
            metadata: 元数据
            doc_id: 文档ID
        """
        # 检查向量长度
        if len(vector) != self.embedding_dim:
            raise ValueError(f"向量长度不匹配: 期望 {self.embedding_dim}, 实际 {len(vector)}")
        
        # 生成ID
        if doc_id is None:
            doc_id = f"doc_{len(self.ids)}"
        
        # 添加到存储
        self.vectors.append(vector)
        self.texts.append(text)
        self.metadata.append(metadata or {})
        self.ids.append(doc_id)
        
        # 重新构建索引
        self._build_index()
    
    def add_batch(self, chunks: List[Dict[str, Any]]):
        """批量添加向量
        
        Args:
            chunks: 分块列表，每个分块包含text、vector等字段
        """
        for chunk in chunks:
            text = chunk.get("text", "")
            vector = chunk.get("vector", [])
            metadata = chunk.get("metadata", {})
            doc_id = chunk.get("id", None)
            
            # 检查向量长度
            if len(vector) != self.embedding_dim:
                raise ValueError(f"向量长度不匹配: 期望 {self.embedding_dim}, 实际 {len(vector)}")
            
            self.vectors.append(vector)
            self.texts.append(text)
            self.metadata.append(metadata)
            self.ids.append(doc_id or f"doc_{len(self.ids)}")
        
        # 重新构建索引
        self._build_index()
    
    def search(self, query_vector: List[float], k: int = 3) -> List[Dict[str, Any]]:
        """搜索相似向量
        
        Args:
            query_vector: 查询向量
            k: 返回结果数量
            
        Returns:
            List[Dict[str, Any]]: 搜索结果
        """
        # 检查向量长度
        if len(query_vector) != self.embedding_dim:
            raise ValueError(f"向量长度不匹配: 期望 {self.embedding_dim}, 实际 {len(query_vector)}")
        
        # 确保索引已构建
        if self.index is None:
            self._build_index()
        
        # 如果有sklearn和numpy，使用它们进行搜索
        if has_sklearn and has_numpy:
            try:
                # 转换为numpy数组
                query_np = np.array([query_vector])
                
                # 确保k不超过样本数量
                actual_k = min(k, len(self.vectors))
                if actual_k == 0:
                    return []
                
                # 搜索
                distances, indices = self.index.kneighbors(query_np, n_neighbors=actual_k)
                
                # 构建结果
                results = []
                for i, idx in enumerate(indices[0]):
                    if idx < len(self.ids):
                        results.append({
                            "id": self.ids[idx],
                            "text": self.texts[idx],
                            "metadata": self.metadata[idx],
                            "distance": float(distances[0][i]),
                            "similarity": 1.0 - float(distances[0][i])  # 转换为相似度
                        })
                
                return results
            except Exception as e:
                print(f"搜索失败: {e}")
                # 使用纯Python实现的余弦相似度
                return self._search_pure_python(query_vector, k)
        else:
            # 直接使用纯Python实现
            return self._search_pure_python(query_vector, k)
    
    def _search_pure_python(self, query_vector: List[float], k: int = 3) -> List[Dict[str, Any]]:
        """纯Python实现的搜索
        
        Args:
            query_vector: 查询向量
            k: 返回结果数量
            
        Returns:
            List[Dict[str, Any]]: 搜索结果
        """
        # 计算余弦相似度
        similarities = []
        for i, vector in enumerate(self.vectors):
            # 检查向量长度
            if len(vector) != len(query_vector):
                continue
            
            # 计算余弦相似度
            similarity = self._cosine_similarity(query_vector, vector)
            similarities.append((i, similarity))
        
        # 按相似度排序
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # 构建结果
        results = []
        for i, (idx, similarity) in enumerate(similarities[:k]):
            results.append({
                "id": self.ids[idx],
                "text": self.texts[idx],
                "metadata": self.metadata[idx],
                "distance": 1.0 - similarity,  # 距离 = 1 - 相似度
                "similarity": similarity
            })
        
        return results
    
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
    
    def _build_index(self):
        """构建索引"""
        if not self.vectors:
            self.index = None
            return
        
        # 如果有sklearn和numpy，使用它们构建索引
        if has_sklearn and has_numpy:
            try:
                # 转换为numpy数组
                vectors_np = np.array(self.vectors)
                
                # 构建KNN索引，确保n_neighbors不超过样本数量
                n_neighbors = min(10, len(self.vectors))
                self.index = NearestNeighbors(n_neighbors=n_neighbors, algorithm='auto', metric='cosine')
                self.index.fit(vectors_np)
            except Exception as e:
                print(f"构建索引失败: {e}")
                self.index = None
        else:
            # 纯Python实现不需要构建索引
            self.index = None
    
    def get_all(self) -> List[Dict[str, Any]]:
        """获取所有向量
        
        Returns:
            List[Dict[str, Any]]: 所有向量
        """
        results = []
        for i, (vector, text, metadata, doc_id) in enumerate(zip(self.vectors, self.texts, self.metadata, self.ids)):
            results.append({
                "id": doc_id,
                "text": text,
                "vector": vector,
                "metadata": metadata
            })
        return results
    
    def get_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取向量
        
        Args:
            doc_id: 文档ID
            
        Returns:
            Optional[Dict[str, Any]]: 向量信息
        """
        try:
            idx = self.ids.index(doc_id)
            return {
                "id": self.ids[idx],
                "text": self.texts[idx],
                "vector": self.vectors[idx],
                "metadata": self.metadata[idx]
            }
        except ValueError:
            return None
    
    def delete(self, doc_id: str) -> bool:
        """删除向量
        
        Args:
            doc_id: 文档ID
            
        Returns:
            bool: 是否删除成功
        """
        try:
            idx = self.ids.index(doc_id)
            del self.vectors[idx]
            del self.texts[idx]
            del self.metadata[idx]
            del self.ids[idx]
            # 重新构建索引
            self._build_index()
            return True
        except ValueError:
            return False
    
    def clear(self):
        """清空存储"""
        self.vectors = []
        self.texts = []
        self.metadata = []
        self.ids = []
        self.index = None
        
        # 删除存储文件
        file_path = os.path.join(self.data_dir, "vector_store.json")
        if os.path.exists(file_path):
            os.remove(file_path)
    
    def save(self, filename: str = "vector_store.json"):
        """保存到文件
        
        Args:
            filename: 文件名
        """
        data = {
            "embedding_dim": self.embedding_dim,
            "vectors": self.vectors,
            "texts": self.texts,
            "metadata": self.metadata,
            "ids": self.ids
        }
        file_path = os.path.join(self.data_dir, filename)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load(self, filename: str = "vector_store.json"):
        """从文件加载
        
        Args:
            filename: 文件名
        """
        file_path = os.path.join(self.data_dir, filename)
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    self.embedding_dim = data.get("embedding_dim", 1024)
                    self.vectors = data.get("vectors", [])
                    self.texts = data.get("texts", [])
                    self.metadata = data.get("metadata", [])
                    self.ids = data.get("ids", [])
                    # 重新构建索引
                    self._build_index()
                except Exception as e:
                    print(f"加载失败: {e}")
    
    def get_size(self) -> int:
        """获取存储大小
        
        Returns:
            int: 存储大小
        """
        return len(self.vectors)


# 全局向量存储实例
vector_store = VectorStore()
# 加载之前保存的数据
vector_store.load()