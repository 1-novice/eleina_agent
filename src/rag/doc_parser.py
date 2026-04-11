"""文档解析与文本提取模块"""
from typing import Dict, List, Optional, Any, Tuple
import os
import tempfile
from src.rag.doc_manager import doc_manager


class DocParser:
    """文档解析类"""
    
    def __init__(self):
        pass
    
    def parse_document(self, doc_id: str) -> Dict[str, Any]:
        """解析文档
        
        Args:
            doc_id: 文档ID
            
        Returns:
            Dict[str, Any]: 解析结果
        """
        # 获取文档信息
        doc_info = doc_manager.get_document(doc_id)
        if not doc_info:
            raise ValueError(f"文档不存在: {doc_id}")
        
        file_path = doc_info.get("file_path")
        if not file_path or not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 更新文档状态
        doc_manager.update_document_status(doc_id, "处理中")
        
        try:
            # 根据文件类型选择解析方法
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext == ".pdf":
                parsed_content = self._parse_pdf(file_path)
            elif file_ext in [".docx", ".doc"]:
                parsed_content = self._parse_word(file_path)
            elif file_ext in [".txt", ".md", ".markdown"]:
                parsed_content = self._parse_text(file_path)
            else:
                parsed_content = self._parse_generic(file_path)
            
            # 更新文档状态
            doc_manager.update_document_status(doc_id, "已生效")
            
            return parsed_content
        except Exception as e:
            print(f"解析文档失败: {e}")
            # 更新文档状态
            doc_manager.update_document_status(doc_id, "已禁用")
            return {
                "status": "error",
                "message": str(e),
                "content": "",
                "metadata": {}
            }
    
    def _parse_pdf(self, file_path: str) -> Dict[str, Any]:
        """解析PDF文件
        
        Args:
            file_path: PDF文件路径
            
        Returns:
            Dict[str, Any]: 解析结果
        """
        return self._parse_pdf_fallback(file_path)
    
    def _parse_word(self, file_path: str) -> Dict[str, Any]:
        """解析Word文件
        
        Args:
            file_path: Word文件路径
            
        Returns:
            Dict[str, Any]: 解析结果
        """
        return self._parse_word_fallback(file_path)
    
    def _parse_text(self, file_path: str) -> Dict[str, Any]:
        """解析文本文件
        
        Args:
            file_path: 文本文件路径
            
        Returns:
            Dict[str, Any]: 解析结果
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            return {
                "status": "success",
                "content": content,
                "metadata": {
                    "file_type": "text",
                    "word_count": len(content.split()),
                    "line_count": len(content.splitlines())
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "content": "",
                "metadata": {}
            }
    
    def _parse_generic(self, file_path: str) -> Dict[str, Any]:
        """解析通用文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            Dict[str, Any]: 解析结果
        """
        return self._parse_text(file_path)
    
    def _parse_pdf_fallback(self, file_path: str) -> Dict[str, Any]:
        """PDF解析方法
        
        Args:
            file_path: PDF文件路径
            
        Returns:
            Dict[str, Any]: 解析结果
        """
        try:
            # 尝试使用PyPDF2
            try:
                import PyPDF2
                with open(file_path, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    content = []
                    for page_num in range(len(reader.pages)):
                        page = reader.pages[page_num]
                        content.append(page.extract_text())
                    return {
                        "status": "success",
                        "content": "\n".join(content),
                        "metadata": {
                            "file_type": "pdf",
                            "page_count": len(reader.pages)
                        }
                    }
            except ImportError:
                # 尝试使用pdfminer
                try:
                    from pdfminer.high_level import extract_text
                    content = extract_text(file_path)
                    return {
                        "status": "success",
                        "content": content,
                        "metadata": {
                            "file_type": "pdf"
                        }
                    }
                except ImportError:
                    return {
                        "status": "error",
                        "message": "缺少PDF解析库，请安装PyPDF2或pdfminer",
                        "content": "",
                        "metadata": {}
                    }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "content": "",
                "metadata": {}
            }
    
    def _parse_word_fallback(self, file_path: str) -> Dict[str, Any]:
        """Word解析方法
        
        Args:
            file_path: Word文件路径
            
        Returns:
            Dict[str, Any]: 解析结果
        """
        try:
            # 尝试使用python-docx
            try:
                import docx
                doc = docx.Document(file_path)
                content = []
                for paragraph in doc.paragraphs:
                    content.append(paragraph.text)
                return {
                    "status": "success",
                    "content": "\n".join(content),
                    "metadata": {
                        "file_type": "word"
                    }
                }
            except ImportError:
                return {
                    "status": "error",
                    "message": "缺少Word解析库，请安装python-docx",
                    "content": "",
                    "metadata": {}
                }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "content": "",
                "metadata": {}
            }
    
    def batch_parse_documents(self, doc_ids: List[str]) -> Dict[str, Any]:
        """批量解析文档
        
        Args:
            doc_ids: 文档ID列表
            
        Returns:
            Dict[str, Any]: 批量解析结果
        """
        results = {}
        for doc_id in doc_ids:
            try:
                results[doc_id] = self.parse_document(doc_id)
            except Exception as e:
                results[doc_id] = {
                    "status": "error",
                    "message": str(e),
                    "content": "",
                    "metadata": {}
                }
        return results
    
    def parse_document_by_path(self, file_path: str) -> Dict[str, Any]:
        """根据文件路径解析文档
        
        Args:
            file_path: 文件路径
            
        Returns:
            Dict[str, Any]: 解析结果
        """
        if not file_path or not os.path.exists(file_path):
            return {
                "status": "error",
                "message": f"文件不存在: {file_path}",
                "content": "",
                "metadata": {}
            }
        
        try:
            # 根据文件类型选择解析方法
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext == ".pdf":
                parsed_content = self._parse_pdf_fallback(file_path)
            elif file_ext in [".docx", ".doc"]:
                parsed_content = self._parse_word_fallback(file_path)
            elif file_ext in [".txt", ".md", ".markdown"]:
                parsed_content = self._parse_text(file_path)
            else:
                parsed_content = self._parse_text(file_path)
            
            return parsed_content
        except Exception as e:
            print(f"解析文档失败: {e}")
            return {
                "status": "error",
                "message": str(e),
                "content": "",
                "metadata": {}
            }


# 全局文档解析器实例
doc_parser = DocParser()