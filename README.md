# Enterprise Intelligent Ops Assistant

基于 Hybrid RAG 的企业智能运维知识库平台

## 项目简介

Enterprise Intelligent Ops Assistant 是一个企业级智能运维知识库平台，采用 Hybrid RAG（检索增强生成）架构，结合 BM25 关键词检索和向量语义检索，为运维团队提供智能化的知识问答和故障诊断服务。

## 核心特性

- **Hybrid Retrieval**: BM25 + Vector Search 混合检索，兼顾关键词精确匹配和语义理解
- **Rerank**: BGE-Reranker 重排序，提升召回质量
- **Multi-format Support**: 支持 PDF、DOCX、TXT、Markdown、日志文件
- **Log Analysis**: 智能日志分析，自动提取异常和错误码
- **Multi-turn Conversation**: 多轮对话记忆，上下文关联
- **Source Citation**: 回答附带引用来源，可追溯
- **Metadata Filtering**: 基于部门、服务、优先级的元数据过滤

## 系统架构

```
用户 Web UI
    ↓
FastAPI API Gateway
    ↓
Query Rewrite (查询改写)
    ↓
Hybrid Retrieval (混合检索)
    ├── BM25 (关键词检索)
    └── Vector Search (语义检索)
    ↓
Rerank (重排序)
    ↓
LLM Generation (大模型生成)
    ↓
Source Citation (引用溯源)
```

## 技术栈

| 组件 | 技术选型 |
|------|----------|
| 后端框架 | FastAPI |
| RAG 框架 | LangChain |
| Embedding | BGE-M3 |
| 向量数据库 | ChromaDB (开发) / Milvus (生产) |
| 关键词检索 | BM25 (rank-bm25) |
| 重排序 | BGE-Reranker |
| LLM | Qwen2.5 / DeepSeek / GPT-4 |
| 数据库 | MySQL |
| 前端 | Streamlit |
| 部署 | Docker |

## 项目结构

```
RAG_Agent_Project/
├── backend/                    # 后端应用
│   ├── app/
│   │   ├── api/               # API 路由
│   │   │   └── endpoints/     # API 端点
│   │   ├── core/              # 核心模块
│   │   ├── models/            # 数据模型
│   │   ├── services/          # 业务逻辑
│   │   └── utils/             # 工具函数
│   └── config/                # 配置管理
├── frontend/                   # 前端应用
├── rag/                        # RAG 核心模块
│   ├── embeddings/            # Embedding 模型
│   ├── llm/                   # LLM 客户端
│   ├── parsers/               # 文档解析器
│   └── processors/            # 文本处理器
├── retrieval/                  # 检索模块
│   ├── bm25/                  # BM25 检索
│   ├── vector/                # 向量检索
│   └── hybrid/                # 混合检索
├── rerank/                     # 重排序模块
├── memory/                     # 对话记忆
├── prompt/                     # Prompt 模板
├── vector_store/               # 向量存储
├── knowledge_base/             # 知识库文件
├── docker/                     # Docker 配置
├── tests/                      # 测试代码
└── docs/                       # 项目文档
```

## 快速开始

### 环境要求

- Python 3.10+
- MySQL 8.0+
- Docker (可选)

### 本地开发

1. 克隆项目
```bash
git clone <repository-url>
cd RAG_Agent_Project
```

2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，配置 API Key 等
```

5. 启动后端
```bash
uvicorn backend.app.main:app --reload --port 8000
```

6. 启动前端
```bash
streamlit run frontend/app.py --server.port 8501
```

### Docker 部署

1. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件
```

2. 启动服务
```bash
cd docker
docker-compose up -d
```

3. 访问服务
- 前端: http://localhost:8501
- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

## API 接口

### 聊天接口

```http
POST /api/v1/chat/
Content-Type: application/json

{
  "query": "MySQL 启动失败怎么办？",
  "session_id": "optional-session-id",
  "use_hybrid": true,
  "top_k": 5
}
```

### 文档上传

