from typing import Dict, List, Optional, Any
import time


class SecurityGateway:
    def __init__(self):
        # 权限配置
        self.permissions = {
            "get_weather": [],  # 所有人可调用
            "search_web": [],  # 所有人可调用
            "run_python": ["admin"],  # 只有管理员可调用
            "run_shell": ["admin"]  # 只有管理员可调用
        }
        
        # 限流配置
        self.rate_limits = {
            "get_weather": {"limit": 60, "window": 60},  # 每分钟60次
            "search_web": {"limit": 30, "window": 60},  # 每分钟30次
            "run_python": {"limit": 10, "window": 60},  # 每分钟10次
            "run_shell": {"limit": 5, "window": 60}  # 每分钟5次
        }
        
        # 调用记录，用于限流
        self.call_records = {}
    
    def check_permission(self, tool_name: str, user_role: str) -> bool:
        """检查权限
        
        Args:
            tool_name: 工具名称
            user_role: 用户角色
            
        Returns:
            bool: 是否有权限
        """
        # 获取工具的权限要求
        required_permissions = self.permissions.get(tool_name, [])
        
        # 如果没有权限要求，所有人都可以调用
        if not required_permissions:
            return True
        
        # 检查用户角色是否在权限列表中
        return user_role in required_permissions
    
    def check_rate_limit(self, tool_name: str, user_id: str) -> bool:
        """检查限流
        
        Args:
            tool_name: 工具名称
            user_id: 用户ID
            
        Returns:
            bool: 是否在限流范围内
        """
        # 获取工具的限流配置
        rate_limit = self.rate_limits.get(tool_name, {"limit": 100, "window": 60})
        limit = rate_limit.get("limit", 100)
        window = rate_limit.get("window", 60)
        
        # 清理过期的调用记录
        current_time = time.time()
        user_key = f"{user_id}:{tool_name}"
        
        if user_key not in self.call_records:
            self.call_records[user_key] = []
        
        # 清理过期的记录
        self.call_records[user_key] = [t for t in self.call_records[user_key] if current_time - t < window]
        
        # 检查是否超过限制
        if len(self.call_records[user_key]) >= limit:
            return False
        
        # 记录本次调用
        self.call_records[user_key].append(current_time)
        return True
    
    def check_sensitive_operation(self, tool_name: str, params: Dict[str, Any]) -> bool:
        """检查敏感操作
        
        Args:
            tool_name: 工具名称
            params: 参数字典
            
        Returns:
            bool: 是否为敏感操作
        """
        # 定义敏感操作
        sensitive_tools = ["run_shell"]
        
        if tool_name not in sensitive_tools:
            return False
        
        # 检查敏感参数
        if tool_name == "run_shell":
            command = params.get("command", "")
            # 检查危险命令
            dangerous_commands = ["rm -rf", "format", "delete", "drop table", "shutdown"]
            for dangerous in dangerous_commands:
                if dangerous in command.lower():
                    return True
        
        return False
    
    def sanitize_params(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """参数脱敏
        
        Args:
            tool_name: 工具名称
            params: 参数字典
            
        Returns:
            Dict[str, Any]: 脱敏后的参数字典
        """
        sanitized_params = params.copy()
        
        # 定义需要脱敏的字段
        sensitive_fields = ["password", "token", "secret", "api_key", "phone", "email", "id_card"]
        
        for field in sensitive_fields:
            if field in sanitized_params:
                sanitized_params[field] = "***"
        
        return sanitized_params
    
    def validate_tool_call(self, tool_name: str, params: Dict[str, Any], user_role: str, user_id: str) -> Dict[str, Any]:
        """验证工具调用
        
        Args:
            tool_name: 工具名称
            params: 参数字典
            user_role: 用户角色
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        # 检查权限
        if not self.check_permission(tool_name, user_role):
            return {
                "valid": False,
                "message": f"无权限调用工具 {tool_name}"
            }
        
        # 检查限流
        if not self.check_rate_limit(tool_name, user_id):
            return {
                "valid": False,
                "message": f"调用工具 {tool_name} 过于频繁，请稍后再试"
            }
        
        # 检查敏感操作
        if self.check_sensitive_operation(tool_name, params):
            return {
                "valid": False,
                "message": f"工具 {tool_name} 的操作过于危险，需要人工确认"
            }
        
        # 参数脱敏
        sanitized_params = self.sanitize_params(tool_name, params)
        
        return {
            "valid": True,
            "message": "验证通过",
            "params": sanitized_params
        }


# 全局安全网关实例
security_gateway = SecurityGateway()