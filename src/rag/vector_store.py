"""向量存储层模块 - 支持ChromaDB和Milvus"""
from typing import Dict, List, Optional, Any, Tuple
import os
import json

from src.config.config import settings


class VectorStore:
    def add(self, text: str, vector: List[float], metadata: Optional[Dict[str, Any]] = None, doc_id: Optional[str] = None):
        raise NotImplementedError

    def add_batch(self, chunks: List[Dict[str, Any]]):
        raise NotImplementedError

    def search(self, query_vector: List[float], k: int = 3) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def get_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    def delete(self, doc_id: str) -> bool:
        raise NotImplementedError

    def clear(self):
        raise NotImplementedError

    def get_size(self) -> int:
        raise NotImplementedError


class ChromaVectorStore(VectorStore):
    has_numpy = False
    has_sklearn = False
    
    def __init__(self, embedding_dim: int = 1024):
        self.embedding_dim = embedding_dim
        self.vectors = []
        self.texts = []
        self.metadata = []
        self.ids = []
        self.index = None
        self.data_dir = "data/vector_store"
        os.makedirs(self.data_dir, exist_ok=True)
        
        self._try_import_dependencies()

    def _try_import_dependencies(self):
        global np, NearestNeighbors
        try:
            import numpy as np
            ChromaVectorStore.has_numpy = True
        except ImportError:
            ChromaVectorStore.has_numpy = False
        
        try:
            from sklearn.neighbors import NearestNeighbors
            ChromaVectorStore.has_sklearn = True
        except ImportError:
            ChromaVectorStore.has_sklearn = False

    def add(self, text: str, vector: List[float], metadata: Optional[Dict[str, Any]] = None, doc_id: Optional[str] = None):
        if len(vector) != self.embedding_dim:
            raise ValueError(f"向量长度不匹配: 期望 {self.embedding_dim}, 实际 {len(vector)}")
        
        if doc_id is None:
            doc_id = f"doc_{len(self.ids)}"
        
        self.vectors.append(vector)
        self.texts.append(text)
        self.metadata.append(metadata or {})
        self.ids.append(doc_id)
        self._build_index()

    def add_batch(self, chunks: List[Dict[str, Any]]):
        for chunk in chunks:
            text = chunk.get("text", "")
            vector = chunk.get("vector", [])
            metadata = chunk.get("metadata", {})
            doc_id = chunk.get("id", None)
            
            if len(vector) != self.embedding_dim:
                raise ValueError(f"向量长度不匹配: 期望 {self.embedding_dim}, 实际 {len(vector)}")
            
            self.vectors.append(vector)
            self.texts.append(text)
            self.metadata.append(metadata)
            self.ids.append(doc_id or f"doc_{len(self.ids)}")
        
        self._build_index()

    def search(self, query_vector: List[float], k: int = 3) -> List[Dict[str, Any]]:
        if len(query_vector) != self.embedding_dim:
            raise ValueError(f"向量长度不匹配: 期望 {self.embedding_dim}, 实际 {len(query_vector)}")
        
        if self.index is None:
            self._build_index()
        
        if ChromaVectorStore.has_sklearn and ChromaVectorStore.has_numpy:
            try:
                query_np = np.array([query_vector])
                actual_k = min(k, len(self.vectors))
                if actual_k == 0:
                    return []
                
                distances, indices = self.index.kneighbors(query_np, n_neighbors=actual_k)
                results = []
                for i, idx in enumerate(indices[0]):
                    if idx < len(self.ids):
                        results.append({
                            "id": self.ids[idx],
                            "text": self.texts[idx],
                            "metadata": self.metadata[idx],
                            "distance": float(distances[0][i]),
                            "similarity": 1.0 - float(distances[0][i])
                        })
                return results
            except Exception as e:
                return self._search_pure_python(query_vector, k)
        else:
            return self._search_pure_python(query_vector, k)

    def _search_pure_python(self, query_vector: List[float], k: int = 3) -> List[Dict[str, Any]]:
        similarities = []
        for i, vector in enumerate(self.vectors):
            if len(vector) != len(query_vector):
                continue
            similarity = self._cosine_similarity(query_vector, vector)
            similarities.append((i, similarity))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for i, (idx, similarity) in enumerate(similarities[:k]):
            results.append({
                "id": self.ids[idx],
                "text": self.texts[idx],
                "metadata": self.metadata[idx],
                "distance": 1.0 - similarity,
                "similarity": similarity
            })
        return results

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)

    def _build_index(self):
        if not self.vectors:
            self.index = None
            return
        
        if ChromaVectorStore.has_sklearn and ChromaVectorStore.has_numpy:
            try:
                vectors_np = np.array(self.vectors)
                n_neighbors = min(10, len(self.vectors))
                self.index = NearestNeighbors(n_neighbors=n_neighbors, algorithm='auto', metric='cosine')
                self.index.fit(vectors_np)
            except Exception as e:
                self.index = None
        else:
            self.index = None

    def get_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
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
        try:
            idx = self.ids.index(doc_id)
            del self.vectors[idx]
            del self.texts[idx]
            del self.metadata[idx]
            del self.ids[idx]
            self._build_index()
            return True
        except ValueError:
            return False

    def clear(self):
        self.vectors = []
        self.texts = []
        self.metadata = []
        self.ids = []
        self.index = None
        
        file_path = os.path.join(self.data_dir, "vector_store.json")
        if os.path.exists(file_path):
            os.remove(file_path)

    def save(self, filename: str = "vector_store.json"):
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
                    self._build_index()
                except Exception as e:
                    print(f"加载失败: {e}")

    def get_size(self) -> int:
        return len(self.vectors)

    def get_all(self) -> List[Dict[str, Any]]:
        results = []
        for i, (vector, text, metadata, doc_id) in enumerate(zip(self.vectors, self.texts, self.metadata, self.ids)):
            results.append({
                "id": doc_id,
                "text": text,
                "vector": vector,
                "metadata": metadata
            })
        return results


