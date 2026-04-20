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
            elif tool_name == "generate_image":
                result = self._execute_generate_image(params)
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
    
    def _execute_generate_image(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行图片生成工具 - 使用 wan2.7-image 模型（官方SDK调用方式）"""
        import os
        import time
        
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            return {
                "status": "error",
                "message": "未配置DASHSCOPE_API_KEY环境变量",
                "prompt": params.get("prompt", ""),
                "size": params.get("size", "1024*1024"),
                "n": params.get("n", 1)
            }
        
        try:
            import dashscope
            from dashscope.aigc.image_generation import ImageGeneration
            from dashscope.api_entities.dashscope_response import Message
        except ImportError as e:
            return {
                "status": "error",
                "message": f"缺少依赖，请安装: pip install dashscope",
                "prompt": params.get("prompt", ""),
                "size": params.get("size", "1024*1024"),
                "n": params.get("n", 1),
                "error_detail": str(e)
            }
        
        dashscope.base_http_api_url = 'https://dashscope.aliyuncs.com/api/v1'
        
        prompt = params.get("prompt", "")
        size = params.get("size", "1024*1024")
        n = int(params.get("n", 1))
        
        if not prompt:
            return {
                "status": "error",
                "message": "图片描述(prompt)不能为空",
                "prompt": prompt,
                "size": size,
                "n": n
            }
        
        if 'x' in size:
            size = size.replace('x', '*')
        
        start_time = time.time()
        
        try:
            print(f"[图片生成工具] 调用 wan2.7-image API")
            print(f"[图片生成工具] 参数: prompt={prompt[:50]}..., size={size}, n={n}")
            
            message = Message(
                role="user",
                content=[
                    {
                        "text": prompt
                    }
                ]
            )
            
            rsp = ImageGeneration.call(
                model='wan2.7-image',
                api_key=api_key,
                messages=[message],
                n=n,
                size=size
            )
            
            elapsed_time = time.time() - start_time
            print(f"[图片生成工具] 调用完成，耗时: {elapsed_time:.2f}秒")
            print(f"[图片生成工具] 响应: {rsp}")
            
            if rsp.status_code == 200:
                output = rsp.output
                if isinstance(output, dict) and 'choices' in output and output['choices']:
                    choice = output['choices'][0]
                    if isinstance(choice, dict) and 'message' in choice and 'content' in choice['message']:
                        content = choice['message']['content']
                        urls = []
                        for item in content:
                            if isinstance(item, dict) and 'image' in item and item['image']:
                                urls.append(item['image'])
                        if urls:
                            result = {
                                "status": "success",
                                "url": urls[0],
                                "urls": urls,
                                "prompt": prompt,
                                "size": size,
                                "n": n,
                                "message": f"成功生成{n}张图片，图片URL: {urls[0]}",
                                "elapsed_time": round(elapsed_time, 2),
                                "detailed_info": f"图片生成成功！\nURL: {urls[0]}\n描述: {prompt}\n尺寸: {size}\n数量: {n}"
                            }
                            print(f"[图片生成工具] 成功: {urls[0]}")
                            return result
                elif hasattr(output, 'choices') and output.choices:
                    choice = output.choices[0]
                    if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                        content = choice.message.content
                        urls = []
                        for item in content:
                            if hasattr(item, 'image') and item.image:
                                urls.append(item.image)
                        if urls:
                            result = {
                                "status": "success",
                                "url": urls[0],
                                "urls": urls,
                                "prompt": prompt,
                                "size": size,
                                "n": n,
                                "message": f"成功生成{n}张图片，图片URL: {urls[0]}",
                                "elapsed_time": round(elapsed_time, 2),
                                "detailed_info": f"图片生成成功！\nURL: {urls[0]}\n描述: {prompt}\n尺寸: {size}\n数量: {n}"
                            }
                            print(f"[图片生成工具] 成功: {urls[0]}")
                            return result
            
            error_msg = rsp.message if hasattr(rsp, 'message') and rsp.message else "图片生成失败"
            print(f"[图片生成工具] 失败: {error_msg}")
            return {
                "status": "error",
                "message": error_msg,
                "prompt": prompt,
                "size": size,
                "n": n,
                "elapsed_time": round(elapsed_time, 2),
                "error_detail": str(rsp)
            }
                
        except Exception as e:
            elapsed_time = time.time() - start_time
            print(f"[图片生成工具] 异常: {str(e)}")
            return {
                "status": "error",
                "message": f"图片生成异常: {str(e)}",
                "prompt": prompt,
                "size": size,
                "n": n,
                "elapsed_time": round(elapsed_time, 2),
                "error_detail": str(e)
            }
    
    def _validate_size(self, size: str) -> bool:
        """验证图片尺寸格式
        
        Args:
            size: 图片尺寸字符串
            
        Returns:
            bool: 是否有效
        """
        valid_sizes = {"512*512", "1024*1024", "1024*1536", "1536*1024"}
        return size in valid_sizes


# 全局工具执行器实例
tool_executor = ToolExecutor()