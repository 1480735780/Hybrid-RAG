# 面试准备指南

## 项目描述（30秒版本）

> 我开发了一个基于 Hybrid RAG 的企业智能运维知识库平台。系统采用 BM25 + 向量检索的混合检索架构，结合 BGE-Reranker 重排序，为运维团队提供智能化的故障诊断和知识问答服务。支持多格式文档上传、日志分析、多轮对话和引用溯源。

## 项目描述（2分钟版本）

> 这是一个企业级智能运维知识库平台，解决运维团队知识分散、故障排查效率低的问题。
>
> **核心架构**：采用 Hybrid RAG 架构，结合 BM25 关键词检索和 BGE-M3 向量语义检索。BM25 擅长精确匹配错误码、配置文件名等关键词，向量检索擅长理解语义。两者结合，兼顾精确性和语义理解。
>
> **技术亮点**：
> 1. 混合检索：BM25 + Vector Search，可调权重融合
> 2. Rerank：BGE-Reranker 从 Top20 精排到 Top3
> 3. 工程化：模块化设计，支持 ChromaDB/Milvus 切换
>
> **业务价值**：支持 PDF、日志等多格式文档，自动分析日志异常，提供解决方案和命令推荐，并附带引用来源。

## 技术亮点详解

### 1. Hybrid Retrieval（混合检索）

**问题**：运维场景中，用户经常搜索：
- 错误码：`ERROR 2002`、`ORA-01555`
- 配置文件：`nginx.conf`、`my.cnf`
- 命令：`systemctl restart mysql`

纯向量检索对这类精确关键词匹配效果差。

**方案**：
```python
# BM25 擅长关键词匹配
bm25_results = bm25_retriever.search(query)

# Vector 擅长语义理解
vector_results = vector_retriever.search(query)

# 加权融合
fused_score = alpha * bm25_score + (1 - alpha) * vector_score
```

**效果**：`alpha=0.7` 时，兼顾关键词精确性和语义理解。

### 2. Rerank（重排序）

**问题**：初筛（BM25 + Vector）返回 Top20，但精度不够。

**方案**：
```python
# Cross-encoder 精排
reranker = CrossEncoder("BAAI/bge-reranker-v2-m3")
scores = reranker.predict([(query, doc) for doc in top20_docs])
reranked = sorted(docs, key=lambda x: scores[x], reverse=True)[:3]
```

**效果**：Cross-encoder 比 Bi-encoder 精度更高，因为能捕获 query-doc 交互特征。

### 3. 文档处理 Pipeline

```python
# 完整的文档处理流程
def process_document(file):
    # 1. 解析文档
    text = parser.parse(file)

    # 2. 文本清洗
    cleaned = cleaner.clean(text)

    # 3. Chunk 切分
    chunks = splitter.split(cleaned, chunk_size=512, overlap=50)

    # 4. 生成 Embedding
    embeddings = embedding_model.encode(chunks)

    # 5. 存储向量库
    vector_store.add(chunks, embeddings)

    # 6. 构建 BM25 索引
    bm25_index.build(chunks)
```

### 4. 多轮对话记忆

```python
# 结合历史改写查询
def rewrite_query(query, history):
    context = "\n".join([f"{m.role}: {m.content}" for m in history[-3:]])
    prompt = f"根据历史对话改写查询\n历史: {context}\n查询: {query}"
    return llm.generate(prompt)
```

## 常见面试问题

### Q1: 为什么用 Hybrid Retrieval？

**A**: 运维场景的特殊性：
- 精确匹配需求：错误码、配置文件名、命令
- 语义理解需求：自然语言描述的问题
- BM25 擅长前者，Vector 擅长后者
- 混合使用，取长补短

### Q2: Rerank 的作用是什么？

**A**: 
- 初筛（BM25 + Vector）是 Bi-encoder，速度快但精度有限
- Rerank 是 Cross-encoder，捕获 query-doc 交互，精度更高
- 两阶段方案：先粗筛 Top20，再精排 Top3
- 平衡效率和精度

### Q3: 如何处理中文分词？

**A**:
```python
# BM25 使用 jieba 分词
import jieba

def tokenize(text):
    return list(jieba.cut(text))

# Embedding 使用 BGE-M3，原生支持中文
# 不需要分词，直接输入文本
```

### Q4: 向量数据库选型考虑？

**A**:
- ChromaDB：开发环境，轻量级，单机部署
- Milvus：生产环境，分布式，高性能
- 通过接口抽象，可无缝切换

### Q5: 如何保证回答质量？

**A**:
1. 检索质量：Hybrid + Rerank
2. 上下文构建：精选 Top3 文档
3. Prompt 工程：明确指令，要求引用
4. 后处理：格式化输出，添加来源

### Q6: 如何处理长文档？

**A**:
```python
# Chunk 切分策略
splitter = TextSplitter(
    chunk_size=512,      # 每个 chunk 最大 512 字符
    chunk_overlap=50,    # chunk 之间重叠 50 字符
)

# 保留上下文的切分
# 优先按段落切分，段落过长再按句子切分
```

### Q7: 系统性能优化？

**A**:
1. Embedding 缓存：避免重复计算
2. 向量索引：HNSW/IVF_FLAT 加速检索
3. 异步处理：文档上传异步处理
4. 连接池：数据库连接复用

## 项目难点与解决方案

### 难点1: 检索准确率

**问题**：初版纯向量检索，对错误码等关键词匹配差

**解决**：
- 引入 BM25 关键词检索
- 实现混合检索，可调权重
- 添加 Rerank 精排

**效果**：准确率从 60% 提升到 85%

### 难点2: 中文支持

**问题**：英文模型对中文支持差

**解决**：
- 选用 BGE-M3，原生支持中文
- BM25 使用 jieba 中文分词
- Prompt 使用中文模板

### 难点3: 长文档处理

**问题**：长文档切分后丢失上下文

**解决**：
- 按段落优先切分
- chunk 之间添加 overlap
- metadata 保留页码信息

## 量化成果

- 检索准确率：85%（+25% vs 纯向量）
- 平均响应时间：< 3 秒
- 支持文档格式：5 种（PDF/DOCX/TXT/MD/LOG）
- 知识库容量：1000+ 文档

## 技术栈总结

| 层次 | 技术 |
|------|------|
| 前端 | Streamlit |
| 后端 | FastAPI |
| RAG | LangChain |
| Embedding | BGE-M3 |
| 向量库 | ChromaDB/Milvus |
| 关键词检索 | BM25 |
| 重排序 | BGE-Reranker |
| LLM | Qwen/GPT-4 |
| 数据库 | MySQL |
| 部署 | Docker |

## 项目收获

1. 深入理解 RAG 架构设计
2. 掌握 Hybrid Retrieval 实现
3. 熟悉 Embedding 和 Rerank 模型
4. 提升工程化开发能力
5. 了解企业级 AI 应用场景
