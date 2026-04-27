"""text2vec向量化模块 - 封装Jerry0/text2vec-base-chinese模型"""
from typing import List, Dict, Optional
import os
import hashlib
import struct

class Text2VecEmbedding:
    """Jerry0/text2vec-base-chinese模型封装类"""
    
    def __init__(self, model_path: str = "D:\\models\\shibing624_text2vec-base-chinese", save_cache: bool = True):
        """初始化text2vec模型
        
        Args:
            model_path: 模型本地路径
            save_cache: 是否保存缓存（设为False可提升性能）
        """
        self.model_path = model_path
        self.model = None
        self.tokenizer = None
        self.cache_dir = "data/text2vec_embedding_cache"
        self.env = None
        self.embedding_dim = 768
        self.device = "cpu"
        self.save_cache = save_cache
        self._init_cache()
        self._load_model()
    
    def _init_cache(self, initial_size_gb: int = 3, max_size_gb: int = 20):
        """初始化LMDB缓存（支持动态扩容）
        
        Args:
            initial_size_gb: 初始预分配空间（GB），默认3GB
            max_size_gb: 最大允许空间（GB），默认50GB
        """
        import lmdb
        
        os.makedirs(self.cache_dir, exist_ok=True)
        
        self._current_map_size = initial_size_gb * 1024 * 1024 * 1024
        self._max_map_size = max_size_gb * 1024 * 1024 * 1024
        self._growth_step = 1 * 1024 * 1024 * 1024  # 每次扩容1GB
        
        self.env = lmdb.open(
            self.cache_dir,
            map_size=self._current_map_size,
            max_dbs=1,
            readonly=False,
            lock=True,
            readahead=False,
            meminit=False
        )
        
        print(f"✓ LMDB缓存初始化完成: {self.cache_dir}")
        print(f"  初始容量: {initial_size_gb}GB, 最大容量: {max_size_gb}GB, 扩容步长: 1GB")
    
    def _resize_cache(self):
        """动态扩容LMDB缓存"""
        if self._current_map_size >= self._max_map_size:
            print(f"⚠️  LMDB缓存已达最大容量 {self._max_map_size // (1024**3)}GB")
            return False
        
        new_size = min(self._current_map_size + self._growth_step, self._max_map_size)
        print(f"📈 LMDB缓存扩容: {self._current_map_size // (1024**3)}GB -> {new_size // (1024**3)}GB")
        
        try:
            self.env.close()
            self._current_map_size = new_size
            import lmdb
            self.env = lmdb.open(
                self.cache_dir,
                map_size=self._current_map_size,
                max_dbs=1,
                readonly=False,
                lock=True,
                readahead=False,
                meminit=False
            )
            return True
        except Exception as e:
            print(f"✗ LMDB缓存扩容失败: {e}")
            return False
    
    def _get_cache_key(self, text: str) -> bytes:
        """生成文本的缓存键（使用MD5哈希）"""
        return hashlib.md5(text.encode('utf-8')).digest()
    
    def _vector_to_bytes(self, vector: List[float]) -> bytes:
        """将向量转换为二进制数据"""
        return struct.pack(f'{len(vector)}f', *vector)
    
    def _bytes_to_vector(self, data: bytes) -> List[float]:
        """将二进制数据转换为向量"""
        count = len(data) // 4
        return list(struct.unpack(f'{count}f', data))
    
    def _get_from_cache(self, text: str) -> Optional[List[float]]:
        """从LMDB缓存获取向量"""
        if not self.env:
            return None
        
        key = self._get_cache_key(text)
        
        try:
            with self.env.begin(write=False) as txn:
                data = txn.get(key)
                if data:
                    return self._bytes_to_vector(data)
        except Exception:
            pass
        
        return None
    
    def _set_to_cache(self, text: str, vector: List[float]):
        """将向量写入LMDB缓存（支持自动扩容）"""
        if not self.save_cache or not self.env:
            return
        
        key = self._get_cache_key(text)
        data = self._vector_to_bytes(vector)
        
        try:
            with self.env.begin(write=True) as txn:
                txn.put(key, data)
        except lmdb.MapFullError:
            print(f"⚠️  LMDB缓存空间不足，尝试扩容...")
            if self._resize_cache():
                try:
                    with self.env.begin(write=True) as txn:
                        txn.put(key, data)
                    print("✓ 扩容后写入成功")
                except Exception as e:
                    print(f"✗ 扩容后写入仍失败: {e}")
        except Exception as e:
            print(f"✗ 写入缓存失败: {e}")
    
    def _get_cache_size(self) -> int:
        """获取缓存数量"""
        if not self.env:
            return 0
        
        try:
            with self.env.begin(write=False) as txn:
                return txn.stat()['entries']
        except Exception:
            return 0
    
    def _clear_cache(self):
        """清空LMDB缓存"""
        if not self.env:
            return
        
        try:
            self.env.close()
            import shutil
            shutil.rmtree(self.cache_dir)
            os.makedirs(self.cache_dir, exist_ok=True)
            self._init_cache()
            print("✓ LMDB缓存已清空")
        except Exception as e:
            print(f"✗ 清空缓存失败: {e}")
    
    def _load_model(self):
        """加载text2vec模型（支持GPU加速）"""
        try:
            from sentence_transformers import SentenceTransformer
            import torch
            
            if torch.cuda.is_available():
                self.device = "cuda"
                print(f"✓ CUDA可用，使用GPU加速")
            else:
                self.device = "cpu"
                print(f"⚠️ CUDA不可用，使用CPU")
            
            self.model = SentenceTransformer(self.model_path, device=self.device)
            print(f"✓ 成功加载text2vec模型: {self.model_path}")
            print(f"✓ 使用设备: {self.device.upper()}")
            
            if self.device == "cuda":
                print(f"✓ GPU名称: {torch.cuda.get_device_name(0)}")
                print(f"✓ GPU显存: {torch.cuda.get_device_properties(0).total_memory / (1024**3):.2f} GB")
                
        except ImportError as e:
            print("✗ 未安装sentence_transformers库，请安装: pip install sentence-transformers")
            raise
        except Exception as e:
            print(f"✗ 加载text2vec模型失败: {e}")
            raise
    
    def embed(self, text: str) -> List[float]:
        """向量化单个文本"""
        text = str(text).strip()
        
        cached = self._get_from_cache(text)
        if cached is not None:
            return cached
        
        if not text:
            return [0.0] * self.embedding_dim
        
        try:
            vector = self.model.encode(text).tolist()
            self._set_to_cache(text, vector)
            return vector
        except Exception as e:
            print(f"向量化失败: {e}")
            return self._fallback_embed(text)
    
    def embed_batch(self, texts: List[str], batch_size: int = 10000) -> List[List[float]]:
        """批量向量化（每1万条打印进度）"""
        vectors = []
        total_texts = len(texts)
        processed_count = 0
        batch_count = 0
        
        cache_hits = 0
        texts_to_embed = []
        indices_to_embed = []
        
        for i, text in enumerate(texts):
            text = str(text).strip()
            cached = self._get_from_cache(text)
            if cached is not None:
                vectors.append(cached)
                cache_hits += 1
                processed_count += 1
            else:
                vectors.append(None)
                texts_to_embed.append(text)
                indices_to_embed.append(i)
        
        print(f"  缓存命中: {cache_hits}/{total_texts}")
        print(f"  需要向量化: {total_texts - cache_hits} 条")
        
        if texts_to_embed:
            total_to_embed = len(texts_to_embed)
            print(f"\n  开始分批向量化...")
            
            for i in range(0, total_to_embed, batch_size):
                batch_end = min(i + batch_size, total_to_embed)
                batch_texts = texts_to_embed[i:batch_end]
                batch_indices = indices_to_embed[i:batch_end]
                
                try:
                    batch_vectors = self.model.encode(batch_texts).tolist()
                    
                    for j, idx in enumerate(batch_indices):
                        vector = batch_vectors[j]
                        vectors[idx] = vector
                        self._set_to_cache(batch_texts[j], vector)
                    
                    processed_count += len(batch_texts)
                    batch_count += 1
                    
                    if batch_count % 1 == 0:
                        progress = (processed_count / total_texts) * 100
                        print(f"    批次 {batch_count}: 完成 {processed_count}/{total_texts} ({progress:.1f}%)")
                        
                except Exception as e:
                    print(f"    ✗ 批次 {batch_count} 失败: {e}")
                    for j, idx in enumerate(batch_indices):
                        vectors[idx] = self._fallback_embed(batch_texts[j])
            
            print(f"\n  ✓ 向量化完成，缓存共 {self._get_cache_size()} 条")
        
        return vectors
    
    def _fallback_embed(self, text: str) -> List[float]:
        """备选向量化方案"""
        hash_obj = hashlib.md5(text.encode())
        hash_hex = hash_obj.hexdigest()
        
        vector = []
        for i in range(0, len(hash_hex), 2):
            if i + 1 < len(hash_hex):
                value = int(hash_hex[i:i+2], 16) / 255.0
                vector.append(value)
        
        while len(vector) < self.embedding_dim:
            vector.append(0.0)
        if len(vector) > self.embedding_dim:
            vector = vector[:self.embedding_dim]
        
        return vector
    
    def get_embedding_dim(self) -> int:
        """获取向量维度"""
        return self.embedding_dim
    
    def clear_cache(self):
        """清空缓存"""
        self._clear_cache()
    
    def get_cache_size(self) -> int:
        """获取缓存大小"""
        return self._get_cache_size()
    
    def close(self):
        """关闭LMDB环境"""
        if self.env:
            self.env.close()


text2vec_embedding = Text2VecEmbedding()


def create_text2vec_embedding(model_path: Optional[str] = None) -> Text2VecEmbedding:
    """创建text2vec嵌入实例"""
    if model_path is None:
        model_path = "D:\\models\\shibing624_text2vec-base-chinese"
    return Text2VecEmbedding(model_path)