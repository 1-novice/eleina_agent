#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试RAG测评器功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from evolution.rag_evaluator import rag_evaluator

# 模拟检索结果
def simulate_retrieval(query):
    """模拟检索结果"""
    retrieval_start = time.time()
    
    # 模拟不同质量的文档
    docs = []
    
    if "师傅" in query or "老师" in query:
        docs = [
            {
                "id": "doc1",
                "text": "芙兰是伊蕾娜的师傅，她外表年轻，性格开朗，教会了伊蕾娜魔女的基本素养与独立精神。师徒关系轻松，如同朋友一般。",
                "score": 0.95,
                "retrieval_type": "hybrid"
            },
            {
                "id": "doc2",
                "text": "芙兰只教导了伊蕾娜三个月便让她出师，并赠予她魔女斗篷与帽子。出师后，伊蕾娜正式开始独自环游世界的旅程。",
                "score": 0.88,
                "retrieval_type": "vector"
            },
            {
                "id": "doc3",
                "text": "伊蕾娜的母亲曾经也是魔女，温柔善良，希望伊蕾娜能够过上平静安稳的生活。",
                "score": 0.45,
                "retrieval_type": "keyword"
            }
        ]
    else:
        docs = [
            {
                "id": "doc1",
                "text": "伊蕾娜是《魔女之旅》的主角，被称为灰之魔女。她是一位旅行者，游历于各个国家之间。",
                "score": 0.92,
                "retrieval_type": "hybrid"
            },
            {
                "id": "doc2",
                "text": "伊蕾娜性格温柔优雅，有点小自恋，喜欢被夸奖。她重视自由，不受国家、规则和身份的束缚。",
                "score": 0.85,
                "retrieval_type": "vector"
            },
            {
                "id": "doc3",
                "text": "伊蕾娜擅长多种魔法，包括攻击魔法、防御魔法、飞行魔法和日常魔法等。",
                "score": 0.78,
                "retrieval_type": "keyword"
            }
        ]
    
    retrieval_time = time.time() - retrieval_start
    rerank_time = 0.05  # 模拟重排时间
    
    return docs, retrieval_time, rerank_time

# 测试查询
queries = [
    "你的师傅是谁",
    "芙兰是谁",
    "伊蕾娜的性格特点",
    "魔女之旅的主角",
    "伊蕾娜擅长什么魔法"
]

print("=== 测试RAG测评器 ===")
print(f"测试查询数量: {len(queries)}\n")

# 执行测评
for i, query in enumerate(queries):
    print(f"查询 {i+1}: '{query}'")
    
    # 模拟检索
    docs, retrieval_time, rerank_time = simulate_retrieval(query)
    
    # 评估检索
    result = rag_evaluator.evaluate_retrieval(query, docs, retrieval_time, rerank_time)
    
    # 打印评估结果
    print(f"  检索耗时: {result['retrieval_time_ms']:.2f} ms")
    print(f"  重排耗时: {result['rerank_time_ms']:.2f} ms")
    print(f"  文档质量: {result['avg_document_quality']:.4f}")
    print(f"  相关性: {result['relevance_score']:.4f}")
    print(f"  多样性: {result['diversity_score']:.4f}")
    print(f"  综合评分: {result['overall_score']:.4f}")
    print()

# 打印测评报告
rag_evaluator.print_report()

# 保存报告
report_path = rag_evaluator.save_report()
print(f"\n测评报告已保存: {report_path}")

print("\n=== 测试完成 ===")
