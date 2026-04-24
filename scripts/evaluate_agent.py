"""Agent 能力评估脚本"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import json
import time
from src.agent.model_engine import model_engine
from src.tools.tool_executor import ToolExecutor
from src.rag.retriever import Retriever


class AgentEvaluator:
    def __init__(self):
        self.tool_executor = ToolExecutor()
        self.retriever = Retriever()
        self.total_tokens = 0
        self.dialog_count = 0
    
    def evaluate_intent_recognition(self):
        """评估意图识别准确率"""
        print("=== 评估意图识别准确率 ===")
        
        test_cases = [
            {"input": "北京今天天气怎么样？", "expected_intent": "weather", "description": "天气查询"},
            {"input": "帮我生成一张可爱猫咪的图片", "expected_intent": "image", "description": "图片生成"},
            {"input": "伊雷娜是谁？", "expected_intent": "rag", "description": "知识问答"},
            {"input": "你好，我叫小明", "expected_intent": "chat", "description": "日常对话"},
            {"input": "明天上海气温多少度？", "expected_intent": "weather", "description": "天气查询"},
            {"input": "帮我画一幅风景图", "expected_intent": "image", "description": "图片生成"},
            {"input": "魔女之旅的故事背景是什么？", "expected_intent": "rag", "description": "知识问答"},
            {"input": "今天心情不错", "expected_intent": "chat", "description": "日常对话"},
            {"input": "广州的天气", "expected_intent": "weather", "description": "天气查询"},
            {"input": "创作一张动漫角色图片", "expected_intent": "image", "description": "图片生成"},
        ]
        
        correct = 0
        total = len(test_cases)
        
        for case in test_cases:
            intent = self._detect_intent(case["input"])
            is_correct = intent == case["expected_intent"]
            correct += 1 if is_correct else 0
            
            status = "✅" if is_correct else "❌"
            print(f"{status} {case['description']}: '{case['input']}' -> 识别为: {intent}, 期望: {case['expected_intent']}")
        
        accuracy = (correct / total) * 100
        print(f"\n意图识别准确率: {accuracy:.1f}% ({correct}/{total})\n")
        return accuracy
    
    def _detect_intent(self, user_input):
        """简单的意图识别"""
        if any(keyword in user_input for keyword in ["天气", "气温", "温度"]):
            return "weather"
        elif any(keyword in user_input for keyword in ["生成图片", "画一幅", "画一张", "帮我画", "创作"]):
            return "image"
        elif any(keyword in user_input for keyword in ["是谁", "什么", "故事", "背景", "角色"]):
            return "rag"
        else:
            return "chat"
    
    def evaluate_tool_call(self):
        """评估工具调用成功率"""
        print("=== 评估工具调用成功率 ===")
        
        test_cases = [
            {"tool": "generate_image", "params": {"prompt": "一只可爱的猫咪"}, "description": "图片生成"},
            {"tool": "generate_image", "params": {"prompt": "风景油画"}, "description": "图片生成"},
        ]
        
        success = 0
        total = len(test_cases)
        
        for case in test_cases:
            try:
                result = self.tool_executor.execute_tool(case["tool"], case["params"])
                result_data = result.get("result", result)
                if result_data.get("status") == "success":
                    success += 1
                    print(f"✅ {case['description']}: 成功")
                else:
                    print(f"❌ {case['description']}: 失败 - {result_data.get('message', '未知错误')}")
            except Exception as e:
                print(f"❌ {case['description']}: 异常 - {e}")
        
        success_rate = (success / total) * 100 if total > 0 else 0
        print(f"\n工具调用成功率: {success_rate:.1f}% ({success}/{total})\n")
        return success_rate
    
    def evaluate_rag_recall(self):
        """评估RAG召回率"""
        print("=== 评估RAG召回率 ===")
        
        test_cases = [
            {"query": "伊雷娜", "expected_keywords": ["伊雷娜", "魔女", "旅行"]},
            {"query": "魔女之旅", "expected_keywords": ["魔女", "旅行", "故事"]},
            {"query": "魔法", "expected_keywords": ["魔法", "能力"]},
        ]
        
        recall_count = 0
        total = len(test_cases)
        
        for case in test_cases:
            try:
                docs = self.retriever.retrieve(case["query"], top_k=3)
                content = " ".join([doc.page_content for doc in docs]) if docs else ""
                
                matched_keywords = sum(1 for kw in case["expected_keywords"] if kw in content)
                has_recall = matched_keywords >= len(case["expected_keywords"]) * 0.5
                
                if has_recall:
                    recall_count += 1
                    print(f"✅ 查询 '{case['query']}': 召回成功")
                else:
                    print(f"❌ 查询 '{case['query']}': 召回失败")
                    
            except Exception as e:
                print(f"❌ 查询 '{case['query']}': 异常 - {e}")
        
        recall_rate = (recall_count / total) * 100 if total > 0 else 0
        print(f"\nRAG召回率: {recall_rate:.1f}% ({recall_count}/{total})\n")
        return recall_rate
    
    def evaluate_hallucination(self):
        """评估幻觉检测准确率"""
        print("=== 评估幻觉检测 ===")
        
        test_cases = [
            {"question": "1+1等于多少？", "expected_answer": "2", "description": "简单数学"},
            {"question": "中国的首都是哪里？", "expected_answer": "北京", "description": "常识问题"},
        ]
        
        total = len(test_cases)
        if total == 0:
            print("⚠️ 未配置测试用例，跳过幻觉检测评估\n")
            return 0
        
        # 由于幻觉检测需要人工判断，这里只输出结果供人工评估
        print("以下是模型回答，请人工判断是否存在幻觉：")
        for case in test_cases:
            request = {
                "model": model_engine.current_model,
                "messages": [{"role": "user", "content": case["question"]}],
                "stream": False,
                "add_system_prompt": False
            }
            
            try:
                response = model_engine.generate(request)
                answer = response.get("content", "")
                print(f"\n问题: {case['question']}")
                print(f"回答: {answer}")
                print(f"期望: {case['expected_answer']}")
                print(f"是否正确？(请人工判断)")
            except Exception as e:
                print(f"❌ {case['description']}: 调用失败 - {e}")
        
        print("\n幻觉检测需人工评估，请根据上述输出判断准确率\n")
        return 0  # 人工评估
    
    def evaluate_token_consumption(self):
        """评估单对话平均Token消耗"""
        print("=== 评估Token消耗 ===")
        
        test_messages = [
            "你好，介绍一下你自己",
            "什么是人工智能？",
            "今天天气怎么样？",
            "帮我生成一张图片",
        ]
        
        total_tokens = 0
        total_requests = len(test_messages)
        
        for msg in test_messages:
            request = {
                "model": model_engine.current_model,
                "messages": [{"role": "user", "content": msg}],
                "stream": False,
                "add_system_prompt": True
            }
            
            try:
                response = model_engine.generate(request)
                usage = response.get("usage", {})
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)
                tokens = prompt_tokens + completion_tokens
                total_tokens += tokens
                
                print(f"问题: '{msg[:30]}...' -> Token消耗: {tokens} (输入:{prompt_tokens}, 输出:{completion_tokens})")
            except Exception as e:
                print(f"❌ 调用失败: {e}")
        
        avg_tokens = total_tokens / total_requests if total_requests > 0 else 0
        print(f"\n单对话平均Token消耗: {avg_tokens:.0f} tokens\n")
        return avg_tokens
    
    def run_full_evaluation(self):
        """运行完整评估"""
        print("=" * 60)
        print("          Agent 能力评估报告")
        print("=" * 60)
        print(f"评估时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"当前模型: {model_engine.current_model}")
        print("-" * 60)
        
        results = {
            "intent_accuracy": self.evaluate_intent_recognition(),
            "tool_success_rate": self.evaluate_tool_call(),
            "rag_recall_rate": self.evaluate_rag_recall(),
            "hallucination_accuracy": self.evaluate_hallucination(),
            "avg_tokens": self.evaluate_token_consumption(),
        }
        
        print("=" * 60)
        print("          评估结果汇总")
        print("=" * 60)
        print(f"意图识别准确率: {results['intent_accuracy']:.1f}%")
        print(f"工具调用成功率: {results['tool_success_rate']:.1f}%")
        print(f"RAG召回率: {results['rag_recall_rate']:.1f}%")
        print(f"幻觉检测准确率: 需要人工评估")
        print(f"单对话平均Token消耗: {results['avg_tokens']:.0f} tokens")
        print("=" * 60)
        
        # 保存评估结果
        report = {
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "model": model_engine.current_model,
            "metrics": results
        }
        
        with open("evaluation_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print("\n评估报告已保存到: evaluation_report.json")
        return results


if __name__ == "__main__":
    evaluator = AgentEvaluator()
    evaluator.run_full_evaluation()
