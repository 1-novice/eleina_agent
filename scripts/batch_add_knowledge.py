import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import glob
import csv
import json
import time
import random
from typing import List, Dict, Any, Set

print("初始化向量化引擎...")
try:
    from src.rag.text2vec_embedding import text2vec_embedding
    print("✓ 向量化引擎初始化成功")
except Exception as e:
    print(f"✗ 向量化引擎初始化失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("初始化向量存储...")
try:
    from src.rag.medical_vector_store import medical_vector_store
    print("✓ 向量存储初始化成功")
except Exception as e:
    print(f"✗ 向量存储初始化失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

PROGRESS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "embedding_progress.json")

DEPARTMENT_QUOTAS = {
    "儿科": 30000,
    "妇产科": 30000,
    "男科": 30000,
    "内科": 30000,
    "外科": 30000,
    "肿瘤科": 30000
}


def load_progress() -> Dict[str, Any]:
    """加载断点续传进度"""
    if not os.path.exists(PROGRESS_FILE):
        return {
            "processed_files": [],
            "processed_chunks": 0,
            "saved_chunks": 0,
            "chunks_by_dept": {},
            "total_chunks": 0
        }
    
    try:
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载进度失败: {e}")
        return {
            "processed_files": [],
            "processed_chunks": 0,
            "saved_chunks": 0,
            "chunks_by_dept": {},
            "total_chunks": 0
        }


def save_progress(processed_files: List[str], processed_chunks: int, saved_chunks: int, 
                  chunks_by_dept: Dict[str, int] = None, total_chunks: int = 0):
    """保存断点续传进度"""
    try:
        os.makedirs(os.path.dirname(PROGRESS_FILE), exist_ok=True)
        progress = {
            "processed_files": processed_files,
            "processed_chunks": processed_chunks,
            "saved_chunks": saved_chunks,
            "chunks_by_dept": chunks_by_dept or {},
            "total_chunks": total_chunks
        }
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(progress, f)
    except Exception as e:
        print(f"保存进度失败: {e}")


def normalize_department(department: str) -> str:
    if not department:
        return "内科"
    
    department_lower = department.lower()
    
    department_keywords = {
        "儿科": ["儿科", "儿童", "小儿", "pediatric"],
        "妇产科": ["妇产科", "妇科", "产科", "妇科疾病", "obstetrics"],
        "男科": ["男科", "男性", "men"],
        "内科": ["内科", "呼吸", "消化", "心脏", "internal"],
        "外科": ["外科", "手术", "surgery"],
        "肿瘤科": ["肿瘤科", "肿瘤", "癌症", "oncology", "癌"]
    }
    
    for std_dept, keywords in department_keywords.items():
        for keyword in keywords:
            if keyword in department_lower:
                return std_dept
    
    return "内科"


def parse_structured_txt(filepath: str) -> List[Dict[str, Any]]:
    documents = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    records = content.split('=' * 80)
    filename = os.path.basename(filepath)
    
    for record in records:
        record = record.strip()
        if not record:
            continue
        
        doc = {
            "content": record,
            "filename": filename,
            "filepath": filepath,
            "department": "内科",
            "source_type": 'document',
            "title": "",
            "question": "",
            "answer": ""
        }
        
        lines = record.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('【科室】'):
                raw_dept = line.replace('【科室】', '').strip()
                doc["department"] = normalize_department(raw_dept)
            elif line.startswith('【标题】'):
                doc["title"] = line.replace('【标题】', '').strip()
            elif line.startswith('【问题】'):
                doc["question"] = line.replace('【问题】', '').strip()
            elif line.startswith('【答案】'):
                doc["answer"] = line.replace('【答案】', '').strip()
        
        if doc["question"] and doc["answer"]:
            doc["source_type"] = 'manual'
        
        documents.append(doc)
    
    print(f"✓ 解析结构化文档: {filename} -> {len(documents)} 条记录")
    return documents


def load_csv_documents(filepath: str) -> List[Dict[str, Any]]:
    documents = []
    filename = os.path.basename(filepath)
    department = infer_department_from_filename(filename)
    
    encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030']
    success = False
    skipped = 0
    
    for encoding in encodings:
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames
                
                if headers is None:
                    continue
                
                question_key = 'question' if 'question' in headers else 'ask'
                
                for row_num, row in enumerate(reader, 1):
                    dept = row.get('department', '').strip() or department
                    title = row.get('title', '').strip()
                    question = row.get(question_key, '').strip()
                    answer = row.get('answer', '').strip()
                    
                    if not _is_valid_medical_record(title, question, answer):
                        skipped += 1
                        continue
                    
                    content = f"【科室】{dept}\n【标题】{title}\n【问题】{question}\n【答案】{answer}"
                    
                    documents.append({
                        "content": content,
                        "filename": filename,
                        "filepath": filepath,
                        "department": dept,
                        "source_type": 'manual',
                        "title": title,
                        "question": question,
                        "answer": answer,
                        "row_num": row_num
                    })
                
                print(f"✓ 加载CSV成功 ({encoding}): {filename} -> {len(documents)} 条记录 (跳过 {skipped} 条无效记录)")
                success = True
                break
                
        except Exception as e:
            print(f"  尝试编码 {encoding} 失败: {str(e)[:30]}")
            continue
    
    if not success:
        print(f"✗ 无法读取CSV文件 {filename}: 所有编码都失败")
    
    return documents


def _is_valid_medical_record(title: str, question: str, answer: str) -> bool:
    if len(title) < 2 or len(question) < 5 or len(answer) < 10:
        return False
    
    medical_keywords = ['治疗', '症状', '诊断', '疾病', '用药', '检查', '医生', '医院', '患者', '病情', '健康']
    text = title + question + answer
    
    has_medical = any(keyword in text for keyword in medical_keywords)
    if not has_medical:
        health_keywords = ['吃', '喝', '注意', '怎么办', '怎么治', '如何', '什么', '为什么']
        has_health = any(keyword in text for keyword in health_keywords)
        return has_health
    
    return True


def infer_department_from_filename(filename: str) -> str:
    filename_lower = filename.lower()
    
    department_keywords = {
        "儿科": ["儿科", "儿童", "小儿", "pediatric"],
        "妇产科": ["妇产科", "妇科", "产科", "妇科疾病", "obstetrics"],
        "男科": ["男科", "男性", "men"],
        "内科": ["内科", "呼吸", "消化", "心脏", "internal"],
        "外科": ["外科", "手术", "surgery"],
        "肿瘤科": ["肿瘤科", "肿瘤", "癌症", "oncology", "癌"]
    }
    
    for department, keywords in department_keywords.items():
        for keyword in keywords:
            if keyword in filename_lower:
                return department
    
    return "内科"


def extract_medical_tags(text: str) -> Dict[str, List[str]]:
    tags = {
        "symptoms": [],
        "treatments": [],
        "diseases": [],
        "examinations": [],
        "body_parts": []
    }
    
    symptom_keywords = [
        "血尿", "尿频", "尿急", "尿痛", "疼痛", "发热", "发烧", 
        "出血", "肿块", "消瘦", "乏力", "恶心", "呕吐", "腹胀",
        "咳嗽", "呼吸困难", "头痛", "头晕", "失眠", "食欲不振"
    ]
    
    treatment_keywords = [
        "手术", "化疗", "放疗", "药物治疗", "中药", "西药", 
        "灌注", "切除", "移植", "介入", "靶向治疗", "免疫治疗"
    ]
    
    disease_keywords = [
        "癌", "肿瘤", "炎症", "感染", "结石", "溃疡", 
        "综合征", "病变", "硬化", "萎缩", "增生"
    ]
    
    examination_keywords = [
        "检查", "化验", "B超", "CT", "MRI", "X光", 
        "活检", "穿刺", "镜检", "扫描", "造影"
    ]
    
    body_part_keywords = [
        "膀胱", "肾", "肝", "肺", "胃", "肠", "心脏", 
        "脑", "骨骼", "血液", "淋巴", "皮肤", "肌肉"
    ]
    
    for keyword in symptom_keywords:
        if keyword in text:
            tags["symptoms"].append(keyword)
    
    for keyword in treatment_keywords:
        if keyword in text:
            tags["treatments"].append(keyword)
    
    for keyword in disease_keywords:
        if keyword in text:
            tags["diseases"].append(keyword)
    
    for keyword in examination_keywords:
        if keyword in text:
            tags["examinations"].append(keyword)
    
    for keyword in body_part_keywords:
        if keyword in text:
            tags["body_parts"].append(keyword)
    
    return tags


MAX_BYTE_LENGTH = 65530


def truncate_to_byte_length(text: str, max_bytes: int = MAX_BYTE_LENGTH) -> str:
    if len(text.encode('utf-8')) <= max_bytes:
        return text
    
    max_chars = max_bytes
    while len(text[:max_chars].encode('utf-8')) > max_bytes:
        max_chars -= 1
    
    return text[:max_chars]


def chunk_documents(documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    chunks = []
    skipped_count = 0
    skipped_details = []
    
    for doc in documents:
        content = doc["content"]
        filename = doc["filename"]
        department = doc.get("department", "内科")
        source_type = doc.get("source_type", "document")
        
        content_byte_length = len(content.encode('utf-8'))
        if content_byte_length > MAX_BYTE_LENGTH:
            skipped_count += 1
            skipped_details.append(f"  - {filename}: {len(content)} 字符 / {content_byte_length} 字节")
            continue
        
        tags = extract_medical_tags(content)
        
        if doc.get('question') and doc.get('answer'):
            chunks.append({
                "content": content,
                "filename": filename,
                "department": department,
                "source_type": source_type,
                "metadata": {
                    "filename": filename,
                    "department": department,
                    "title": doc.get("title", ""),
                    "question": doc.get("question", ""),
                    "answer": doc.get("answer", ""),
                    "symptoms": tags["symptoms"],
                    "treatments": tags["treatments"],
                    "diseases": tags["diseases"],
                    "examinations": tags["examinations"],
                    "body_parts": tags["body_parts"]
                }
            })
        else:
            chunk_size = 500
            chunk_overlap = 50
            
            content_length = len(content)
            if content_length <= chunk_size:
                chunks.append({
                    "content": content,
                    "filename": filename,
                    "department": department,
                    "source_type": source_type,
                    "metadata": {
                        "filename": filename,
                        "department": department,
                        "symptoms": tags["symptoms"],
                        "treatments": tags["treatments"],
                        "diseases": tags["diseases"],
                        "examinations": tags["examinations"],
                        "body_parts": tags["body_parts"]
                    }
                })
            else:
                for i in range(0, content_length, chunk_size - chunk_overlap):
                    chunk = content[i:i+chunk_size]
                    chunk_tags = extract_medical_tags(chunk)
                    chunks.append({
                        "content": chunk,
                        "filename": filename,
                        "department": department,
                        "source_type": source_type,
                        "metadata": {
                            "filename": filename,
                            "department": department,
                            "chunk_index": i // (chunk_size - chunk_overlap),
                            "chunk_size": chunk_size,
                            "symptoms": chunk_tags["symptoms"],
                            "treatments": chunk_tags["treatments"],
                            "diseases": chunk_tags["diseases"],
                            "examinations": chunk_tags["examinations"],
                            "body_parts": chunk_tags["body_parts"]
                        }
                    })
    
    print(f"切分完成，共生成 {len(chunks)} 个文档块")
    if skipped_count > 0:
        print(f"跳过 {skipped_count} 个超长记录:")
        for detail in skipped_details[:10]:
            print(detail)
        if len(skipped_details) > 10:
            print(f"  ... 还有 {len(skipped_details) - 10} 条")
    return chunks


def sample_by_quota(chunks: List[Dict[str, Any]], quotas: Dict[str, int], 
                    existing_counts: Dict[str, int] = None) -> List[Dict[str, Any]]:
    """按科室配额采样，考虑已有数据量"""
    existing_counts = existing_counts or {}
    print(f"\n📊 按科室配额采样 (每科室最多 {quotas['内科']} 条)")
    
    chunks_by_dept = {}
    for chunk in chunks:
        dept = chunk["department"]
        if dept not in chunks_by_dept:
            chunks_by_dept[dept] = []
        chunks_by_dept[dept].append(chunk)
    
    sampled_chunks = []
    remaining_quotas = {}
    
    for dept, dept_chunks in chunks_by_dept.items():
        quota = quotas.get(dept, quotas["内科"])
        existing = existing_counts.get(dept, 0)
        remaining = max(0, quota - existing)
        remaining_quotas[dept] = remaining
        
        if remaining <= 0:
            print(f"  {dept}: 已达配额上限 ({existing}/{quota})，跳过")
            continue
        
        count = len(dept_chunks)
        
        if count <= remaining:
            sampled = dept_chunks
            print(f"  {dept}: {count} 条 (未超剩余配额 {remaining}，全部保留)")
        else:
            sampled = random.sample(dept_chunks, remaining)
            print(f"  {dept}: {count} 条 -> 随机采样 {remaining} 条 (剩余配额)")
        
        sampled_chunks.extend(sampled)
    
    random.shuffle(sampled_chunks)
    print(f"\n✓ 采样完成，共保留 {len(sampled_chunks)} 条记录")
    
    return sampled_chunks, remaining_quotas


def embed_chunks_batch(chunks: List[Dict[str, Any]], start_idx: int, batch_size: int) -> tuple:
    end_idx = min(start_idx + batch_size, len(chunks))
    batch_chunks = chunks[start_idx:end_idx]
    
    cache_hits = 0
    texts_to_embed = []
    indices_to_embed = []
    
    for i, chunk in enumerate(batch_chunks):
        content = chunk["content"]
        
        if len(content.encode('utf-8')) > MAX_BYTE_LENGTH:
            content = truncate_to_byte_length(content)
            chunk["content"] = content
        
        texts_to_embed.append(content)
        indices_to_embed.append(i)
    
    cache_misses = len(batch_chunks)
    
    if cache_misses > 0:
        vectors = text2vec_embedding.embed_batch(texts_to_embed)
        
        for i, idx in enumerate(indices_to_embed):
            vector = vectors[i]
            batch_chunks[idx]["vector"] = vector
    
    return end_idx, cache_hits, cache_misses


def save_chunks_to_milvus(chunks: List[Dict[str, Any]], start_idx: int, end_idx: int):
    batch_chunks = chunks[start_idx:end_idx]
    
    chunks_by_dept = {}
    for chunk in batch_chunks:
        content = chunk["content"]
        content = truncate_to_byte_length(content)
        chunk["content"] = content
        
        dept = chunk.get("department", "内科")
        if dept not in chunks_by_dept:
            chunks_by_dept[dept] = []
        chunks_by_dept[dept].append(chunk)
    
    for dept, dept_chunks in chunks_by_dept.items():
        milvus_chunks = []
        for chunk in dept_chunks:
            milvus_chunks.append({
                "content": chunk["content"],
                "vector": chunk["vector"],
                "metadata": chunk["metadata"],
                "source_type": chunk["source_type"]
            })
        
        medical_vector_store.add_batch(dept, milvus_chunks)


def main():
    parser = argparse.ArgumentParser(description="批量嵌入医疗文档到Milvus向量库（支持科室配额控制和断点续传）")
    parser.add_argument("--doc_dir", type=str, default="d:\\Cursorcode\\eleina_agent\\src\\rag\\knowledge", 
                        help="医疗文档目录路径")
    parser.add_argument("--clear_existing", action="store_true", help="是否清空现有数据")
    parser.add_argument("--batch_size", type=int, default=10000, help="每批处理的文档块数量")
    parser.add_argument("--resume", action="store_true", help="是否从上次中断处继续（断点续传）")
    parser.add_argument("--clear_progress", action="store_true", help="是否清除进度文件重新开始")
    parser.add_argument("--skip_sampling", action="store_true", help="跳过配额采样，处理所有数据")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("批量嵌入医疗文档到Milvus向量库（支持科室配额控制和断点续传）")
    print("=" * 60)
    
    if args.clear_progress:
        if os.path.exists(PROGRESS_FILE):
            os.remove(PROGRESS_FILE)
            print("已清除进度文件")
    
    progress = load_progress() if args.resume else {
        "processed_files": [],
        "processed_chunks": 0,
        "saved_chunks": 0,
        "chunks_by_dept": {},
        "total_chunks": 0
    }
    
    processed_files_set: Set[str] = set(progress.get("processed_files", []))
    
    if args.clear_existing:
        print("\n清空现有医疗RAG向量库...")
        medical_vector_store.clear_all()
        print("✓ 清空完成")
        processed_files_set = set()
    
    print("\n步骤1: 获取现有数据统计")
    print("-" * 40)
    existing_counts = {}
    for dept in DEPARTMENT_QUOTAS.keys():
        count = medical_vector_store.get_size(dept)
        existing_counts[dept] = count
        print(f"  {dept}: {count} 条")
    
    print("\n步骤2: 加载医疗文档")
    print("-" * 40)
    
    documents = []
    doc_dir = args.doc_dir
    all_files = []
    
    if not os.path.exists(doc_dir):
        print(f"✗ 文档目录不存在: {doc_dir}")
        return
    
    supported_extensions = ['.txt', '.md', '.json', '.csv']
    
    for ext in supported_extensions:
        pattern = os.path.join(doc_dir, f'**/*{ext}')
        files = glob.glob(pattern, recursive=True)
        all_files.extend(files)
    
    total_files = len(all_files)
    skipped_files = 0
    
    for filepath in all_files:
        file_key = os.path.abspath(filepath)
        
        if file_key in processed_files_set:
            skipped_files += 1
            continue
        
        try:
            filename = os.path.basename(filepath)
            
            if filepath.lower().endswith('.csv'):
                docs = load_csv_documents(filepath)
                documents.extend(docs)
            elif filepath.lower().endswith('.txt') and ('_knowledge' in filepath.lower() or '_records' in filepath.lower()):
                docs = parse_structured_txt(filepath)
                documents.extend(docs)
            else:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                department = infer_department_from_filename(filename)
                
                documents.append({
                    "content": content,
                    "filename": filename,
                    "filepath": filepath,
                    "department": department,
                    "source_type": 'document'
                })
                print(f"✓ 加载文档: {filename} -> 科室: {department}")
            
            processed_files_set.add(file_key)
            
        except Exception as e:
            print(f"✗ 加载文档失败 {filepath}: {e}")
    
    if skipped_files > 0:
        print(f"\n⏭️  跳过 {skipped_files} 个已处理文件")
    
    print(f"\n共加载 {len(documents)} 个文档")
    
    if not documents:
        print("没有找到任何新的医疗文档")
        if os.path.exists(PROGRESS_FILE):
            os.remove(PROGRESS_FILE)
            print("✓ 进度文件已清除")
        return
    
    print("\n步骤3: 切分文档")
    print("-" * 40)
    chunks = chunk_documents(documents)
    
    if len(chunks) == 0:
        print("没有生成任何文档块")
        return
    
    print("\n步骤4: 按科室配额采样")
    print("-" * 40)
    
    if args.skip_sampling:
        print("⚠️ 跳过配额采样，处理所有数据")
        sampled_chunks = chunks
    else:
        sampled_chunks, _ = sample_by_quota(chunks, DEPARTMENT_QUOTAS, existing_counts)
    
    total_chunks = len(sampled_chunks)
    
    if total_chunks == 0:
        print("采样后没有剩余文档块")
        if os.path.exists(PROGRESS_FILE):
            os.remove(PROGRESS_FILE)
            print("✓ 进度文件已清除")
        return
    
    print("\n步骤5: 分批向量化和保存")
    print("-" * 40)
    
    start_idx = progress.get("processed_chunks", 0)
    saved_idx = progress.get("saved_chunks", 0)
    
    if start_idx > 0 and args.resume:
        print(f"📌 从第 {start_idx} 条继续处理...")
    
    batch_count = (total_chunks - start_idx + args.batch_size - 1) // args.batch_size
    total_cache_hits = 0
    total_cache_misses = 0
    start_time = time.time()
    
    for batch_num in range(batch_count):
        current_start = start_idx + batch_num * args.batch_size
        if current_start >= total_chunks:
            break
        
        print(f"\n📦 批次 {batch_num + 1}/{batch_count}")
        print(f"   处理范围: [{current_start} - {min(current_start + args.batch_size, total_chunks)})")
        
        end_idx, cache_hits, cache_misses = embed_chunks_batch(sampled_chunks, current_start, args.batch_size)
        total_cache_hits += cache_hits
        total_cache_misses += cache_misses
        
        print(f"   向量化完成: 缓存命中 {cache_hits} | 新计算 {cache_misses}")
        
        print(f"   保存到Milvus...")
        save_chunks_to_milvus(sampled_chunks, current_start, end_idx)
        
        current_processed_files = list(processed_files_set)
        save_progress(current_processed_files, end_idx, end_idx)
        
        elapsed = time.time() - start_time
        processed = end_idx - start_idx
        avg_time_per_item = elapsed / processed if processed > 0 else 0
        remaining = total_chunks - end_idx
        eta = remaining * avg_time_per_item
        
        print(f"   ✓ 已完成 {end_idx}/{total_chunks} ({(end_idx/total_chunks)*100:.1f}%)")
        print(f"   ⏱️  已用时: {elapsed:.1f}s | ETA: {eta:.1f}s")
    
    save_progress(list(processed_files_set), total_chunks, total_chunks)
    
    print("\n" + "=" * 60)
    print("嵌入完成!")
    print("=" * 60)
    print(f"总文档块数: {total_chunks}")
    print(f"缓存命中: {total_cache_hits}")
    print(f"新向量化: {total_cache_misses}")
    print(f"总耗时: {time.time() - start_time:.1f}秒")
    
    print("\n各科室文档统计:")
    for dept in DEPARTMENT_QUOTAS.keys():
        count = medical_vector_store.get_size(dept)
        quota = DEPARTMENT_QUOTAS[dept]
        print(f"  - {dept}: {count} 条 (配额: {quota})")
    
    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)
        print("\n✓ 进度文件已清除")


if __name__ == "__main__":
    main()