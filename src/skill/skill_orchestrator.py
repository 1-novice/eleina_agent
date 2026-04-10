from typing import Dict, List, Optional, Any


class SkillOrchestrator:
    def __init__(self):
        self.execution_history = {}
    
    def orchestrate(self, skill_id: str, slots: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """执行Skill编排
        
        Args:
            skill_id: Skill ID
            slots: 槽位信息
            context: 上下文信息
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        user_id = context.get("user_id", "unknown")
        session_id = context.get("session_id", "default")
        
        # 初始化执行历史
        if session_id not in self.execution_history:
            self.execution_history[session_id] = {
                "skill_id": skill_id,
                "steps": [],
                "current_step": 0,
                "status": "running",
                "slots": slots
            }
        
        # 根据Skill ID执行不同的编排逻辑
        if skill_id == "weather_skill":
            return self._orchestrate_weather_skill(slots, context)
        elif skill_id == "search_skill":
            return self._orchestrate_search_skill(slots, context)
        else:
            return self._orchestrate_generic_skill(skill_id, slots, context)
    
    def _orchestrate_weather_skill(self, slots: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """编排天气查询Skill
        
        Args:
            slots: 槽位信息
            context: 上下文信息
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        session_id = context.get("session_id", "default")
        
        # 检查槽位
        city = slots.get("city")
        date = slots.get("date", "今天")
        
        if not city:
            return {
                "status": "needs_clarification",
                "questions": ["请问你想查询哪个城市的天气？"]
            }
        
        # 执行步骤
        steps = [
            {
                "step": "验证参数",
                "description": "验证城市和日期参数"
            },
            {
                "step": "调用天气工具",
                "description": "调用天气查询工具获取天气信息"
            },
            {
                "step": "格式化结果",
                "description": "格式化天气查询结果"
            }
        ]
        
        # 更新执行历史
        if session_id in self.execution_history:
            self.execution_history[session_id]["steps"] = steps
        
        # 执行步骤
        for i, step in enumerate(steps):
            # 更新当前步骤
            if session_id in self.execution_history:
                self.execution_history[session_id]["current_step"] = i
            
            # 模拟执行步骤
            print(f"执行步骤 {i+1}: {step['step']}")
        
        # 构建工具调用
        tool_call = {
            "tool_choice": "get_weather",
            "tool_params": {
                "city": city,
                "date": date
            }
        }
        
        return {
            "status": "needs_tool",
            "tool_call": tool_call
        }
    
    def _orchestrate_search_skill(self, slots: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """编排搜索Skill
        
        Args:
            slots: 槽位信息
            context: 上下文信息
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        session_id = context.get("session_id", "default")
        
        # 检查槽位
        query = slots.get("query")
        
        if not query:
            return {
                "status": "needs_clarification",
                "questions": ["请问你想搜索什么内容？"]
            }
        
        # 执行步骤
        steps = [
            {
                "step": "验证参数",
                "description": "验证搜索查询参数"
            },
            {
                "step": "调用搜索工具",
                "description": "调用网页搜索工具获取搜索结果"
            },
            {
                "step": "格式化结果",
                "description": "格式化搜索结果"
            }
        ]
        
        # 更新执行历史
        if session_id in self.execution_history:
            self.execution_history[session_id]["steps"] = steps
        
        # 执行步骤
        for i, step in enumerate(steps):
            # 更新当前步骤
            if session_id in self.execution_history:
                self.execution_history[session_id]["current_step"] = i
            
            # 模拟执行步骤
            print(f"执行步骤 {i+1}: {step['step']}")
        
        # 构建工具调用
        tool_call = {
            "tool_choice": "search_web",
            "tool_params": {
                "query": query
            }
        }
        
        return {
            "status": "needs_tool",
            "tool_call": tool_call
        }
    
    def _orchestrate_generic_skill(self, skill_id: str, slots: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """编排通用Skill
        
        Args:
            skill_id: Skill ID
            slots: 槽位信息
            context: 上下文信息
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        return {
            "status": "completed",
            "answer": f"执行Skill {skill_id}，槽位信息: {slots}"
        }
    
    def resume_execution(self, session_id: str, tool_result: Dict[str, Any]) -> Dict[str, Any]:
        """恢复执行
        
        Args:
            session_id: 会话ID
            tool_result: 工具执行结果
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        if session_id not in self.execution_history:
            return {
                "status": "error",
                "message": "执行历史不存在"
            }
        
        execution_info = self.execution_history[session_id]
        skill_id = execution_info.get("skill_id")
        
        # 处理工具执行结果
        if tool_result.get("status") == "success":
            # 构建最终结果
            from src.tools.result_formatter import result_formatter
            formatted_result = result_formatter.format_result(tool_result)
            
            # 将结果交给大模型进行语气和话术处理
            from src.agent.model_engine import model_engine
            from src.config.config import settings
            
            # 构建大模型提示词
            prompt = f"请将以下天气查询结果转换为自然、友好的回答，使用动漫角色的语气：\n\n{formatted_result}"
            
            # 调用大模型
            request = {
                "model": settings.model_type,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "stream": False,
                "user_id": "system"
            }
            
            try:
                response = model_engine.generate(request)
                processed_answer = response.get("content", formatted_result)
            except Exception as e:
                print(f"大模型处理失败: {e}")
                processed_answer = formatted_result
            
            # 更新执行历史
            execution_info["status"] = "completed"
            
            return {
                "status": "completed",
                "answer": processed_answer
            }
        else:
            # 工具执行失败
            return {
                "status": "error",
                "message": f"工具执行失败: {tool_result.get('result')}"
            }


# 全局Skill执行编排器实例
skill_orchestrator = SkillOrchestrator()