"""医疗领域专用向量存储 - 支持科室级别的独立Collection"""
from typing import Dict, List, Optional, Any
import json

from src.config.config import settings


class MedicalMilvusVectorStore:
    """医疗领域专用Milvus向量存储 - 支持多Collection"""
    
    def __init__(self, db_name: str = "medical"):
        """初始化医疗向量存储
        
        Args:
            db_name: 数据库名称，默认连接到"医疗"数据库
        """
        self.client = None
        self.collections: Dict[str, Any] = {}  # collection_name -> Collection对象
        self.alias = "medical"
        self.db_name = db_name
        self._connect()
        self._init_collections()
    
    def _connect(self):
        """连接Milvus并切换到指定数据库"""
        try:
            from pymilvus import connections, utility, Collection, DataType, FieldSchema, CollectionSchema
            self.FieldSchema = FieldSchema
            self.CollectionSchema = CollectionSchema
            self.DataType = DataType
            self.Collection = Collection
            self.connections = connections
            self.utility = utility
            
            if self.connections.has_connection(self.alias):
                self.connections.remove_connection(self.alias)
            
            # 连接时指定数据库（兼容不同版本）
            try:
                # Milvus 2.2+ 支持在连接时指定db_name
                self.connections.connect(
                    alias=self.alias,
                    host=settings.milvus_host,
                    port=settings.milvus_port,
                    db_name=self.db_name
                )
            except TypeError:
                # 旧版本不支持db_name参数，先连接再使用USE命令
                self.connections.connect(
                    alias=self.alias,
                    host=settings.milvus_host,
                    port=settings.milvus_port
                )
                
            print(f"✓ 医疗RAG Milvus连接成功: {settings.milvus_host}:{settings.milvus_port}")
        except Exception as e:
            print(f"✗ 医疗RAG Milvus连接失败: {e}")
            raise
    
    def _init_collections(self):
        """初始化所有科室Collection"""
        departments = ["儿科", "妇产科", "男科", "内科", "外科", "肿瘤科"]
        
        for dept in departments:
            collection_name = self._get_collection_name(dept)
            self._create_collection(collection_name)
    
    def _get_collection_name(self, department: str) -> str:
        """获取科室对应的Collection名称"""
        department_mapping = {
            "儿科": "pediatric",
            "妇产科": "obstetrics",
            "男科": "male",
            "内科": "internal",
            "外科": "surgery",
            "肿瘤科": "oncology"
        }
        
        name = department_mapping.get(department.strip(), department.strip().lower())
        import re
        name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        return f"medical_{name}"
    
    def _create_collection(self, collection_name: str, embedding_dim: int = 768):
        """创建或加载Collection"""
        if collection_name in self.collections:
            return
        
        max_varchar_length = 65535  # Milvus VARCHAR 最大限制
        
        if not self.utility.has_collection(collection_name, using=self.alias):
            fields = [
                self.FieldSchema(name="id", dtype=self.DataType.VARCHAR, max_length=255, is_primary=True),
                self.FieldSchema(name="content", dtype=self.DataType.VARCHAR, max_length=max_varchar_length),
                self.FieldSchema(name="embedding", dtype=self.DataType.FLOAT_VECTOR, dim=embedding_dim),
                self.FieldSchema(name="metadata", dtype=self.DataType.VARCHAR, max_length=max_varchar_length),
                self.FieldSchema(name="source_type", dtype=self.DataType.VARCHAR, max_length=100),
                self.FieldSchema(name="department", dtype=self.DataType.VARCHAR, max_length=50)
            ]
            schema = self.CollectionSchema(fields, f"医疗RAG-{collection_name}知识库")
            collection = self.Collection(collection_name, schema, using=self.alias)
            
            index_params = {
                "metric_type": "COSINE",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 128}
            }
            collection.create_index("embedding", index_params)
            print(f"✓ 创建医疗RAG Collection: {collection_name}")
        else:
            collection = self.Collection(collection_name, using=self.alias)
            print(f"✓ 加载医疗RAG Collection: {collection_name}")
        
        self.collections[collection_name] = collection
    
    def _truncate_metadata(self, metadata_str: str, max_length: int = None) -> str:
        """截断过长的metadata字符串"""
        if max_length is None:
            max_length = 65530  # Milvus VARCHAR最大65535，留5个字符安全空间
        if len(metadata_str) > max_length:
            try:
                metadata = json.loads(metadata_str)
                truncated = {}
                for key, value in metadata.items():
                    if isinstance(value, str):
                        truncated[key] = value[:200] if len(value) > 200 else value
                    elif isinstance(value, list):
                        truncated[key] = [item[:100] if isinstance(item, str) and len(item) > 100 else item for item in value[:20]]
                    else:
                        truncated[key] = value
                return json.dumps(truncated, ensure_ascii=False)[:max_length]
            except:
                return metadata_str[:max_length]
        return metadata_str
    
    def get_collection(self, department: str) -> Any:
        """获取指定科室的Collection"""
        collection_name = self._get_collection_name(department)
        if collection_name not in self.collections:
            self._create_collection(collection_name)
        return self.collections[collection_name]
    
    def add(self, department: str, content: str, vector: List[float], 
            metadata: Optional[Dict[str, Any]] = None, doc_id: Optional[str] = None, 
            source_type: str = "document"):
        """添加单个文档到指定科室Collection"""
        collection = self.get_collection(department)
        
        if doc_id is None:
            doc_id = f"med_{department}_{collection.num_entities}"
        
        metadata_str = json.dumps(metadata or {}, ensure_ascii=False)
        metadata_str = self._truncate_metadata(metadata_str)
        
        entities = [
            [doc_id],
            [content],
            [vector],
            [metadata_str],
            [source_type],
            [department]
        ]
        
        collection.insert(entities)
        collection.flush()
    
    def _truncate_to_byte_length(self, text: str, max_bytes: int = 65530) -> str:
        """将文本截断到指定的字节长度（UTF-8编码），确保不破坏字符边界"""
        if len(text.encode('utf-8')) <= max_bytes:
            return text
        
        max_chars = max_bytes
        while len(text[:max_chars].encode('utf-8')) > max_bytes:
            max_chars -= 1
        
        return text[:max_chars]
    
    def add_batch(self, department: str, chunks: List[Dict[str, Any]], batch_size: int = 50):
        """批量添加文档到指定科室Collection
        
        Args:
            department: 科室名称
            chunks: 文档块列表
            batch_size: 每批插入的数量，默认50（避免gRPC消息超限）
        """
        collection = self.get_collection(department)
        total_chunks = len(chunks)
        
        for start in range(0, total_chunks, batch_size):
            end = min(start + batch_size, total_chunks)
            batch_chunks = chunks[start:end]
            
            ids = []
            contents = []
            vectors = []
            metadatas = []
            source_types = []
            departments = []
            
            for i, chunk in enumerate(batch_chunks):
                doc_id = chunk.get("id") or f"med_{department}_{collection.num_entities + start + i}"
                ids.append(doc_id)
                
                content = chunk["content"]
                content = self._truncate_to_byte_length(content)
                contents.append(content)
                
                vectors.append(chunk["vector"])
                metadata_str = json.dumps(chunk.get("metadata", {}), ensure_ascii=False)
                metadata_str = self._truncate_metadata(metadata_str)
                metadatas.append(metadata_str)
                source_types.append(chunk.get("source_type", "document"))
                departments.append(department)
            
            entities = [
                ids,
                contents,
                vectors,
                metadatas,
                source_types,
                departments
            ]
            
            collection.insert(entities)
            print(f"  已插入 {end}/{total_chunks} 条")
        
        collection.flush()
    
    def search(self, department: str, query_vector: List[float], top_k: int = 5, 
               filter_expr: Optional[str] = None, keep_loaded: bool = True) -> List[Dict[str, Any]]:
        """在指定科室Collection中搜索
        
        Args:
            department: 科室名称
            query_vector: 查询向量
            top_k: 返回结果数量
            filter_expr: 过滤表达式
            keep_loaded: 是否保持加载状态（True则检索后不释放，False则立即释放）
        """
        collection = self.get_collection(department)
        
        # 加载Collection（幂等操作，已加载时不会重复加载）
        collection.load()
        
        search_params = {
            "metric_type": "COSINE",
            "params": {"nprobe": 10}
        }
        
        results = collection.search(
            data=[query_vector],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            expr=filter_expr
        )
        
        # 如果不需要保持加载状态，则释放
        if not keep_loaded:
            collection.release()
        
        search_results = []
        for hits in results:
            for hit in hits:
                search_results.append({
                    "id": hit.id,
                    "content": hit.entity.get("content"),
                    "score": hit.score,
                    "metadata": json.loads(hit.entity.get("metadata")) if hit.entity.get("metadata") else {},
                    "source_type": hit.entity.get("source_type"),
                    "department": hit.entity.get("department")
                })
        
        return search_results
    
    def release_collection(self, department: str = None):
        """释放指定科室的Collection
        
        Args:
            department: 科室名称，为None则释放当前加载的所有Collection
        """
        if department:
            collection_name = self._get_collection_name(department)
            if collection_name in self.collections:
                self.collections[collection_name].release()
                print(f"✓ 已释放 Collection: {collection_name}")
        else:
            # 释放所有加载的 Collection
            for name, collection in self.collections.items():
                if collection.isLoaded:
                    collection.release()
                    print(f"✓ 已释放 Collection: {name}")
    
    def get_size(self, department: str = None) -> int:
        """获取指定科室Collection的文档数"""
        if department is None:
            total = 0
            for dept in self._get_all_departments():
                total += self.get_size(dept)
            return total
        
        collection = self.get_collection(department)
        return collection.num_entities
    
    def get_collections(self) -> List[str]:
        """获取所有科室Collection列表"""
        return list(self.collections.keys())
    
    def _get_all_departments(self) -> List[str]:
        """获取所有科室名称列表"""
        return ["儿科", "妇产科", "男科", "内科", "外科", "肿瘤科"]
    
    def search_multi(self, departments: List[str], query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """在多个科室Collection中搜索并合并结果"""
        all_results = []
        
        for dept in departments:
            results = self.search(dept, query_vector, top_k)
            all_results.extend(results)
        
        # 按相似度排序并去重
        seen = set()
        unique_results = []
        for result in sorted(all_results, key=lambda x: x.get("score", 0), reverse=True):
            content = result.get("content", "")
            if content not in seen:
                seen.add(content)
                unique_results.append(result)
        
        return unique_results[:top_k]
    
    def clear(self, department: str):
        """清空指定科室Collection"""
        collection_name = self._get_collection_name(department)
        if self.utility.has_collection(collection_name, using=self.alias):
            self.utility.drop_collection(collection_name, using=self.alias)
            if collection_name in self.collections:
                del self.collections[collection_name]
            print(f"✓ 清空医疗RAG Collection: {collection_name}")
    
    def clear_all(self):
        """清空所有科室Collection"""
        departments = ["儿科", "妇产科", "男科", "内科", "外科", "肿瘤科"]
        for dept in departments:
            self.clear(dept)
    
    def close(self):
        """关闭连接"""
        if self.connections.has_connection(self.alias):
            self.connections.disconnect(self.alias)


# 全局医疗向量存储实例 - 使用医疗数据库的连接别名
medical_vector_store = MedicalMilvusVectorStore()


def create_medical_vector_store() -> MedicalMilvusVectorStore:
    """创建医疗向量存储实例
    
    Returns:
        MedicalMilvusVectorStore: 医疗向量存储实例
    """
    return MedicalMilvusVectorStore()