```http
POST /api/v1/documents/upload
Content-Type: multipart/form-data

file: <file>
metadata: {"department": "ops", "service": "mysql", "level": "P1"}
```

### 知识库搜索

```http
POST /api/v1/knowledge-base/search
Content-Type: application/json

{
  "query": "Docker 容器无法启动",
  "top_k": 10,
  "use_hybrid": true,
  "metadata_filter": {"service": "docker"}
}
```

## 核心模块说明

### 1. Hybrid Retrieval (混合检索)

```python
from retrieval import HybridRetriever

retriever = HybridRetriever(
    bm25_weight=0.3,
    vector_weight=0.7,
    top_k=20,
)

# 构建索引
retriever.build_index(documents)

# 搜索
results = retriever.search(
    query="MySQL connection error",
    metadata_filter={"service": "mysql"},
)
```

### 2. Rerank (重排序)

```python
from rerank import Reranker

reranker = Reranker(
    model_name="BAAI/bge-reranker-v2-m3",
    top_k=3,
)

# 重排序
reranked = reranker.rerank(query, documents)
```

### 3. Document Parsing (文档解析)

```python
from rag.parsers import DocumentParser

parser = DocumentParser()

# 解析文档
text = parser.parse("troubleshooting.pdf")

# 解析并获取元数据
result = parser.parse_with_metadata("troubleshooting.pdf")
```

## 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| APP_NAME | 应用名称 | Enterprise Ops Assistant |
| DEBUG | 调试模式 | true |
| DB_HOST | 数据库主机 | localhost |
| DB_PORT | 数据库端口 | 3306 |
| DB_USER | 数据库用户 | root |
| DB_PASSWORD | 数据库密码 | - |
| DB_NAME | 数据库名称 | ops_assistant |
| VECTOR_STORE_TYPE | 向量存储类型 | chroma |
| EMBEDDING_MODEL | Embedding 模型 | BAAI/bge-m3 |
| RERANK_MODEL | Rerank 模型 | BAAI/bge-reranker-v2-m3 |
| LLM_PROVIDER | LLM 提供商 | openai |
| OPENAI_API_KEY | OpenAI API Key | - |
| OPENAI_MODEL | OpenAI 模型 | gpt-4-turbo |

## 测试

```bash
# 运行所有测试
pytest

# 运行单元测试
pytest tests/unit/

# 运行集成测试
pytest tests/integration/

# 生成覆盖率报告
pytest --cov=backend --cov-report=html
```

## 开发路线图

### Phase 1: MVP (当前)
- [x] 基础 RAG Pipeline
- [x] Hybrid Retrieval
- [x] 文档上传和解析
- [x] 基础前端界面

### Phase 2: 增强功能
- [ ] 流式响应
- [ ] 更多文档格式支持
- [ ] 用户认证和权限
- [ ] 对话历史持久化

### Phase 3: 企业级功能
- [ ] 多租户支持
- [ ] 审计日志
- [ ] API 限流
- [ ] 监控和告警

### Phase 4: Agent 化
- [ ] MCP Tool 集成
- [ ] 自动化运维脚本
- [ ] 智能告警处理
- [ ] 自动故障修复

## 面试亮点

### 技术亮点

1. **Hybrid RAG 架构**
   - BM25 + Vector Search 混合检索
   - 解决运维场景中关键词和语义的双重需求
   - 可调权重的融合策略

2. **Rerank 重排序**
   - BGE-Reranker Cross-Encoder
   - Top20 → Top3 精排
   - 显著提升召回准确率

3. **工程化设计**
   - 模块化架构，高可扩展
   - 完整的 API 设计
   - Docker 容器化部署

4. **运维场景优化**
   - 错误码、配置文件等特殊文本处理
   - 日志分析和异常提取
   - 多轮对话上下文关联

### 项目价值

- 提升运维团队知识共享效率
- 加速故障诊断和解决
- 沉淀运维经验为知识库
- 降低新人培训成本

## 许可证

MIT License

## 联系方式

如有问题，请提交 Issue 或联系项目维护者。
