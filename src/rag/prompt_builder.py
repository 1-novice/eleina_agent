"""上下文构建模块"""
from typing import Dict, List, Optional, Any


class PromptBuilder:
    """Prompt构建器类"""
    
    def __init__(self, max_tokens: int = 2000):
        """初始化Prompt构建器
        
        Args:
            max_tokens: 最大token数
        """
        self.max_tokens = max_tokens
    
    def build_prompt(self, query: str, documents: List[Dict[str, Any]]) -> str:
        """构建Prompt
        
        Args:
            query: 查询文本
            documents: 文档列表
            
        Returns:
            str: 构建的Prompt
        """
        # 1. 去重
        unique_docs = self._deduplicate_documents(documents)
        
        # 2. 长度控制
        trimmed_docs = self._trim_documents(unique_docs, query)
        
        # 3. 构建Prompt
        prompt = self._build_prompt_template(query, trimmed_docs)
        
        return prompt
    
    def _deduplicate_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重文档
        
        Args:
            documents: 文档列表
            
        Returns:
            List[Dict[str, Any]]: 去重后的文档列表
        """
        seen_texts = set()
        unique_docs = []
        
        for doc in documents:
            text = doc.get('text', '')
            if text not in seen_texts:
                seen_texts.add(text)
                unique_docs.append(doc)
        
        return unique_docs
    
    def _trim_documents(self, documents: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """裁剪文档以控制长度
        
        Args:
            documents: 文档列表
            query: 查询文本
            
        Returns:
            List[Dict[str, Any]]: 裁剪后的文档列表
        """
        # 估算query的token数
        query_tokens = self._count_tokens(query)
        remaining_tokens = self.max_tokens - query_tokens - 100  # 预留100token给模板
        
        trimmed_docs = []
        current_tokens = 0
        
        for doc in documents:
            text = doc.get('text', '')
            doc_tokens = self._count_tokens(text)
            
            if current_tokens + doc_tokens <= remaining_tokens:
                trimmed_docs.append(doc)
                current_tokens += doc_tokens
            else:
                # 裁剪文档
                max_text_length = int((remaining_tokens - current_tokens) * 4)  # 假设平均每个token对应4个字符
                if max_text_length > 0:
                    # 尝试在句子边界处裁剪
                    trimmed_text = self._trim_text(text, max_text_length)
                    if trimmed_text:
                        doc['text'] = trimmed_text
                        trimmed_docs.append(doc)
                break
        
        return trimmed_docs
    
    def _trim_text(self, text: str, max_length: int) -> str:
        """裁剪文本
        
        Args:
            text: 文本
            max_length: 最大长度
            
        Returns:
            str: 裁剪后的文本
        """
        if len(text) <= max_length:
            return text
        
        # 尝试在句子边界处裁剪
        punctuation = ['.', '!', '?', '。', '！', '？']
        for i in range(max_length, max_length - 100, -1):
            if i < 0:
                break
            if text[i] in punctuation:
                return text[:i+1]
        
        # 尝试在单词边界处裁剪
        for i in range(max_length, max_length - 100, -1):
            if i < 0:
                break
            if text[i].isspace():
                return text[:i]
        
        # 直接裁剪
        return text[:max_length] + '...'
    
    def _build_prompt_template(self, query: str, documents: List[Dict[str, Any]]) -> str:
        """构建Prompt模板
        
        Args:
            query: 查询文本
            documents: 文档列表
            
        Returns:
            str: 构建的Prompt
        """
        template = """
请根据下面的参考资料回答用户问题，不要编造。
如果资料中没有答案，请直接说"根据现有资料无法回答"。

【参考资料】
{references}

【用户问题】
{query}

【回答】
"""
        
        # 构建参考资料
        references = []
        for i, doc in enumerate(documents):
            text = doc.get('text', '')
            metadata = doc.get('metadata', {})
            
            # 提取来源信息
            source = metadata.get('source', 'unknown')
            title = metadata.get('title', '文档' + str(i+1))
            
            # 构建参考资料条目
            reference = str(i+1) + '. [' + title + ']\n' + text + '\n'
            references.append(reference)
        
        # 填充模板
        prompt = template.format(
            references='\n'.join(references),
            query=query
        )
        
        return prompt
    
    def _count_tokens(self, text: str) -> int:
        """估算token数
        
        Args:
            text: 文本
            
        Returns:
            int: 估算的token数
        """
        # 简单估算：假设平均每个token对应4个字符
        return len(text) // 4
    
    def build_chat_prompt(self, query: str, documents: List[Dict[str, Any]], history: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """构建聊天Prompt
        
        Args:
            query: 查询文本
            documents: 文档列表
            history: 历史对话
            
        Returns:
            List[Dict[str, Any]]: 聊天Prompt
        """
        messages = []
        
        # 系统消息
        system_message = {
            "role": "system",
            "content": "你是一个基于知识库回答问题的智能助手，请根据提供的参考资料回答用户问题，不要编造。如果资料中没有答案，请直接说'根据现有资料无法回答'。"
        }
        messages.append(system_message)
        
        # 历史对话
        if history:
            for msg in history:
                messages.append(msg)
        
        # 构建参考资料
        references = []
        for i, doc in enumerate(documents):
            text = doc.get('text', '')
            metadata = doc.get('metadata', {})
            
            # 提取来源信息
            source = metadata.get('source', 'unknown')
            title = metadata.get('title', '文档' + str(i+1))
            
            # 构建参考资料条目
            reference = str(i+1) + '. [' + title + ']\n' + text + '\n'
            references.append(reference)
        
        # 用户消息
        references_str = '\n'.join(references)
        user_message = {
            "role": "user",
            "content": '\n【参考资料】\n' + references_str + '\n\n【用户问题】\n' + query
        }
        messages.append(user_message)
        
        return messages


# 全局Prompt构建器实例
prompt_builder = PromptBuilder()