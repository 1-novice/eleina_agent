#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""追加模式：添加新文件到RAG系统（不清空现有数据）"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rag.doc_parser import doc_parser
from src.rag.text_chunker import text_chunker
from src.rag.embedding_engine import embedding_engine
from src.rag.vector_store import vector_store
from src.rag.retriever import retriever


def find_md_files(directory):
    """查找目录中所有的md文件"""
    md_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.md'):
                md_files.append(os.path.join(root, file))
    return md_files


def process_file(file_path):
    """处理单个文件"""
    print(f"\n处理文件: {file_path}")
    
    # 解析文档
    parse_result = doc_parser.parse_document_by_path(file_path)
    if parse_result.get("status") != "success":
        print(f"  ❌ 解析失败: {parse_result.get('message')}")
        return None
    
    content = parse_result.get("content", "")
    if not content.strip():
        print(f"  ❌ 文档内容为空")
        return None
    
    print(f"  ✓ 文档内容长度: {len(content)}")
    
    # 文本分块
    chunks = text_chunker.chunk_text(content, strategy="semantic")
    print(f"  ✓ 分块数量: {len(chunks)}")
    
    # 向量化
    embeddings = embedding_engine.embed_batch([chunk.get("text", "") for chunk in chunks])
    print(f"  ✓ 向量化结果: {len(embeddings)} 个向量")
    
    return chunks, embeddings


def main():
    # 设置knowledge目录路径
    knowledge_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "rag", "knowledge")
    
    print("=" * 60)
    print("追加模式：添加新文件到RAG系统")
    print("=" * 60)
    print(f"knowledge目录路径: {knowledge_dir}")
    print("注意：此模式不会清空现有数据，仅追加新内容")
    
    # 检查目录是否存在
    if not os.path.exists(knowledge_dir):
        print(f"❌ knowledge目录不存在: {knowledge_dir}")
        return
    
    # 查找所有md文件
    md_files = find_md_files(knowledge_dir)
    print(f"找到 {len(md_files)} 个md文件")
    
    if not md_files:
        print("❌ 没有找到任何md文件")
        return
    
    # 列出找到的文件
    print("\n找到的文件:")
    for i, file in enumerate(md_files, 1):
        print(f"  {i}. {os.path.basename(file)}")
    
    # 确认操作
    confirm = input(f"\n确定要追加这些文件到RAG系统吗？(y/n): ")
    if confirm.lower() != 'y':
        print("操作已取消")
        return
    
    # 获取当前存储的文档数量
    current_count = len(vector_store.get_all())
    print(f"\n当前向量存储中已有 {current_count} 个文档")
    
    # 处理所有文件
    total_chunks = 0
    total_embeddings = 0
    failed_files = []
    
    for file_path in md_files:
        result = process_file(file_path)
        if result:
            chunks, embeddings = result
            
            # 添加到向量存储（追加模式）
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                chunk["vector"] = embedding
                chunk["id"] = f"knowledge_{os.path.basename(file_path)}_{i}"
            
            vector_store.add_batch(chunks)
            total_chunks += len(chunks)
            total_embeddings += len(embeddings)
            print(f"  ✓ 追加成功")
        else:
            failed_files.append(file_path)
    
    # 保存向量存储
    vector_store.save()
    
    # 显示结果
    print("\n" + "=" * 60)
    print("追加完成！")
    print("=" * 60)
    print(f"成功处理文件: {len(md_files) - len(failed_files)} / {len(md_files)}")
    print(f"新增块数: {total_chunks}")
    print(f"新增向量数: {total_embeddings}")
    print(f"总文档数: {len(vector_store.get_all())}")
    
    if failed_files:
        print("\n失败的文件:")
        for file in failed_files:
            print(f"  - {file}")
    
    # 更新检索器的预缓存
    print("\n更新检索器预缓存...")
    retriever._precache()
    print("✓ 预缓存更新完成")
    
    # 测试检索
    print("\n测试检索功能...")
    test_query = "知识"
    results = retriever.retrieve(test_query, k=3)
    print(f"查询 '{test_query}' 检索到 {len(results)} 个文档")
    for i, result in enumerate(results):
        print(f"  {i+1}. 得分: {result.get('score'):.4f}, 文本: {result.get('text')[:50]}...")


if __name__ == "__main__":
    main()
