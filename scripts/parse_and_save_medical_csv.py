"""解析医疗CSV文件并保存到指定目录"""
import sys
import os
import glob
import csv
from typing import List, Dict, Any

def parse_csv_files(input_dir: str, output_dir: str):
    """解析CSV文件并保存到输出目录"""
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 查找所有CSV文件
    csv_files = glob.glob(os.path.join(input_dir, '*.csv'))
    print(f"找到 {len(csv_files)} 个CSV文件")
    
    all_records = []
    
    for csv_file in csv_files:
        print(f"\n处理文件: {os.path.basename(csv_file)}")
        
        # 解析单个CSV文件
        records = parse_single_csv(csv_file)
        print(f"  解析完成: {len(records)} 条有效记录")
        
        all_records.extend(records)
    
    # 按科室分组保存
    save_by_department(all_records, output_dir)
    
    print(f"\n✅ 完成！共处理 {len(all_records)} 条记录")


def parse_single_csv(filepath: str) -> List[Dict[str, Any]]:
    """解析单个CSV文件"""
    records = []
    filename = os.path.basename(filepath)
    
    # 推断科室
    department = infer_department_from_filename(filename)
    
    # 尝试多种编码
    encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030']
    skipped = 0
    
    for encoding in encodings:
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames
                
                if headers is None:
                    continue
                
                # 确定问题字段名
                question_key = 'question' if 'question' in headers else 'ask'
                
                for row_num, row in enumerate(reader, 1):
                    dept = row.get('department', '').strip() or department
                    title = row.get('title', '').strip()
                    question = row.get(question_key, '').strip()
                    answer = row.get('answer', '').strip()
                    
                    # 数据清洗
                    if not is_valid_medical_record(title, question, answer):
                        skipped += 1
                        continue
                    
                    records.append({
                        "department": dept,
                        "title": title,
                        "question": question,
                        "answer": answer,
                        "source_file": filename,
                        "row_num": row_num
                    })
                
                print(f"  使用编码: {encoding}, 跳过无效记录: {skipped}")
                break
                
        except Exception as e:
            continue
    
    return records


def infer_department_from_filename(filename: str) -> str:
    """从文件名推断科室"""
    filename_lower = filename.lower()
    
    department_keywords = {
        "儿科": ["儿科", "儿童", "小儿"],
        "妇产科": ["妇产科", "妇科", "产科"],
        "男科": ["男科", "男性"],
        "内科": ["内科"],
        "外科": ["外科"],
        "肿瘤科": ["肿瘤科", "肿瘤"]
    }
    
    for department, keywords in department_keywords.items():
        for keyword in keywords:
            if keyword in filename_lower:
                return department
    
    return "内科"


def is_valid_medical_record(title: str, question: str, answer: str) -> bool:
    """检查记录是否为有效的医疗问答"""
    # 检查基本长度
    if len(title) < 2 or len(question) < 5 or len(answer) < 10:
        return False
    
    # 检查是否包含医疗相关关键词
    medical_keywords = ['治疗', '症状', '诊断', '疾病', '用药', '检查', '医生', '医院', '患者', '病情', '健康']
    text = title + question + answer
    
    has_medical = any(keyword in text for keyword in medical_keywords)
    if not has_medical:
        # 允许一些通用健康问题
        health_keywords = ['吃', '喝', '注意', '怎么办', '怎么治', '如何', '什么', '为什么', '治疗']
        has_health = any(keyword in text for keyword in health_keywords)
        return has_health
    
    return True


def save_by_department(records: List[Dict[str, Any]], output_dir: str):
    """按科室分组保存记录"""
    # 按科室分组
    records_by_dept = {}
    for record in records:
        dept = record["department"]
        if dept not in records_by_dept:
            records_by_dept[dept] = []
        records_by_dept[dept].append(record)
    
    # 保存每个科室的文件
    for dept, dept_records in records_by_dept.items():
        output_file = os.path.join(output_dir, f"{dept}_knowledge.txt")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for i, record in enumerate(dept_records, 1):
                f.write(f"【记录 {i}】\n")
                f.write(f"【科室】{record['department']}\n")
                f.write(f"【标题】{record['title']}\n")
                f.write(f"【问题】{record['question']}\n")
                f.write(f"【答案】{record['answer']}\n")
                f.write(f"【来源】{record['source_file']}:第{record['row_num']}行\n")
                f.write("=" * 80 + "\n\n")
        
        print(f"  保存科室 [{dept}]: {len(dept_records)} 条记录 -> {output_file}")


def main():
    if len(sys.argv) < 2:
        print("用法: python parse_and_save_medical_csv.py <CSV目录>")
        print("示例: python parse_and_save_medical_csv.py D:/medicaldata/Chinese-medical-dialogue-data-master/Data")
        return
    
    input_dir = sys.argv[1]
    output_dir = r"d:\Cursorcode\eleina_agent\src\rag\knowledge"
    
    print("=" * 60)
    print("解析医疗CSV文件")
    print("=" * 60)
    print(f"输入目录: {input_dir}")
    print(f"输出目录: {output_dir}")
    print("=" * 60)
    
    parse_csv_files(input_dir, output_dir)


if __name__ == "__main__":
    main()