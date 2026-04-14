"""二次元角色识别器 - 基于视觉Embedding的纯视觉特征匹配"""
import base64
import numpy as np
from typing import Optional, Tuple
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility

class CharacterRecognizer:
    """角色识别器 - 使用阿里云DashScope官方SDK调用多模态Embedding"""

    def __init__(self, api_key: Optional[str] = None, milvus_host: str = "localhost", milvus_port: int = 19530):
        self.api_key = api_key
        self.milvus_host = milvus_host
        self.milvus_port = milvus_port
        self.collection_name = "character_embeddings"
        self.dim = 2560
        self.dashscope = None

    def _init_dashscope(self):
        if self.dashscope is None:
            try:
                from dashscope import MultiModalEmbedding
                MultiModalEmbedding.api_key = self.api_key
                self.dashscope = MultiModalEmbedding
                return True
            except ImportError:
                print("错误：未安装 dashscope SDK，请运行 pip install dashscope")
                return False
        return True

    def connect_milvus(self):
        try:
            connections.connect(alias="default", host=self.milvus_host, port=self.milvus_port)
            return True
        except Exception as e:
            print(f"Milvus连接失败: {e}")
            return False

    def create_collection(self):
        if not self.connect_milvus():
            return False

        if utility.has_collection(self.collection_name):
            print(f"集合 {self.collection_name} 已存在")
            return True

        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="character_name", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.dim),
            FieldSchema(name="image_path", dtype=DataType.VARCHAR, max_length=500)
        ]

        schema = CollectionSchema(fields, "二次元角色视觉Embedding集合")
        collection = Collection(self.collection_name, schema)

        index_params = {
            "metric_type": "COSINE",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 100}
        }
        collection.create_index("embedding", index_params)
        print(f"成功创建集合 {self.collection_name}")
        return True

    def get_image_embedding(self, image_path: str) -> Optional[np.ndarray]:
        if not self.api_key:
            print("错误：未设置 API Key")
            return None

        if not self._init_dashscope():
            return None

        try:
            from dashscope import MultiModalEmbedding

            print(f"[CharacterRecognizer] 读取图片: {image_path}")
            with open(image_path, "rb") as f:
                image_bytes = f.read()

            print(f"[CharacterRecognizer] 图片大小: {len(image_bytes)} bytes")
            
            import io
            from PIL import Image
            img = Image.open(io.BytesIO(image_bytes))
            format = img.format.lower() if img.format else "png"
            img_base64 = f"data:image/{format};base64,{base64.b64encode(image_bytes).decode('utf-8')}"
            print(f"[CharacterRecognizer] 图片格式: {format}")

            response = MultiModalEmbedding.call(
                model="qwen3-vl-embedding",
                input=[{"image": img_base64}]
            )

            print(f"[CharacterRecognizer] 响应状态: {response.status_code}")

            if response.status_code == 200:
                if hasattr(response, 'output'):
                    result = response.output
                else:
                    result = response
                
                if isinstance(result, dict):
                    embeddings = result.get('embeddings', [])
                elif hasattr(result, 'embeddings'):
                    embeddings = result.embeddings
                else:
                    embeddings = []
                
                if embeddings and len(embeddings) > 0:
                    embedding_data = embeddings[0]
                    if isinstance(embedding_data, dict):
                        embedding = embedding_data.get('embedding', embedding_data)
                    elif hasattr(embedding_data, 'embedding'):
                        embedding = embedding_data.embedding
                    else:
                        embedding = embedding_data
                    
                    print(f"[CharacterRecognizer] Embedding维度: {len(embedding)}")
                    return np.array(embedding, dtype=np.float32)
                else:
                    print(f"[CharacterRecognizer] 未获取到Embedding")
                    return None
            else:
                error_msg = response.message if hasattr(response, 'message') else str(response)
                print(f"[CharacterRecognizer] API错误: {error_msg}")
                return None

        except Exception as e:
            print(f"获取Embedding失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def add_character(self, character_name: str, image_path: str) -> bool:
        if not self.connect_milvus():
            return False

        try:
            collection = Collection(self.collection_name)
            collection.load()

            embedding = self.get_image_embedding(image_path)
            if embedding is None:
                print(f"无法获取 {character_name} 的Embedding")
                return False

            data = [
                [character_name],
                [embedding.tolist()],
                [image_path]
            ]

            collection.insert(data)
            collection.flush()
            print(f"✅ 成功添加角色: {character_name}")
            return True

        except Exception as e:
            print(f"添加角色失败: {e}")
            return False

    def recognize_character(self, image_path: str) -> Tuple[str, float]:
        if not self.connect_milvus():
            return "❌ 非伊雷娜 | 相似度：0.0000", 0.0

        try:
            collection = Collection(self.collection_name)
            collection.load()
            embedding = self.get_image_embedding(image_path)

            if embedding is None:
                return "❌ 非伊雷娜 | 相似度：0.0000", 0.0

            search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
            results = collection.search(
                data=[embedding],
                anns_field="embedding",
                param=search_params,
                limit=1,
                expr='character_name == "伊雷娜"'
            )

            if results and results[0]:
                similarity = round(float(results[0][0].distance), 4)
                if similarity >= 0.7:
                    return f"✅ 识别为伊雷娜 | 相似度：{similarity:.4f}", similarity
                else:
                    return f"❌ 非伊雷娜 | 相似度：{similarity:.4f}", similarity

            return "❌ 非伊雷娜 | 相似度：0.0000", 0.0

        except Exception as e:
            print(f"识别失败: {e}")
            return "❌ 非伊雷娜 | 相似度：0.0000", 0.0

    def batch_add_characters(self, character_list: list) -> int:
        success = 0
        for item in character_list:
            name = item.get("name")
            paths = item.get("path")
            if not name or not paths:
                continue
            if isinstance(paths, str):
                paths = [paths]
            for path in paths:
                if self.add_character(name, path):
                    success += 1
        return success

    def get_character_count(self) -> int:
        try:
            if self.connect_milvus():
                collection = Collection(self.collection_name)
                return collection.num_entities
            return 0
        except:
            return 0

character_recognizer = CharacterRecognizer()