from typing import Dict, List, Optional, Any
import os

# 尝试导入yaml
try:
    import yaml
    has_yaml = True
except ImportError:
    has_yaml = False
    print("警告: 无法导入yaml模块，将禁用配置文件加载功能")


class ToolRegistry:
    def __init__(self, config_path: Optional[str] = None):
        self.tools = {}
        self.config_path = config_path
        if config_path and os.path.exists(config_path):
            self.load_from_config(config_path)
    
    def register_tool(self, name: str, description: str, parameters: Dict[str, Any], 
                     return_schema: Dict[str, Any], permissions: List[str] = None, 
                     rate_limit: int = 100):
        """注册工具
        
        Args:
            name: 工具名称
            description: 工具描述
            parameters: 参数列表
            return_schema: 返回值格式
            permissions: 权限列表
            rate_limit: 限流配置
        """
        self.tools[name] = {
            "name": name,
            "description": description,
            "parameters": parameters,
            "return_schema": return_schema,
            "permissions": permissions or [],
            "rate_limit": rate_limit
        }
    
    def load_from_config(self, config_path: str):
        """从配置文件加载工具
        
        Args:
            config_path: 配置文件路径
        """
        if not has_yaml:
            print("警告: yaml模块不可用，跳过配置文件加载")
            return
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            if 'tools' in config:
                for tool in config['tools']:
                    self.register_tool(
                        name=tool['name'],
                        description=tool['description'],
                        parameters=tool['parameters'],
                        return_schema=tool['return_schema'],
                        permissions=tool.get('permissions'),
                        rate_limit=tool.get('rate_limit', 100)
                    )
        except Exception as e:
            print(f"加载工具配置失败: {e}")
    
    def get_tool(self, name: str) -> Optional[Dict[str, Any]]:
        """获取工具信息
        
        Args:
            name: 工具名称
            
        Returns:
            Optional[Dict[str, Any]]: 工具信息
        """
        return self.tools.get(name)
    
    def get_all_tools(self) -> Dict[str, Dict[str, Any]]:
        """获取所有工具
        
        Returns:
            Dict[str, Dict[str, Any]]: 工具字典
        """
        return self.tools
    
    def get_tools_for_llm(self) -> List[Dict[str, Any]]:
        """获取用于LLM的工具列表
        
        Returns:
            List[Dict[str, Any]]: 工具列表
        """
        tool_list = []
        for tool_name, tool_info in self.tools.items():
            tool_list.append({
                "type": "function",
                "function": {
                    "name": tool_info["name"],
                    "description": tool_info["description"],
                    "parameters": {
                        "type": "object",
                        "properties": tool_info["parameters"],
                        "required": [k for k, v in tool_info["parameters"].items() if v.get("required", False)]
                    }
                }
            })
        return tool_list


# 全局工具注册表实例
tool_registry = ToolRegistry()