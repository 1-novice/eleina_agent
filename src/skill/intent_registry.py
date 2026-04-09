from typing import Dict, List, Optional, Any
import yaml
import os


class IntentRegistry:
    def __init__(self, config_path: Optional[str] = None):
        self.intents = {}
        self.config_path = config_path
        if config_path and os.path.exists(config_path):
            self.load_from_config(config_path)
    
    def register_intent(self, intent_name: str, patterns: List[str], 
                      skill_id: str, confidence_threshold: float = 0.7, 
                      priority: int = 0):
        """注册意图
        
        Args:
            intent_name: 意图名称
            patterns: 触发话术模板/关键词
            skill_id: 绑定的Skill ID
            confidence_threshold: 置信度阈值
            priority: 优先级
        """
        self.intents[intent_name] = {
            "name": intent_name,
            "patterns": patterns,
            "skill_id": skill_id,
            "confidence_threshold": confidence_threshold,
            "priority": priority
        }
    
    def load_from_config(self, config_path: str):
        """从配置文件加载意图
        
        Args:
            config_path: 配置文件路径
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            if 'intents' in config:
                for intent in config['intents']:
                    self.register_intent(
                        intent_name=intent['name'],
                        patterns=intent['patterns'],
                        skill_id=intent['skill_id'],
                        confidence_threshold=intent.get('confidence_threshold', 0.7),
                        priority=intent.get('priority', 0)
                    )
        except Exception as e:
            print(f"加载意图配置失败: {e}")
    
    def get_intent(self, intent_name: str) -> Optional[Dict[str, Any]]:
        """获取意图信息
        
        Args:
            intent_name: 意图名称
            
        Returns:
            Optional[Dict[str, Any]]: 意图信息
        """
        return self.intents.get(intent_name)
    
    def get_all_intents(self) -> Dict[str, Dict[str, Any]]:
        """获取所有意图
        
        Returns:
            Dict[str, Dict[str, Any]]: 意图字典
        """
        return self.intents
    
    def get_intents_by_skill(self, skill_id: str) -> List[Dict[str, Any]]:
        """根据Skill ID获取意图
        
        Args:
            skill_id: Skill ID
            
        Returns:
            List[Dict[str, Any]]: 意图列表
        """
        intents = []
        for intent in self.intents.values():
            if intent['skill_id'] == skill_id:
                intents.append(intent)
        return intents


# 全局意图注册中心实例
intent_registry = IntentRegistry()