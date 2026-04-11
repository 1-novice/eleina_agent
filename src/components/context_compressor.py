"""上下文裁剪与压缩器 - 管理对话上下文的长度和质量"""
from typing import List, Dict, Any, Optional
from datetime import datetime

class ContextCompressor:
    """上下文裁剪与压缩器"""
    
    def __init__(self):
        self.max_history_rounds = 10
        self.max_tokens = 2048
        self.summary_ratio = 0.3
        self.system_prompt = ""
    
    def set_system_prompt(self, prompt: str):
        """设置系统提示"""
        self.system_prompt = prompt
    
    def compress(self, messages: List[Dict[str, Any]], 
                 keep_recent_rounds: int = 3) -> List[Dict[str, Any]]:
        """压缩上下文"""
        if len(messages) <= keep_recent_rounds:
            return messages
        
        # 分离系统提示和对话历史
        system_messages = [m for m in messages if m.get("role") == "system"]
        user_messages = [m for m in messages if m.get("role") == "user"]
        assistant_messages = [m for m in messages if m.get("role") == "assistant"]
        
        # 保留最近的几轮对话
        recent_messages = []
        total_length = len(user_messages)
        
        if total_length > 0:
            start_idx = max(0, total_length - keep_recent_rounds)
            for i in range(start_idx, total_length):
                if i < len(user_messages):
                    recent_messages.append(user_messages[i])
                if i < len(assistant_messages):
                    recent_messages.append(assistant_messages[i])
        
        # 对早期对话进行摘要
        if total_length > keep_recent_rounds:
            early_messages = []
            for i in range(start_idx):
                if i < len(user_messages):
                    early_messages.append(user_messages[i])
                if i < len(assistant_messages):
                    early_messages.append(assistant_messages[i])
            
            summary = self._summarize(early_messages)
            if summary:
                summary_message = {
                    "role": "system",
                    "content": f"对话摘要（早期）：{summary}",
                    "timestamp": datetime.now().isoformat()
                }
                recent_messages.insert(0, summary_message)
        
        # 添加系统提示
        if self.system_prompt:
            system_message = {
                "role": "system",
                "content": self.system_prompt,
                "timestamp": datetime.now().isoformat()
            }
            recent_messages.insert(0, system_message)
        
        return recent_messages
    
    def _summarize(self, messages: List[Dict[str, Any]]) -> str:
        """生成对话摘要"""
        if not messages:
            return ""
        
        # 提取关键信息
        key_points = []
        
        for msg in messages:
            content = msg.get("content", "")
            if content:
                # 提取实体和动作
                entities = self._extract_entities(content)
                actions = self._extract_actions(content)
                
                if entities:
                    key_points.append(f"提到{entities}")
                if actions:
                    key_points.append(f"{actions}")
        
        if key_points:
            return "; ".join(key_points[:5])
        
        # 如果无法提取关键点，返回简短摘要
        contents = [m.get("content", "")[:50] for m in messages]
        return "；".join(contents[:3]) + "..."
    
    def _extract_entities(self, text: str) -> str:
        """提取实体"""
        patterns = [
            r"([\u4e00-\u9fa5]{2,4}(市|省|区|县))",  # 地点
            r"(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日号]?)",  # 日期
            r"(\d{1,2}[:点]\d{2})",  # 时间
            r"([\u4e00-\u9fa5]{2,4})",  # 人名
        ]
        
        entities = []
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                entities.append(match.group(1))
        
        return "、".join(entities[:3])
    
    def _extract_actions(self, text: str) -> str:
        """提取动作"""
        action_verbs = ["查询", "预订", "购买", "取消", "修改", "创建", "删除", "添加"]
        
        for verb in action_verbs:
            if verb in text:
                return f"{verb}操作"
        
        return ""
    
    def trim_by_tokens(self, messages: List[Dict[str, Any]], max_tokens: int) -> List[Dict[str, Any]]:
        """按token数量裁剪"""
        total_tokens = 0
        trimmed = []
        
        # 倒序遍历，保留最新的
        for msg in reversed(messages):
            msg_tokens = len(msg.get("content", "")) // 4  # 粗略估算
            if total_tokens + msg_tokens <= max_tokens:
                trimmed.insert(0, msg)
                total_tokens += msg_tokens
            else:
                # 截断消息内容
                content = msg.get("content", "")
                remaining_tokens = max_tokens - total_tokens
                truncated_content = content[:remaining_tokens * 4] + "..."
                msg["content"] = truncated_content
                trimmed.insert(0, msg)
                break
        
        return trimmed
    
    def clean_context(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """清理上下文，去除重复和无用信息"""
        cleaned = []
        seen_contents = set()
        
        for msg in messages:
            content = msg.get("content", "").strip()
            if content and content not in seen_contents:
                seen_contents.add(content)
                cleaned.append(msg)
        
        return cleaned
    
    def merge_consecutive_same_role(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """合并连续相同角色的消息"""
        if not messages:
            return messages
        
        merged = [messages[0]]
        
        for msg in messages[1:]:
            last_msg = merged[-1]
            if last_msg.get("role") == msg.get("role"):
                last_msg["content"] += "\n" + msg.get("content", "")
            else:
                merged.append(msg)
        
        return merged


import re

# 全局上下文压缩器实例
context_compressor = ContextCompressor()
