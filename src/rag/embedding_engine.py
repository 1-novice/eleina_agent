"""向量化引擎模块"""
from typing import List, Dict, Optional, Any
import os
import json
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


class EmbeddingEngine:
    """向量化引擎类"""
    
    def __init__(self, model_name: str = "text-embedding-v3"):
        """初始化向量化引擎
        
        Args:
            model_name: 模型名称
        """
        self.model_name = model_name
        self.cache_file = "data/embedding_cache.json"
        self.cache = self._load_cache()
        self.api_key = self._get_api_key()
        self.api_url = "https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/text-embedding"
    
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
    
    def _load_cache(self) -> Dict[str, List[float]]:
        """加载缓存
        
        Returns:
            Dict[str, List[float]]: 缓存字典
        """
        os.makedirs('data', exist_ok=True)
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def _save_cache(self):
        """保存缓存"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def embed(self, text: str) -> List[float]:
        """向量化单个文本
        
        Args:
            text: 文本
            
        Returns:
            List[float]: 向量
        """
        # 检查缓存
        if text in self.cache:
            return self.cache[text]
        
        # 调用API
        try:
            vector = self._call_api([text])[0]
            # 保存到缓存
            self.cache[text] = vector
            self._save_cache()
            return vector
        except Exception as e:
            print(f"向量化失败: {e}")
            # 使用本地向量化作为备选
            return self._local_embed(text)
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量向量化
        
        Args:
            texts: 文本列表
            
        Returns:
            List[List[float]]: 向量列表
        """
        vectors = []
        uncached_texts = []
        uncached_indices = []
        
        # 检查缓存
        for i, text in enumerate(texts):
            if text in self.cache:
                vectors.append(self.cache[text])
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)
        
        # 批量处理未缓存的文本
        if uncached_texts:
            try:
                batch_vectors = self._call_api(uncached_texts)
                # 填充结果
                for i, idx in enumerate(uncached_indices):
                    vector = batch_vectors[i]
                    vectors.insert(idx, vector)
                    # 保存到缓存
                    self.cache[uncached_texts[i]] = vector
                # 保存缓存
                self._save_cache()
            except Exception as e:
                print(f"批量向量化失败: {e}")
                # 使用本地向量化作为备选
                for i, idx in enumerate(uncached_indices):
                    vector = self._local_embed(uncached_texts[i])
                    vectors.insert(idx, vector)
        
        return vectors
    
    def _call_api(self, texts: List[str]) -> List[List[float]]:
        """调用API
        
        Args:
            texts: 文本列表
            
        Returns:
            List[List[float]]: 向量列表
        """
        if not self.api_key:
            raise ValueError("未配置API密钥")
        
        # 处理文本列表
        processed_texts = []
        for text in texts:
            # 检查空字符串
            if not text or text.strip() == "":
                # 替换为空字符串
                processed_texts.append("")
                continue
            
            # 移除不可见特殊字符
            text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t\r')
            
            # 限制文本长度（2048字符）
            text = text[:2048]
            
            processed_texts.append(text)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model_name,
            "input": {
                "texts": processed_texts
            },
            "parameters": {
                "dimension": 1024,  # 指定1024维度
                "output_type": "dense"  # 指定输出类型为dense
            }
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
                vectors = []
                for item in result.get('output', {}).get('embeddings', []):
                    vectors.append(item.get('embedding', []))
                
                return vectors
            except Exception as e:
                print(f"API调用失败 (尝试 {i+1}/{max_retries}): {e}")
                if i < max_retries - 1:
                    time.sleep(2 ** i)  # 指数退避
                else:
                    raise
    
    def _local_embed(self, text: str) -> List[float]:
        """本地向量化（备选方案）
        
        Args:
            text: 文本
            
        Returns:
            List[float]: 向量
        """
        # 简单的基于字符频率的向量化
        import hashlib
        
        # 计算文本的哈希值
        hash_obj = hashlib.md5(text.encode())
        hash_hex = hash_obj.hexdigest()
        
        # 将哈希值转换为1024维向量
        vector = []
        for i in range(0, len(hash_hex), 2):
            if i + 1 < len(hash_hex):
                value = int(hash_hex[i:i+2], 16) / 255.0
                vector.append(value)
        
        # 确保向量长度为1024
        while len(vector) < 1024:
            vector.append(0.0)
        if len(vector) > 1024:
            vector = vector[:1024]
        
        return vector
    
    def get_embedding_dim(self) -> int:
        """获取向量维度
        
        Returns:
            int: 向量维度
        """
        return 1024  # 固定为1024维度
    
    def clear_cache(self):
        """清空缓存"""
        self.cache = {}
        self._save_cache()
    
    def get_cache_size(self) -> int:
        """获取缓存大小
        
        Returns:
            int: 缓存大小
        """
        return len(self.cache)


# 全局向量化引擎实例
embedding_engine = EmbeddingEngine()