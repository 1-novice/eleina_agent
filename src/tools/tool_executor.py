from typing import Dict, List, Optional, Any
import subprocess
import time
import asyncio

# 尝试导入httpx
try:
    import httpx
    has_httpx = True
except ImportError:
    has_httpx = False
    print("警告: 无法导入httpx模块，将使用urllib作为备选")


class ToolExecutor:
    def __init__(self):
        self.execution_history = {}
    
    def execute_tool(self, tool_name: str, params: Dict[str, Any], timeout: int = 30) -> Dict[str, Any]:
        """执行工具
        
        Args:
            tool_name: 工具名称
            params: 参数字典
            timeout: 超时时间（秒）
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        start_time = time.time()
        result = {}
        
        try:
            # 根据工具名称选择执行方式
            if tool_name == "get_weather":
                result = self._execute_get_weather(params)
            elif tool_name == "search_web":
                result = self._execute_search_web(params)
            elif tool_name == "run_python":
                result = self._execute_run_python(params, timeout)
            elif tool_name == "run_shell":
                result = self._execute_run_shell(params, timeout)
            else:
                # 执行自定义工具
                result = self._execute_custom_tool(tool_name, params)
            
            # 记录执行历史
            self.execution_history[tool_name] = {
                "params": params,
                "result": result,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "execution_time": time.time() - start_time
            }
            
            return {
                "tool": tool_name,
                "params": params,
                "result": result,
                "status": "success"
            }
        except Exception as e:
            # 记录执行历史
            self.execution_history[tool_name] = {
                "params": params,
                "error": str(e),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "execution_time": time.time() - start_time
            }
            
            return {
                "tool": tool_name,
                "params": params,
                "result": f"执行失败: {str(e)}",
                "status": "error"
            }
    
    async def execute_tool_async(self, tool_name: str, params: Dict[str, Any], timeout: int = 30) -> Dict[str, Any]:
        """异步执行工具
        
        Args:
            tool_name: 工具名称
            params: 参数字典
            timeout: 超时时间（秒）
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.execute_tool,
            tool_name,
            params,
            timeout
        )
    
    def _execute_get_weather(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行天气查询工具
        
        Args:
            params: 参数字典
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        import urllib.request
        import json
        
        city = params.get("city", "北京")
        date = params.get("date", "今天")
        
        try:
            # 城市坐标映射
            city_coordinates = {
                "北京": {"lat": 39.9042, "lon": 116.4074},
                "上海": {"lat": 31.2304, "lon": 121.4737},
                "广州": {"lat": 23.1291, "lon": 113.2644},
                "深圳": {"lat": 22.5431, "lon": 114.0579},
                "杭州": {"lat": 30.2741, "lon": 120.1551},
                "成都": {"lat": 30.5728, "lon": 104.0668},
                "重庆": {"lat": 29.4316, "lon": 106.9123},
                "武汉": {"lat": 30.5928, "lon": 114.3055},
                "西安": {"lat": 34.3416, "lon": 108.9398},
                "南京": {"lat": 32.0603, "lon": 118.7969}
            }
            
            # 获取城市坐标
            if city in city_coordinates:
                coords = city_coordinates[city]
            else:
                # 默认使用北京坐标
                coords = city_coordinates["北京"]
                city = "北京"
            
            # 构建API请求URL
            url = f"https://api.open-meteo.com/v1/forecast?latitude={coords['lat']}&longitude={coords['lon']}&current_weather=true&temperature_unit=celsius"
            
            # 发送请求
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read().decode())
            
            # 提取天气数据
            current_weather = data.get("current_weather", {})
            weather_data = {
                "city": city,
                "date": date,
                "weather": self._get_weather_description(current_weather.get("weathercode", 0)),
                "temperature": f"{current_weather.get('temperature', 0)}°C",
                "temperature_value": current_weather.get("temperature", 0),
                "humidity": "N/A",  # Open-Meteo免费版不提供湿度数据
                "wind_speed": f"{current_weather.get('windspeed', 0)} km/h",
                "wind_speed_value": current_weather.get("windspeed", 0),
                "wind_direction": current_weather.get("winddirection", 0),
                "last_updated": current_weather.get("time", "N/A"),
                "detailed_info": f"城市: {city}, 日期: {date}, 天气: {self._get_weather_description(current_weather.get('weathercode', 0))}, 温度: {current_weather.get('temperature', 0)}°C, 风速: {current_weather.get('windspeed', 0)} km/h, 风向: {current_weather.get('winddirection', 0)}度, 最后更新: {current_weather.get('time', 'N/A')}"
            }
            
            return weather_data
        except Exception as e:
            # 出错时返回错误信息
            print(f"获取天气数据失败: {e}")
            return {
                "city": city,
                "date": date,
                "weather": "未知",
                "temperature": "N/A",
                "temperature_value": 0,
                "humidity": "N/A",
                "wind_speed": "N/A",
                "wind_speed_value": 0,
                "wind_direction": 0,
                "last_updated": "N/A",
                "detailed_info": f"城市: {city}, 日期: {date}, 天气: 未知, 温度: N/A, 风速: N/A, 风向: N/A, 最后更新: N/A",
                "error": "抱歉查询天气失败"
            }
    
    def _get_weather_description(self, weather_code: int) -> str:
        """根据天气代码获取天气描述
        
        Args:
            weather_code: 天气代码
            
        Returns:
            str: 天气描述
        """
        weather_codes = {
            0: "晴朗",
            1: "大部分晴朗",
            2: "部分多云",
            3: "多云",
            45: "雾",
            48: "霾",
            51: "小雨",
            53: "中雨",
            55: "大雨",
            56: "冻雨",
            57: "冻雨",
            61: "小雨",
            63: "中雨",
            65: "大雨",
            66: "冻雨",
            67: "冻雨",
            71: "小雪",
            73: "中雪",
            75: "大雪",
            77: "雨夹雪",
            80: "阵雨",
            81: "中阵雨",
            82: "大阵雨",
            85: "阵雪",
            86: "大阵雪",
            95: "雷暴",
            96: "雷暴",
            99: "雷暴"
        }
        return weather_codes.get(weather_code, "未知")
    
    def _execute_search_web(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行网页搜索工具
        
        Args:
            params: 参数字典
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        query = params.get("query", "")
        
        # 模拟搜索结果
        search_results = {
            "query": query,
            "results": [
                {
                    "title": "搜索结果1",
                    "url": "https://example.com/1",
                    "snippet": "这是搜索结果1的摘要"
                },
                {
                    "title": "搜索结果2",
                    "url": "https://example.com/2",
                    "snippet": "这是搜索结果2的摘要"
                }
            ]
        }
        
        return search_results
    
    def _execute_run_python(self, params: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        """执行Python代码工具
        
        Args:
            params: 参数字典
            timeout: 超时时间（秒）
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        code = params.get("code", "")
        
        # 执行Python代码
        try:
            result = subprocess.run(
                ["python", "-c", code],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": f"执行超时（{timeout}秒）",
                "returncode": 1
            }
    
    def _execute_run_shell(self, params: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        """执行Shell命令工具
        
        Args:
            params: 参数字典
            timeout: 超时时间（秒）
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        command = params.get("command", "")
        
        # 执行Shell命令
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": f"执行超时（{timeout}秒）",
                "returncode": 1
            }
    
    def _execute_custom_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行自定义工具
        
        Args:
            tool_name: 工具名称
            params: 参数字典
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        # 这里可以扩展自定义工具的执行逻辑
        return {
            "message": f"执行自定义工具 {tool_name}",
            "params": params
        }


# 全局工具执行器实例
tool_executor = ToolExecutor()