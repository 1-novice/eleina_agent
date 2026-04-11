"""文档接入与管理模块"""
from typing import Dict, List, Optional, Any
import os
import time
import hashlib
from datetime import datetime
from src.config.config import settings


class DocManager:
    """文档管理类"""
    
    def __init__(self):
        self.documents = {}
        self.document_dir = os.path.join("data", "docs")
        os.makedirs(self.document_dir, exist_ok=True)
    
    def add_document(self, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """添加文档
        
        Args:
            file_path: 文件路径
            metadata: 文档元数据
            
        Returns:
            str: 文档ID
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 生成文档ID
        doc_id = self._generate_doc_id(file_path)
        
        # 复制文件到文档目录
        file_name = os.path.basename(file_path)
        dest_path = os.path.join(self.document_dir, file_name)
        
        # 如果文件已存在，创建新的版本
        version = 1
        if os.path.exists(dest_path):
            # 检查是否是相同文件
            if self._is_same_file(file_path, dest_path):
                # 相同文件，返回现有文档ID
                return doc_id
            # 不同文件，创建新版本
            base_name, ext = os.path.splitext(file_name)
            timestamp = int(time.time())
            dest_path = os.path.join(self.document_dir, f"{base_name}_{timestamp}{ext}")
            version = 2
        
        # 复制文件
        import shutil
        shutil.copy2(file_path, dest_path)
        
        # 构建元数据
        if metadata is None:
            metadata = {}
        
        doc_metadata = {
            "id": doc_id,
            "file_name": file_name,
            "file_path": dest_path,
            "original_path": file_path,
            "version": version,
            "status": "待处理",
            "upload_time": datetime.now().isoformat(),
            "uploader": metadata.get("uploader", "system"),
            "title": metadata.get("title", file_name),
            "source": metadata.get("source", "local"),
            "tags": metadata.get("tags", []),
            "permissions": metadata.get("permissions", ["public"])
        }
        
        # 存储文档信息
        self.documents[doc_id] = doc_metadata
        
        # 保存到文件
        self._save_documents()
        
        return doc_id
    
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """获取文档信息
        
        Args:
            doc_id: 文档ID
            
        Returns:
            Optional[Dict[str, Any]]: 文档信息
        """
        self._load_documents()
        return self.documents.get(doc_id)
    
    def get_all_documents(self) -> List[Dict[str, Any]]:
        """获取所有文档
        
        Returns:
            List[Dict[str, Any]]: 文档列表
        """
        self._load_documents()
        return list(self.documents.values())
    
    def update_document(self, doc_id: str, metadata: Dict[str, Any]) -> bool:
        """更新文档信息
        
        Args:
            doc_id: 文档ID
            metadata: 要更新的元数据
            
        Returns:
            bool: 是否更新成功
        """
        self._load_documents()
        if doc_id not in self.documents:
            return False
        
        # 更新元数据
        self.documents[doc_id].update(metadata)
        
        # 保存到文件
        self._save_documents()
        return True
    
    def delete_document(self, doc_id: str) -> bool:
        """删除文档
        
        Args:
            doc_id: 文档ID
            
        Returns:
            bool: 是否删除成功
        """
        self._load_documents()
        if doc_id not in self.documents:
            return False
        
        # 删除文件
        doc_info = self.documents[doc_id]
        file_path = doc_info.get("file_path")
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # 删除文档信息
        del self.documents[doc_id]
        
        # 保存到文件
        self._save_documents()
        return True
    
    def update_document_status(self, doc_id: str, status: str) -> bool:
        """更新文档状态
        
        Args:
            doc_id: 文档ID
            status: 新状态
            
        Returns:
            bool: 是否更新成功
        """
        return self.update_document(doc_id, {"status": status})
    
    def get_documents_by_status(self, status: str) -> List[Dict[str, Any]]:
        """根据状态获取文档
        
        Args:
            status: 文档状态
            
        Returns:
            List[Dict[str, Any]]: 文档列表
        """
        self._load_documents()
        return [doc for doc in self.documents.values() if doc.get("status") == status]
    
    def _generate_doc_id(self, file_path: str) -> str:
        """生成文档ID
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 文档ID
        """
        # 使用文件路径和时间戳生成唯一ID
        content = f"{file_path}_{time.time()}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _is_same_file(self, file1: str, file2: str) -> bool:
        """检查两个文件是否相同
        
        Args:
            file1: 第一个文件路径
            file2: 第二个文件路径
            
        Returns:
            bool: 是否相同
        """
        # 比较文件大小
        if os.path.getsize(file1) != os.path.getsize(file2):
            return False
        
        # 比较文件内容
        with open(file1, "rb") as f1, open(file2, "rb") as f2:
            return f1.read() == f2.read()
    
    def _save_documents(self):
        """保存文档信息到文件"""
        import json
        data_file = os.path.join(self.document_dir, "documents.json")
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(self.documents, f, ensure_ascii=False, indent=2)
    
    def _load_documents(self):
        """从文件加载文档信息"""
        import json
        data_file = os.path.join(self.document_dir, "documents.json")
        if os.path.exists(data_file):
            with open(data_file, "r", encoding="utf-8") as f:
                try:
                    self.documents = json.load(f)
                except Exception:
                    self.documents = {}
    
    def initialize(self):
        """初始化文档管理"""
        # 加载现有文档
        self._load_documents()
        
        # 检查PDF文档路径配置
        pdf_path = settings.pdf_document_path
        if pdf_path and os.path.exists(pdf_path):
            # 添加PDF文档
            try:
                self.add_document(pdf_path, {
                    "title": "PDF文档",
                    "source": "config"
                })
                print(f"已加载PDF文档: {pdf_path}")
            except Exception as e:
                print(f"加载PDF文档失败: {e}")


# 全局文档管理实例
doc_manager = DocManager()