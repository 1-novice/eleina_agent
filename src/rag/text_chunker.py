"""文本分块模块"""
from typing import Dict, List, Optional, Any, Tuple
import re

# 纯Python分句函数
def sent_tokenize(text: str) -> List[str]:
    """纯Python实现的句子分割
    
    Args:
        text: 文本
        
    Returns:
        List[str]: 句子列表
    """
    # 使用正则表达式分割句子
    # 匹配句号、问号、感叹号等标点符号
    sentences = re.split(r'[.!?。！？]', text)
    # 过滤空句子并去除首尾空格
    sentences = [s.strip() for s in sentences if s.strip()]
    return sentences

# 标记为不使用nltk
has_nltk = False
print("使用纯Python分句函数")


class TextChunker:
    """文本分块类"""
    
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 64):
        """初始化文本分块器
        
        Args:
            chunk_size: 块大小
            chunk_overlap: 重叠长度
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk_text(self, text: str, strategy: str = "semantic") -> List[Dict[str, Any]]:
        """分块文本
        
        Args:
            text: 文本内容
            strategy: 分块策略，可选值：paragraph, semantic, heading, fixed
            
        Returns:
            List[Dict[str, Any]]: 分块结果列表
        """
        if strategy == "paragraph":
            return self._chunk_by_paragraph(text)
        elif strategy == "semantic":
            return self._chunk_by_semantics(text)
        elif strategy == "heading":
            return self._chunk_by_heading(text)
        elif strategy == "fixed":
            return self._chunk_by_fixed_length(text)
        else:
            raise ValueError(f"无效的分块策略: {strategy}")
    
    def _chunk_by_paragraph(self, text: str) -> List[Dict[str, Any]]:
        """按段落分块
        
        Args:
            text: 文本内容
            
        Returns:
            List[Dict[str, Any]]: 分块结果列表
        """
        # 按段落分割
        paragraphs = re.split(r'\n\s*\n', text)
        chunks = []
        current_chunk = []
        current_length = 0
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            paragraph_length = len(paragraph)
            
            # 如果当前段落长度超过块大小，单独作为一个块
            if paragraph_length > self.chunk_size:
                # 先处理当前块
                if current_chunk:
                    chunks.append({
                        "text": "\n\n".join(current_chunk),
                        "start_idx": 0,  # 简化处理，实际应计算真实索引
                        "end_idx": 0,
                        "length": current_length
                    })
                    current_chunk = []
                    current_length = 0
                
                # 将长段落分割成多个块
                sub_chunks = self._split_long_text(paragraph)
                chunks.extend(sub_chunks)
            else:
                # 检查添加当前段落后是否超过块大小
                if current_length + paragraph_length + 2 > self.chunk_size:  # +2 是换行符
                    # 保存当前块
                    chunks.append({
                        "text": "\n\n".join(current_chunk),
                        "start_idx": 0,
                        "end_idx": 0,
                        "length": current_length
                    })
                    # 开始新块，保留重叠部分
                    current_chunk = current_chunk[-1:] if current_chunk else []
                    current_length = len("\n\n".join(current_chunk))
                
                # 添加当前段落
                current_chunk.append(paragraph)
                current_length += paragraph_length + 2  # +2 是换行符
        
        # 处理最后一个块
        if current_chunk:
            chunks.append({
                "text": "\n\n".join(current_chunk),
                "start_idx": 0,
                "end_idx": 0,
                "length": current_length
            })
        
        return chunks
    
    def _chunk_by_semantics(self, text: str) -> List[Dict[str, Any]]:
        """按语义分块
        
        Args:
            text: 文本内容
            
        Returns:
            List[Dict[str, Any]]: 分块结果列表
        """
        # 按句子分割
        if has_nltk:
            try:
                sentences = sent_tokenize(text)
            except Exception as e:
                print(f"使用nltk分割句子失败: {e}")
                # 备选方法：按标点符号分割
                sentences = re.split(r'[.!?。！？]', text)
        else:
            # 备选方法：按标点符号分割
            sentences = re.split(r'[.!?。！？]', text)
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            sentence_length = len(sentence)
            
            # 如果当前句子长度超过块大小，单独作为一个块
            if sentence_length > self.chunk_size:
                # 先处理当前块
                if current_chunk:
                    chunks.append({
                        "text": " ".join(current_chunk),
                        "start_idx": 0,
                        "end_idx": 0,
                        "length": current_length
                    })
                    current_chunk = []
                    current_length = 0
                
                # 将长句子分割成多个块
                sub_chunks = self._split_long_text(sentence)
                chunks.extend(sub_chunks)
            else:
                # 检查添加当前句子后是否超过块大小
                if current_length + sentence_length + 1 > self.chunk_size:  # +1 是空格
                    # 保存当前块
                    chunks.append({
                        "text": " ".join(current_chunk),
                        "start_idx": 0,
                        "end_idx": 0,
                        "length": current_length
                    })
                    # 开始新块，保留重叠部分
                    overlap_size = min(len(current_chunk), 3)  # 保留最后3个句子作为重叠
                    current_chunk = current_chunk[-overlap_size:] if current_chunk else []
                    current_length = len(" ".join(current_chunk))
                
                # 添加当前句子
                current_chunk.append(sentence)
                current_length += sentence_length + 1  # +1 是空格
        
        # 处理最后一个块
        if current_chunk:
            chunks.append({
                "text": " ".join(current_chunk),
                "start_idx": 0,
                "end_idx": 0,
                "length": current_length
            })
        
        return chunks
    
    def _chunk_by_heading(self, text: str) -> List[Dict[str, Any]]:
        """按标题层级分块
        
        Args:
            text: 文本内容
            
        Returns:
            List[Dict[str, Any]]: 分块结果列表
        """
        # 按标题分割
        sections = re.split(r'(^#+ .+\n)', text, flags=re.MULTILINE)
        chunks = []
        current_chunk = []
        current_length = 0
        
        for i in range(0, len(sections), 2):
            # sections[i] 是标题前的内容，sections[i+1] 是标题
            if i + 1 < len(sections):
                heading = sections[i+1]
                content = sections[i]
                
                # 先处理标题前的内容
                if content.strip():
                    content_chunks = self._chunk_by_semantics(content)
                    chunks.extend(content_chunks)
                
                # 处理标题及其内容
                current_chunk = [heading]
                current_length = len(heading)
        
        # 处理最后一部分内容
        if len(sections) % 2 == 1 and sections[-1].strip():
            content_chunks = self._chunk_by_semantics(sections[-1])
            chunks.extend(content_chunks)
        
        return chunks
    
    def _chunk_by_fixed_length(self, text: str) -> List[Dict[str, Any]]:
        """按固定长度分块
        
        Args:
            text: 文本内容
            
        Returns:
            List[Dict[str, Any]]: 分块结果列表
        """
        chunks = []
        text_length = len(text)
        start_idx = 0
        
        while start_idx < text_length:
            end_idx = min(start_idx + self.chunk_size, text_length)
            
            # 尝试在句子边界处分割
            if end_idx < text_length:
                # 找到最近的句子结束位置
                sentence_end = text.rfind('.', start_idx, end_idx)
                if sentence_end != -1:
                    end_idx = sentence_end + 1
                else:
                    # 找不到句子结束，在单词边界处分割
                    word_end = text.rfind(' ', start_idx, end_idx)
                    if word_end != -1:
                        end_idx = word_end
            
            # 提取块
            chunk_text = text[start_idx:end_idx].strip()
            if chunk_text:
                chunks.append({
                    "text": chunk_text,
                    "start_idx": start_idx,
                    "end_idx": end_idx,
                    "length": len(chunk_text)
                })
            
            # 移动到下一个块，考虑重叠
            start_idx = end_idx - self.chunk_overlap
            if start_idx < 0:
                start_idx = 0
        
        return chunks
    
    def _split_long_text(self, text: str) -> List[Dict[str, Any]]:
        """分割长文本
        
        Args:
            text: 长文本
            
        Returns:
            List[Dict[str, Any]]: 分块结果列表
        """
        chunks = []
        text_length = len(text)
        start_idx = 0
        
        while start_idx < text_length:
            end_idx = min(start_idx + self.chunk_size, text_length)
            
            # 尝试在单词边界处分割
            if end_idx < text_length:
                word_end = text.rfind(' ', start_idx, end_idx)
                if word_end != -1:
                    end_idx = word_end
            
            # 提取块
            chunk_text = text[start_idx:end_idx].strip()
            if chunk_text:
                chunks.append({
                    "text": chunk_text,
                    "start_idx": start_idx,
                    "end_idx": end_idx,
                    "length": len(chunk_text)
                })
            
            # 移动到下一个块，考虑重叠
            start_idx = end_idx - self.chunk_overlap
            if start_idx < 0:
                start_idx = 0
        
        return chunks
    
    def batch_chunk(self, texts: List[str], strategy: str = "semantic") -> List[List[Dict[str, Any]]]:
        """批量分块
        
        Args:
            texts: 文本列表
            strategy: 分块策略
            
        Returns:
            List[List[Dict[str, Any]]]: 批量分块结果
        """
        return [self.chunk_text(text, strategy) for text in texts]


# 全局文本分块器实例
text_chunker = TextChunker()