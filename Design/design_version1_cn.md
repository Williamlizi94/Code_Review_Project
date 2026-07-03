<div align="center">

# 🛡️ CodeGuardian AI — 智能代码审查 Agent

> 面向企业和团队的多语言、上下文感知代码审查平台，
> 由大模型推理 + 静态规则引擎 + RAG 增强驱动。

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-最新版-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-ReAct_Agent-1C3C3C?style=flat-square&logo=chainlink&logoColor=white)](https://langchain.com)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--5.4--mini-412991?style=flat-square&logo=openai&logoColor=white)](https://openai.com)
[![Semgrep](https://img.shields.io/badge/Semgrep-30%2B种语言-20B2AA?style=flat-square)](https://semgrep.dev)
[![pgvector](https://img.shields.io/badge/pgvector-RAG向量检索-336791?style=flat-square&logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)
[![License](https://img.shields.io/badge/许可证-Apache%202.0-E25822?style=flat-square)](../LICENSE)

</div>

---

## 📋 目录

- [项目简介](#-项目简介)
- [支持语言](#-支持语言)
- [核心功能](#-核心功能)
- [技术架构](#-技术架构)
- [技术栈](#-技术栈)
- [快速开始](#-快速开始)
- [模块说明](#-模块说明)
- [API 接口](#-api-接口)
- [配置说明](#-配置说明)
- [CI/CD 集成](#-cicd-集成)
- [路线图](#-路线图)
- [贡献指南](#-贡献指南)

---

## 📖 项目简介

**CodeGuardian AI** 是一款面向企业和开发团队的智能代码审查 Agent。它将 Semgrep 30+ 语言静态分析、Tree-sitter AST 解析、LangGraph 大模型推理与 RAG 增强缺陷检索深度结合，为任意技术栈提供多维度、可落地的代码问题诊断与修复建议。

### 💡 解决的核心痛点

| ❌ 传统静态分析痛点 | ✅ CodeGuardian AI 解决方案 |
|---|---|
| 规则固定，误报率高 | LLM 结合上下文语义理解，过滤无效告警 |
| 无法理解业务逻辑 | RAG 检索企业私有知识库 & 历史缺陷案例 |
| 工具锁定语言，无法覆盖多语言仓库 | Semgrep + Tree-sitter 一套管线支持 30+ 语言 |
| 报告不可读，开发不爱看 | 结构化 HTML/Markdown/PDF 报告 + Diff 精确定位 |
| 只能手动触发 | Webhook + REST API 自动集成 PR/MR/流水线 |
| 多工具割裂，结果分散 | 统一 Agent 协同调度所有分析器 |

---

## 🌐 支持语言

| 语言 | 静态分析 | AST 解析 | 风格规范 |
|---|---|---|---|
| 🐍 Python | Semgrep, Bandit | Tree-sitter | PEP8 / Black |
| ☕ Java | Semgrep | Tree-sitter | Google Java Style |
| 🟦 TypeScript / JavaScript | Semgrep, ESLint | Tree-sitter | Airbnb / Standard |
| 🐹 Go | Semgrep, Staticcheck | Tree-sitter | Effective Go |
| 🦀 Rust | Semgrep, Clippy | Tree-sitter | Rust API Guidelines |
| ⚙️ C / C++ | Semgrep | Tree-sitter | MISRA C / CERT |
| 💎 Ruby | Semgrep, RuboCop | Tree-sitter | Ruby Style Guide |
| 🐘 PHP | Semgrep | Tree-sitter | PSR-12 |
| 🍎 Swift / Kotlin | Semgrep | Tree-sitter | 官方风格指南 |

---

## ⚡ 核心功能

### 🔍 1. 多范围审查

支持五种粒度的代码审查入口：

- 🏢 **项目级** — 拉取整个 Git 仓库，全量扫描
- 📁 **目录级** — 指定模块或包路径进行局部审查
- 📄 **文件级** — 单文件上传或路径指定
- 📝 **代码片段** — 粘贴代码块即时审查（无需仓库）
- ⚡ **增量模式** — 基于 `git diff`，只审查当前 PR 的变更行

### ⚙️ 2. AI + 规则双引擎深度分析

```
用户代码
    │
    ├─► 📏 规则引擎层
    │       ├─► Semgrep       （30+ 语言，OWASP / 安全 / 风格规则集）
    │       ├─► Tree-sitter   （AST 级别结构分析）
    │       └─► 语言专项 Linter（ESLint / Bandit / Staticcheck / Clippy ...）
    │               └─► 结构化问题列表（位置 + 规则编号 + 严重度）
    │
    ├─► 🧠 LLM 推理层（LangGraph Agent）
    │       ├─► 调用本地分析器工具
    │       ├─► 语义理解 & 业务逻辑分析
    │       └─► 修复建议生成（修改前后代码对比）
    │
    └─► 🔎 RAG 增强层
            ├─► 相似历史缺陷检索（BM25 + 向量混合搜索）
            ├─► Rerank 精排
            └─► 注入增强上下文到 LLM Prompt
```

**分析维度：**

| 维度 | 检测内容 |
|---|---|
| 🎨 代码规范 | 命名、格式、注释 |
| 🔒 安全漏洞 | SQL 注入、XSS、SSRF、反序列化等 OWASP Top 10 |
| ⚡ 性能问题 | N+1 查询、异步上下文中的阻塞 I/O、内存泄漏风险 |
| 🔧 可维护性 | 圈复杂度、重复代码、魔法数字 |
| 💼 业务逻辑 | 根据 RAG 知识库推断潜在逻辑缺陷 |

### 🧠 3. RAG 知识增强

- 📂 **知识来源** — 历史代码审查记录、企业内部规范文档、缺陷案例库
- 🔍 **检索策略** — BM25 关键词检索 + 向量语义检索混合 + Cross-Encoder Rerank 精排
- 🌳 **代码感知分块** — Tree-sitter 按函数/类边界切分，而非按字符数任意截断
- 💾 **存储方案** — pgvector（向量）+ PostgreSQL 全文检索（内置）
- 🖥️ **管理界面** — 知识库上传、分类、版本管理

### 🔧 4. LangGraph 工具协同

LLM Agent 通过 LangGraph ReAct 循环以结构化工具调用驱动本地分析器，确保输出可信、可验证：

```python
# Agent 发出的工具调用示例
{
  "tool": "run_semgrep",
  "args": { "path": "src/", "ruleset": "p/owasp-top-ten", "lang": "python" }
}
```

内置工具集：

`run_semgrep` · `run_eslint` · `run_bandit` · `run_staticcheck` · `parse_ast` · `get_git_diff` · `search_knowledge_base`

### 📊 5. 专业审查报告

- **格式** — `HTML`（交互式）· `Markdown` · `PDF`
- **内容**
  - 🗺️ 问题分布热力图（按文件 / 按严重级别 / 按语言）
  - 📈 严重度统计（Critical / High / Medium / Low / Info）
  - 📍 精确行号定位 + Diff 高亮展示
  - 🤖 AI 生成的修复建议（含修改前后代码对比）
  - 📉 跨多次审查的历史趋势对比

### 📚 6. 审查历史与检索

- 所有审查任务持久化存储（PostgreSQL）
- 支持分页查询、关键词搜索、语言过滤、状态过滤
- 支持对历史结果发起二次追问（对话式审查）
- 审查结果可导出为知识库条目

### 📏 7. 编码规范管理

- 📦 **内置规范模板** — Google Style / Airbnb / PEP8 / Effective Go / MISRA C / CERT / OWASP
- ✏️ **自定义规范** — 上传私有规范文档，AI 自动解析为可执行规则
- 🔖 **规范版本管理** — 规范变更不影响历史审查结果可溯源性

### 🔀 8. Git 集成

- 配置 Git 平台地址（GitHub / GitLab / Bitbucket）及 Access Token
- 自动 Clone / Pull 最新代码
- 增量分析：只审查 `git diff` 变更范围，降低噪音
- 审查结果自动回写为 PR/MR 行级评论

### 🔄 9. CI/CD 集成

- 🪝 **Webhook** — PR/MR 创建/更新时自动触发审查
- 🔌 **REST API** — 流水线 Stage 中主动调用，获取审查报告
- 🚦 **质量门禁** — 支持按严重度阈值拦截构建（例：Critical >= 1 则 Fail）
- 🔩 **构建插件** *（规划中）* — GitHub Action / pre-commit hook

### 🔒 10. 安全与合规

- 🙈 敏感信息脱敏（密钥、Token、密码等不进入 LLM）
- 🔑 Git 凭据仅存于当前会话（可选加密持久化）
- 📋 完整审计日志（操作人、时间、输入摘要、输出摘要）
- 🔭 链路追踪（Trace ID 贯穿全流程，便于问题排查）

---

## 🏗️ 技术架构

```
┌──────────────────────────────────────────────────────────────┐
│                        接入层                                 │
│   Web Browser / UI    Git Webhook    CI/CD Pipeline          │
└───────────────────────────┬──────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────┐
│                     网关 & 认证层                              │
│            FastAPI Router  ·  JWT Bearer Auth                 │
└───────────────────────────┬──────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────┐
│                       核心服务层                               │
│                                                              │
│  ┌─────────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │  审查调度服务    │  │  Git 操作服务 │  │  报告生成服务   │  │
│  │  (Celery Tasks) │  │  (GitPython) │  │  (Jinja2/PDF)  │  │
│  └────────┬────────┘  └──────────────┘  └────────────────┘  │
│           │                                                  │
│  ┌────────▼────────────────────────────────────────────┐    │
│  │           LangGraph AI Agent 执行引擎                 │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌───────────┐  │    │
│  │  │  LLM 调用层  │  │   工具节点   │  │  Prompt   │  │    │
│  │  │ (LangChain)  │  │(Semgrep/AST) │  │  Builder  │  │    │
│  │  └──────────────┘  └──────────────┘  └───────────┘  │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                   RAG 引擎                             │   │
│  │  知识库管理  ·  混合检索（pgvector+BM25）  ·  Rerank 精排│   │
│  └──────────────────────────────────────────────────────┘   │
└───────────────────────────┬──────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────┐
│                       数据基础设施                             │
│                                                              │
│  PostgreSQL + pgvector    Redis              S3 / MinIO       │
│  （元数据 + 向量存储）      （缓存 / 队列）    （文件存储）      │
└──────────────────────────────────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────┐
│                       AI 模型层                               │
│       OpenAI GPT-5.4-mini / GPT-5.5  ·  Ollama（本地）       │
└──────────────────────────────────────────────────────────────┘
```

### 🔄 内部事件流（审查管线）

```
ReviewRequest
    │
    ▼
[1] 📥 GitCloneTask       → 拉取/更新代码（GitPython）
    │
    ▼
[2] 🔬 StaticAnalysisTask → Semgrep + 语言专项 Linter 并行执行（Celery）
    │
    ▼
[3] 🌳 ASTParseTask       → Tree-sitter 构建 AST，提取函数/类上下文
    │
    ▼
[4] 🧠 RAGRetrievalTask   → 检索相似历史缺陷，生成增强上下文
    │
    ▼
[5] 🤖 LLMReviewTask      → LangGraph Agent：工具调用 + Prompt 构造 + LLM 推理
    │
    ▼
[6] 🔀 ResultMergeTask    → 去重、分级、结构化
    │
    ▼
[7] 📊 ReportGenerateTask → HTML / Markdown / PDF 报告（Jinja2 + WeasyPrint）
    │
    ▼
[8] 📣 NotifyTask         → 回写 PR 评论 / Webhook 回调 / 邮件通知
```

---

## 🛠️ 技术栈

| 类别 | 技术选型 |
|---|---|
| **语言** | ![Python](https://img.shields.io/badge/-Python_3.12+-3776AB?style=flat-square&logo=python&logoColor=white) |
| **Web 框架** | ![FastAPI](https://img.shields.io/badge/-FastAPI_+_Uvicorn-009688?style=flat-square&logo=fastapi&logoColor=white) |
| **AI Agent** | ![LangChain](https://img.shields.io/badge/-LangChain_+_LangGraph-1C3C3C?style=flat-square) |
| **大语言模型** | ![OpenAI](https://img.shields.io/badge/-GPT--5.4--mini_/_GPT--5.5-412991?style=flat-square&logo=openai&logoColor=white) |
| **静态分析** | Semgrep · Bandit · ESLint · Staticcheck · Clippy |
| **AST 解析** | Tree-sitter（通用，语言无关） |
| **RAG 检索** | LlamaIndex + BM25 + pgvector + Cross-Encoder Rerank |
| **嵌入模型** | `text-embedding-3-small` / `nomic-embed-code`（Ollama 本地） |
| **任务队列** | ![Celery](https://img.shields.io/badge/-Celery_+_Redis-37814A?style=flat-square&logo=celery&logoColor=white) |
| **数据存储** | ![PostgreSQL](https://img.shields.io/badge/-PostgreSQL_+_pgvector-336791?style=flat-square&logo=postgresql&logoColor=white) |
| **文件存储** | AWS S3 / MinIO |
| **文档解析** | Unstructured.io |
| **报告生成** | Jinja2 + WeasyPrint |
| **认证授权** | FastAPI-Users + JWT |
| **Git 操作** | GitPython · PyGithub · python-gitlab · atlassian-python-api |
| **构建 & 部署** | ![Docker](https://img.shields.io/badge/-Docker_+_Poetry-2496ED?style=flat-square&logo=docker&logoColor=white) |
| **监控 & 日志** | Loguru · OpenTelemetry · Grafana / Loki |
| **测试** | pytest · pytest-asyncio · Testcontainers |

---

## 🚀 快速开始

### 环境依赖

- Python 3.12+
- Docker & Docker Compose
- Poetry（`pip install poetry`）

### 1. 克隆项目

```bash
git clone https://github.com/your-org/codeguardian-ai.git
cd codeguardian-ai
```

### 2. 启动基础设施

```bash
# 启动 PostgreSQL（含 pgvector）、Redis、MinIO
docker compose -f docker/compose-dev.yml up -d
```

### 3. 安装依赖

```bash
poetry install
```

### 4. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，填入以下配置：

```env
# 大语言模型
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-5.4-mini

# 数据库
DATABASE_URL=postgresql+asyncpg://codeguardian:codeguardian@localhost:5432/codeguardian

# Redis
REDIS_URL=redis://localhost:6379/0

# 文件存储
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=codeguardian

# 认证
JWT_SECRET=change-me-in-production
```

### 5. 初始化数据库

```bash
poetry run alembic upgrade head
```

### 6. 启动应用

```bash
# 终端 1：API 服务
poetry run uvicorn app.main:app --reload --port 8080

# 终端 2：Celery Worker（异步分析任务）
poetry run celery -A app.worker worker --loglevel=info
```

### 7. 访问 Web UI

打开浏览器访问 [http://localhost:8080](http://localhost:8080)

> 默认账号：`admin / codeguardian123`

---

## 📁 模块说明

```
codeguardian-ai/
├── app/
│   ├── main.py                 # FastAPI 应用入口
│   ├── agent/                  # 🤖 LangGraph AI Agent
│   │   ├── graph.py            # Agent 图定义（ReAct 循环）
│   │   ├── tools/              # 工具节点定义
│   │   │   ├── semgrep.py      # Semgrep 封装
│   │   │   ├── tree_sitter.py  # AST 解析器封装
│   │   │   ├── linters.py      # 语言专项 Linter 封装
│   │   │   └── git_diff.py     # Git Diff 提取器
│   │   └── prompts/            # Prompt 模板（Jinja2）
│   ├── review/                 # 🔍 审查业务核心
│   │   ├── service.py          # 审查任务入口
│   │   ├── pipeline/           # 管线各阶段实现
│   │   └── merger.py           # 结果去重 & 分级
│   ├── analyzer/               # 🔬 静态分析器封装
│   │   ├── semgrep.py
│   │   ├── bandit.py           # Python 安全扫描
│   │   ├── eslint.py           # JS/TS
│   │   └── staticcheck.py      # Go
│   ├── rag/                    # 🧠 RAG 引擎
│   │   ├── knowledge.py        # 知识库管理
│   │   ├── hybrid_search.py    # BM25 + 向量混合检索
│   │   └── rerank.py           # Cross-Encoder 精排
│   ├── git/                    # 🔀 Git 操作封装
│   │   └── service.py          # Clone、Pull、Diff（GitPython）
│   ├── report/                 # 📊 报告生成
│   │   ├── html.py             # Jinja2 HTML 报告
│   │   ├── markdown.py
│   │   └── pdf.py              # WeasyPrint PDF
│   ├── webhook/                # 🪝 Webhook 接收 & 事件路由
│   │   ├── github.py
│   │   ├── gitlab.py
│   │   └── bitbucket.py
│   ├── auth/                   # 🔒 JWT 认证（FastAPI-Users）
│   ├── models/                 # 💾 SQLAlchemy ORM 模型
│   ├── schemas/                # 📐 Pydantic 请求/响应 Schema
│   ├── worker.py               # ⚙️ Celery 应用 & 任务定义
│   └── config.py               # 🔧 全局配置（pydantic-settings）
├── docker/
│   ├── compose-dev.yml         # 开发环境基础设施
│   └── compose-prod.yml        # 生产环境全量部署
├── migrations/                 # Alembic 数据库迁移
├── tests/                      # pytest 测试套件
│   ├── unit/
│   └── integration/
├── docs/
│   ├── api.md
│   └── architecture.md
├── pyproject.toml
└── .env.example
```

---

## 🔌 API 接口

### 提交审查任务

```http
POST /api/v1/reviews
Content-Type: application/json
Authorization: Bearer <token>

{
  "type": "GIT_REPO",           // GIT_REPO | DIRECTORY | FILE | SNIPPET
  "target": "https://github.com/org/repo.git",
  "branch": "feature/login",
  "languages": ["python", "typescript"],   // 留空则自动检测
  "mode": "INCREMENTAL",        // FULL | INCREMENTAL
  "rulesetId": "owasp-top-ten",
  "notifyWebhook": "https://your-ci/callback"
}
```

### 查询审查结果

```http
GET /api/v1/reviews/{reviewId}
GET /api/v1/reviews/{reviewId}/report?format=html
```

### 历史审查列表

```http
GET /api/v1/reviews?page=0&size=20&keyword=injection&severity=HIGH&lang=python
```

### 知识库管理

```http
POST /api/v1/knowledge/upload     # 上传规范文档
GET  /api/v1/knowledge/search     # 检索相似案例
```

### Webhook（供 Git 平台调用）

```http
POST /api/v1/webhook/github
POST /api/v1/webhook/gitlab
POST /api/v1/webhook/bitbucket
```

> 完整 API 文档见 [docs/api.md](../docs/api.md) 或启动后访问 `/docs`（Swagger UI）

---

## ⚙️ 配置说明

### 切换 AI 模型

```env
OPENAI_MODEL=gpt-5.4-mini       # 默认，性价比最优
# OPENAI_MODEL=gpt-5.5          # 最高质量
# OLLAMA_MODEL=codellama:34b    # 本地部署，数据不出境
```

### 规则引擎开关

```env
ANALYZER_SEMGREP_ENABLED=true
ANALYZER_BANDIT_ENABLED=true       # 仅 Python
ANALYZER_ESLINT_ENABLED=true       # 仅 JS/TS
ANALYZER_STATICCHECK_ENABLED=true  # 仅 Go
ANALYZER_CLIPPY_ENABLED=true       # 仅 Rust
```

### Semgrep 规则集

```env
SEMGREP_RULES=p/owasp-top-ten,p/secrets,p/python,p/typescript
```

### 🚦 质量门禁阈值

```env
QUALITY_GATE_ENABLED=true
QUALITY_GATE_FAIL_ON_CRITICAL=1    # Critical 问题 >= 1 则返回失败状态码
QUALITY_GATE_FAIL_ON_HIGH=10
```

---

## 🔄 CI/CD 集成

### GitHub Actions

```yaml
- name: CodeGuardian AI Review
  uses: your-org/codeguardian-action@v1
  with:
    server-url: ${{ secrets.CODEGUARDIAN_URL }}
    api-token: ${{ secrets.CODEGUARDIAN_TOKEN }}
    fail-on-critical: true
```

### GitLab CI

```yaml
code-review:
  stage: test
  script:
    - |
      RESULT=$(curl -sf -X POST "$CODEGUARDIAN_URL/api/v1/reviews" \
        -H "Authorization: Bearer $CODEGUARDIAN_TOKEN" \
        -d "{\"type\":\"DIRECTORY\",\"target\":\"$CI_PROJECT_DIR\"}" | jq -r '.status')
      [ "$RESULT" = "PASS" ] || exit 1
```

### Jenkins

```groovy
stage('AI Code Review') {
    steps {
        codeguardianReview(
            serverUrl: env.CODEGUARDIAN_URL,
            apiToken: credentials('codeguardian-token'),
            failOnCritical: true
        )
    }
}
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/your-org/codeguardian-ai
    rev: v0.3.0
    hooks:
      - id: codeguardian-review
        args: [--mode, snippet, --fail-on, HIGH]
```

---

## 🗺️ 路线图

### v0.1 — MVP（当前）
- [x] 项目骨架（FastAPI + Python 3.12）
- [x] 基础 REST API 设计
- [ ] Semgrep 集成（多语言静态分析）
- [ ] LangGraph Agent + OpenAI GPT-5.4-mini 审查核心
- [ ] 简单 HTML 报告生成（Jinja2）
- [ ] PostgreSQL 任务持久化（SQLAlchemy + Alembic）

### v0.2 — RAG 增强
- [ ] pgvector 集成 + OpenAI 嵌入模型
- [ ] 知识库管理界面
- [ ] BM25 + 向量混合检索（LlamaIndex）
- [ ] Cross-Encoder Rerank 精排

### v0.3 — Git & CI 集成
- [ ] GitHub / GitLab / Bitbucket Webhook 接收
- [ ] 审查结果回写 PR/MR 行级评论
- [ ] 增量 Diff 分析模式
- [ ] GitHub Actions 集成
- [ ] Pre-commit hook 支持

### v0.4 — 多语言扩展
- [ ] Tree-sitter AST 级别分析（全支持语言）
- [ ] ESLint / Bandit / Staticcheck / Clippy / RuboCop 集成
- [ ] 语言自动检测
- [ ] 按语言独立配置规则集

### v0.5 — 企业特性
- [ ] 多租户支持
- [ ] 自定义规范文档解析（Unstructured.io）
- [ ] Ollama 本地模型支持（离线部署）
- [ ] PDF 报告导出（WeasyPrint）
- [ ] 完整审计日志 + OpenTelemetry 链路追踪

### v1.0 — 生产就绪
- [ ] 性能压测 & 调优（Celery Worker 水平扩展验证）
- [ ] Docker Compose 一键生产部署
- [ ] 监控大盘（Grafana + Loki）
- [ ] 完整测试覆盖（≥ 80%）

---

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feat/your-feature`
3. 安装开发依赖：`poetry install --with dev`
4. 确保通过所有单元测试：`poetry run pytest`
5. 确保通过代码检查：`poetry run ruff check . && poetry run mypy app/`
6. 发起 Pull Request，描述变更目的与测试方案

---

## 📄 许可证

本项目采用 [Apache License 2.0](../LICENSE) 开源协议。

---

<div align="center">
<sub>🛡️ <strong>CodeGuardian AI</strong> — 每一行代码，无论何种语言，都经得起最严格的审视。</sub>
</div>
