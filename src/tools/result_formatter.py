from typing import Dict, List, Optional, Any


class ResultFormatter:
    def __init__(self):
        pass
    
    def format_result(self, tool_result: Dict[str, Any]) -> str:
        """格式化工具执行结果
        
        Args:
            tool_result: 工具执行结果
            
        Returns:
            str: 格式化后的自然语言
        """
        tool_name = tool_result.get("tool", "")
        status = tool_result.get("status", "")
        result = tool_result.get("result", "")
        
        if status == "error":
            return f"工具执行失败: {result}"
        
        # 根据工具类型格式化结果
        if tool_name == "get_weather":
            return self._format_weather_result(result)
        elif tool_name == "search_web":
            return self._format_search_result(result)
        elif tool_name == "run_python":
            return self._format_python_result(result)
        elif tool_name == "run_shell":
            return self._format_shell_result(result)
        else:
            return self._format_generic_result(result)
    
    def _format_weather_result(self, result: Dict[str, Any]) -> str:
        """格式化天气查询结果
        
        Args:
            result: 天气查询结果
            
        Returns:
            str: 格式化后的自然语言
        """
        if isinstance(result, dict):
            city = result.get("city", "")
            date = result.get("date", "")
            weather = result.get("weather", "")
            temp = result.get("temp", "")
            humidity = result.get("humidity", "")
            wind = result.get("wind", "")
            
            return f"{city}{date}天气{weather}，气温{temp}℃，湿度{humidity}%，{wind}。"
        else:
            return str(result)
    
    def _format_search_result(self, result: Dict[str, Any]) -> str:
        """格式化搜索结果
        
        Args:
            result: 搜索结果
            
        Returns:
            str: 格式化后的自然语言
        """
        if isinstance(result, dict):
            query = result.get("query", "")
            results = result.get("results", [])
            
            if not results:
                return f"未找到关于'{query}'的搜索结果。"
            
            formatted_results = []
            for i, item in enumerate(results[:3], 1):
                title = item.get("title", "")
                url = item.get("url", "")
                snippet = item.get("snippet", "")
                formatted_results.append(f"{i}. {title} - {snippet} (链接: {url})")
            
            return f"关于'{query}'的搜索结果：\n" + "\n".join(formatted_results)
        else:
            return str(result)
    
    def _format_python_result(self, result: Dict[str, Any]) -> str:
        """格式化Python代码执行结果
        
        Args:
            result: Python代码执行结果
            
        Returns:
            str: 格式化后的自然语言
        """
        if isinstance(result, dict):
            stdout = result.get("stdout", "")
            stderr = result.get("stderr", "")
            returncode = result.get("returncode", 0)
            
            if returncode == 0:
                if stdout:
                    return f"Python代码执行成功，输出：\n{stdout}"
                else:
                    return "Python代码执行成功，无输出。"
            else:
                if stderr:
                    return f"Python代码执行失败，错误信息：\n{stderr}"
                else:
                    return f"Python代码执行失败，返回码：{returncode}"
        else:
            return str(result)
    
    def _format_shell_result(self, result: Dict[str, Any]) -> str:
        """格式化Shell命令执行结果
        
        Args:
            result: Shell命令执行结果
            
        Returns:
            str: 格式化后的自然语言
        """
        if isinstance(result, dict):
            stdout = result.get("stdout", "")
            stderr = result.get("stderr", "")
            returncode = result.get("returncode", 0)
            
            if returncode == 0:
                if stdout:
                    return f"Shell命令执行成功，输出：\n{stdout}"
                else:
                    return "Shell命令执行成功，无输出。"
            else:
                if stderr:
                    return f"Shell命令执行失败，错误信息：\n{stderr}"
                else:
                    return f"Shell命令执行失败，返回码：{returncode}"
        else:
            return str(result)
    
    def _format_generic_result(self, result: Any) -> str:
        """格式化通用结果
        
        Args:
            result: 通用结果
            
        Returns:
            str: 格式化后的自然语言
        """
        if isinstance(result, dict):
            # 递归格式化字典
            formatted_items = []
            for key, value in result.items():
                if isinstance(value, (dict, list)):
                    formatted_value = self._format_generic_result(value)
                else:
                    formatted_value = str(value)
                formatted_items.append(f"{key}: {formatted_value}")
            return "\n".join(formatted_items)
        elif isinstance(result, list):
            # 格式化列表
            formatted_items = []
            for i, item in enumerate(result, 1):
                if isinstance(item, (dict, list)):
                    formatted_item = self._format_generic_result(item)
                else:
                    formatted_item = str(item)
                formatted_items.append(f"{i}. {formatted_item}")
            return "\n".join(formatted_items)
        else:
            # 直接转换为字符串
            return str(result)
    
    def truncate_result(self, text: str, max_length: int = 1000) -> str:
        """截断超长结果
        
        Args:
            text: 文本
            max_length: 最大长度
            
        Returns:
            str: 截断后的文本
        """
        if len(text) > max_length:
            return text[:max_length] + "...（结果已截断）"
        return text
    
    def summarize_result(self, text: str) -> str:
        """摘要结果
        
        Args:
            text: 文本
            
        Returns:
            str: 摘要后的文本
        """
        # 简单摘要逻辑，实际项目中可以使用更复杂的摘要算法
        sentences = text.split("。")
        if len(sentences) > 3:
            return "。".join(sentences[:3]) + "。...（结果已摘要）"
        return text


# 全局结果格式化器实例
result_formatter = ResultFormatter()