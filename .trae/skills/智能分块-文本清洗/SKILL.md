---
name: 智能分块 + 文本清洗
description: 请使用【魔女之旅-RAG-优化专家】技能，优化我的RAG系统
---

---
name: 魔女之旅-RAG-优化专家
description: 针对《魔女之旅》项目做RAG全流程优化：语义分块、Milvus重建、向量入库、检索调参、Hit@1从40%→90%+
version: 1.0
---

# 魔女之旅 RAG 全流程优化专家

## 描述
自动优化《魔女之旅》RAG系统：
- 智能语义分块（修复破碎chunk）
- 删除旧Milvus库、重建优化库
- text2vec向量化 + 最优检索参数
- 标准测试集评估 + Hit@1提升至90%+
- Windows环境兼容、一键运行

## 使用场景（触发条件）
- 当用户说：优化RAG、提升Hit@1、重建Milvus、分块优化、RAG测评
- 当用户提供：RAG日志、Milvus连接、text2vec模型、知识库文本
- 当用户需求：《魔女之旅》知识库、检索准确率低、chunk切割混乱

## 指令（执行步骤）

### 1. 环境与配置
- 确认：Python、pymilvus、transformers、torch、jieba
- 模型：shibing624/text2vec-base-chinese
- Milvus：localhost:19530
- 知识库：《魔女之旅》小说txt

### 2. 文本清洗 + 智能分块（核心）
- 清洗：去多余换行/空格/符号、统一标点
- 分块：按段落/句子切割、max=512、min=100、重叠50
- 输出：id, content, category(character/plot), source

### 3. Milvus 重建（必须删旧库）
1. 连接 client = MilvusClient("http://localhost:19530")
2. 删除旧集合：client.drop_collection("rag_old")
3. 新建优化集合：
   - 字段：id(INT64), vector(FLOAT_VECTOR,768), content(VARCHAR), category(VARCHAR)
   - 索引：IVF_SQ8, COSINE, nlist=1024
   - 检索参数：topk=10, nprobe=32, ef=200

### 4. 向量化 + 批量入库
- 用 text2vec 生成 768 维向量
- 批量插入、加载索引
- 打印：总chunk数、耗时、向量维度

### 5. 检索优化（中文最优）
- 距离：COSINE（禁用L2）
- 过滤：支持按 category 筛选
- 结果：按相似度排序、返回content+元数据

### 6. 标准评估（50题测试集）
- 测试集：100%原文可查、无模糊/推理题
- 指标：Hit@1/3/5、MRR、Recall@5、分类准确率
- 报告：输出清晰、对比优化前后

### 7. 输出要求
- 全代码可直接运行（Windows）
- 注释清晰、分步执行
- 结果验证、效果总结

## 示例
### 输入（触发）
优化我的《魔女之旅》RAG，当前Hit@1=40%，知识库3927 chunks，Milvus localhost:19530，模型shibing624_text2vec-base-chinese

### 输出
1. 智能分块代码
2. Milvus重建代码
3. 向量入库代码
4. 检索优化代码
5. 标准50题测试集
6. 评估报告（Hit@1≥90%）