"""诊断嵌入过程中的问题"""
import sys
import os
import glob
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def diagnose():
    print("=" * 60)
    print("医疗RAG嵌入诊断")
    print("=" * 60)
    
    # 1. 检查Milvus连接和数据
    print("\n【1】Milvus状态检查")
    try:
        from src.rag.medical_vector_store import medical_vector_store
        departments = ['儿科', '妇产科', '男科', '内科', '外科', '肿瘤科']
        
        total_docs = 0
        for dept in departments:
            count = medical_vector_store.get_size(dept)
            total_docs += count
            print(f"  {dept}: {count} 条")
        
        print(f"  总计: {total_docs} 条")
        
        if total_docs == 0:
            print("  ⚠️ Milvus中没有数据")
        else:
            print("  ✓ Milvus中有数据")
            
    except Exception as e:
        print(f"  ✗ Milvus连接失败: {e}")
        return
    
    # 2. 检查向量化缓存
    print("\n【2】向量化缓存检查")
    cache_file = "data/text2vec_embedding_cache.json"
    if os.path.exists(cache_file):
        import json
        file_size = os.path.getsize(cache_file) / (1024 * 1024)
        with open(cache_file, 'r', encoding='utf-8') as f:
            try:
                cache = json.load(f)
                print(f"  缓存文件大小: {file_size:.2f} MB")
                print(f"  缓存条目数: {len(cache)}")
            except:
                print(f"  ⚠️ 缓存文件损坏或正在写入")
    else:
        print("  ⚠️ 缓存文件不存在")
    
    # 3. 检查输入CSV文件
    print("\n【3】输入文件检查")
    input_dir = "D:/medicaldata/Chinese-medical-dialogue-data-master/Data"
    if os.path.exists(input_dir):
        csv_files = glob.glob(os.path.join(input_dir, '*.csv'))
        print(f"  找到CSV文件: {len(csv_files)} 个")
        
        for csv_file in csv_files[:3]:  # 只显示前3个
            file_size = os.path.getsize(csv_file) / (1024 * 1024)
            print(f"    - {os.path.basename(csv_file)}: {file_size:.2f} MB")
        
        if len(csv_files) > 3:
            print(f"    ... 还有 {len(csv_files) - 3} 个文件")
    else:
        print(f"  ⚠️ 输入目录不存在: {input_dir}")
    
    # 4. 检查检查点文件
    print("\n【4】检查点文件检查")
    checkpoint_file = "data/embedding_checkpoint.txt"
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            processed_files = f.read().splitlines()
        print(f"  已处理文件数: {len(processed_files)}")
        for f in processed_files[:3]:
            print(f"    - {f}")
        if len(processed_files) > 3:
            print(f"    ... 还有 {len(processed_files) - 3} 个文件")
    else:
        print("  ⚠️ 检查点文件不存在")
    
    # 5. 检查text2vec模型
    print("\n【5】模型检查")
    try:
        from src.rag.text2vec_embedding import text2vec_embedding
        print(f"  ✓ 模型已加载")
        print(f"  向量维度: {text2vec_embedding.get_embedding_dim()}")
    except Exception as e:
        print(f"  ✗ 模型加载失败: {e}")
    
    # 6. 检查系统资源
    print("\n【6】系统资源检查")
    try:
        import psutil
        memory = psutil.virtual_memory()
        print(f"  总内存: {memory.total / (1024**3):.1f} GB")
        print(f"  可用内存: {memory.available / (1024**3):.1f} GB")
        print(f"  内存使用率: {memory.percent}%")
        
        disk = psutil.disk_usage('.')
        print(f"  磁盘可用: {disk.free / (1024**3):.1f} GB")
    except:
        print("  ⚠️ 无法检查系统资源（需要安装psutil）")
    
    print("\n" + "=" * 60)
    print("诊断完成！")
    print("=" * 60)
    
    # 给出建议
    if total_docs == 0:
        print("\n💡 建议：")
        print("  1. 检查Milvus服务是否正常运行")
        print("  2. 检查输入目录路径是否正确")
        print("  3. 尝试使用 --resume 参数重新运行")
        print("  4. 如果还是不行，尝试清空缓存后重新运行")

if __name__ == "__main__":
    diagnose()