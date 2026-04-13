"""RAG检索功能测试"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from src.rag.retriever import retriever


class TestRagRetrieval:
    """RAG检索测试类"""
    
    def test_retriever_initialization(self):
        """测试检索器初始化"""
        assert retriever is not None
        assert retriever.total_docs >= 0
        print(f"✓ 检索器初始化成功，文档数: {retriever.total_docs}")
    
    def test_retrieve_basic(self):
        """测试基础检索功能"""
        query = "你的老师是谁"
        results = retriever.retrieve(query, k=3)
        
        assert isinstance(results, list)
        print(f"✓ 检索查询 '{query}' 成功，返回 {len(results)} 条结果")
        
        if results:
            for i, result in enumerate(results):
                print(f"  {i+1}. 得分: {result.get('score', 0.0):.4f}, 文本: {result.get('text', '')[:50]}...")
    
    def test_retrieve_empty_query(self):
        """测试空查询"""
        query = ""
        results = retriever.retrieve(query, k=3)
        assert isinstance(results, list)
        print("✓ 空查询处理成功")
    
    def test_retrieve_with_filters(self):
        """测试带过滤条件的检索"""
        query = "知识"
        filters = {"tags": ["test"]}
        results = retriever.retrieve(query, k=3, filters=filters)
        
        assert isinstance(results, list)
        print(f"✓ 带过滤条件检索成功，返回 {len(results)} 条结果")
    
    def test_retrieve_different_k_values(self):
        """测试不同的k值"""
        query = "测试"
        for k in [1, 3, 5]:
            results = retriever.retrieve(query, k=k)
            assert len(results) <= k
            print(f"✓ k={k} 时返回 {len(results)} 条结果")


if __name__ == "__main__":
    print("=" * 60)
    print("RAG检索功能测试")
    print("=" * 60)
    
    test = TestRagRetrieval()
    
    try:
        test.test_retriever_initialization()
        test.test_retrieve_basic()
        test.test_retrieve_empty_query()
        test.test_retrieve_with_filters()
        test.test_retrieve_different_k_values()
        
        print("\n" + "=" * 60)
        print("✓ 所有测试通过！")
        print("=" * 60)
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()