class MilvusVectorStore(VectorStore):
    def __init__(self, embedding_dim: int = 1024):
        self.embedding_dim = embedding_dim
        self.client = None
        self.collection_name = "eleina_rag"
        self._connect()

    def _connect(self):
        try:
            from pymilvus import connections, utility, Collection, DataType, FieldSchema, CollectionSchema
            self.FieldSchema = FieldSchema
            self.CollectionSchema = CollectionSchema
            self.DataType = DataType
            self.Collection = Collection
            self.connections = connections
            self.utility = utility
            
            self.connections.connect(
                alias="default",
                host=settings.milvus_host,
                port=settings.milvus_port
            )
            print(f"✓ Milvus连接成功: {settings.milvus_host}:{settings.milvus_port}")
            self._create_collection()
        except Exception as e:
            print(f"✗ Milvus连接失败: {e}")
            raise

    def _create_collection(self):
        if not self.utility.has_collection(self.collection_name):
            fields = [
                self.FieldSchema(name="id", dtype=self.DataType.VARCHAR, max_length=255, is_primary=True),
                self.FieldSchema(name="text", dtype=self.DataType.VARCHAR, max_length=65535),
                self.FieldSchema(name="embedding", dtype=self.DataType.FLOAT_VECTOR, dim=self.embedding_dim),
                self.FieldSchema(name="metadata", dtype=self.DataType.VARCHAR, max_length=4096)
            ]
            schema = self.CollectionSchema(fields, "RAG知识库向量集合")
            self.collection = self.Collection(self.collection_name, schema)
            
            index_params = {
                "metric_type": "COSINE",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 128}
            }
            self.collection.create_index("embedding", index_params)
            print(f"✓ 创建Milvus集合: {self.collection_name}")
        else:
            self.collection = self.Collection(self.collection_name)
            print(f"✓ 加载Milvus集合: {self.collection_name}")

    def add(self, text: str, vector: List[float], metadata: Optional[Dict[str, Any]] = None, doc_id: Optional[str] = None):
        if doc_id is None:
            doc_id = f"doc_{self.get_size()}"
        
        import json
        metadata_str = json.dumps(metadata or {}, ensure_ascii=False)
        
        entities = [
            [doc_id],
            [text],
            [vector],
            [metadata_str]
        ]
        
        self.collection.insert(entities)
        self.collection.flush()

    def add_batch(self, chunks: List[Dict[str, Any]]):
        import json
        ids = []
        texts = []
        vectors = []
        metadatas = []
        
        for chunk in chunks:
            text = chunk.get("text", "")
            vector = chunk.get("vector", [])
            metadata = chunk.get("metadata", {})
            doc_id = chunk.get("id", None)
            
            if len(vector) != self.embedding_dim:
                raise ValueError(f"向量长度不匹配: 期望 {self.embedding_dim}, 实际 {len(vector)}")
            
            if doc_id is None:
                doc_id = f"doc_{self.get_size() + len(ids)}"
            
            ids.append(doc_id)
            texts.append(text)
            vectors.append(vector)
            metadatas.append(json.dumps(metadata, ensure_ascii=False))
        
        entities = [ids, texts, vectors, metadatas]
        self.collection.insert(entities)
        self.collection.flush()

    def search(self, query_vector: List[float], k: int = 3) -> List[Dict[str, Any]]:
        import json
        
        self.collection.load()
        search_params = {
            "metric_type": "COSINE",
            "params": {"nprobe": 10}
        }
        
        results = self.collection.search(
            data=[query_vector],
            anns_field="embedding",
            param=search_params,
            limit=k,
            output_fields=["text", "metadata"]
        )
        
        output = []
        for hits in results:
            for hit in hits:
                metadata = {}
                try:
                    metadata = json.loads(hit.entity.get("metadata"))
                except:
                    pass
                
                output.append({
                    "id": hit.id,
                    "text": hit.entity.get("text"),
                    "metadata": metadata,
                    "distance": hit.distance,
                    "similarity": 1.0 - hit.distance
                })
        
        return output

    def get_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        import json
        
        self.collection.load()
        results = self.collection.query(
            expr=f'id == "{doc_id}"',
            output_fields=["text", "embedding", "metadata"]
        )
        
        if results:
            result = results[0]
            metadata = {}
            try:
                metadata = json.loads(result.get("metadata", "{}"))
            except:
                pass
            
            return {
                "id": result["id"],
                "text": result["text"],
                "vector": result["embedding"],
                "metadata": metadata
            }
        return None

    def delete(self, doc_id: str) -> bool:
        try:
            self.collection.delete(f'id == "{doc_id}"')
            self.collection.flush()
            return True
        except Exception as e:
            print(f"删除失败: {e}")
            return False

    def clear(self):
        if self.utility.has_collection(self.collection_name):
            self.utility.drop_collection(self.collection_name)
        self._create_collection()

    def get_size(self) -> int:
        self.collection.load()
        return self.collection.num_entities

    def get_all(self) -> List[Dict[str, Any]]:
        import json
        
        self.collection.load()
        size = self.get_size()
        if size == 0:
            return []
        
        results = self.collection.query(
            expr="",
            output_fields=["id", "text", "embedding", "metadata"],
            limit=size
        )
        
        output = []
        for result in results:
            metadata = {}
            try:
                metadata = json.loads(result.get("metadata", "{}"))
            except:
                pass
            
            output.append({
                "id": result["id"],
                "text": result["text"],
                "vector": result["embedding"],
                "metadata": metadata
            })
        
        return output

    def save(self, filename: str = "vector_store.json"):
        self.collection.flush()

    def load(self, filename: str = "vector_store.json"):
        pass


def create_vector_store() -> VectorStore:
    """根据配置创建向量存储实例"""
    vector_db_type = settings.vector_db_type.lower()
    
    if vector_db_type == "milvus":
        print("使用Milvus向量存储")
        return MilvusVectorStore()
    else:
        print("使用ChromaDB向量存储")
        return ChromaVectorStore()


vector_store = create_vector_store()