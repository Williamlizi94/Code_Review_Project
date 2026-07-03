<div align="center">

# 🛡️ CodeGuardian AI

### AI-Powered Code Review Agent for Enterprises & Teams

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-latest-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-ReAct_Agent-1C3C3C?style=flat-square&logo=chainlink&logoColor=white)](https://langchain.com)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--5.4--mini-412991?style=flat-square&logo=openai&logoColor=white)](https://openai.com)
[![Semgrep](https://img.shields.io/badge/Semgrep-30%2B_Languages-20B2AA?style=flat-square)](https://semgrep.dev)
[![License](https://img.shields.io/badge/License-Apache%202.0-E25822?style=flat-square)](LICENSE)

</div>

---

**CodeGuardian AI** is an intelligent code review agent that automatically analyzes code across **30+ programming languages**, combining static analysis with large language model reasoning to surface actionable bugs, security vulnerabilities, and style violations — and suggest exactly how to fix them.

## ✨ What It Does

| | Feature |
|---|---|
| 🔍 | Submit a Git repo, directory, file, or raw code snippet for review |
| ⚡ | Run Semgrep, Tree-sitter, and language-specific linters in parallel |
| 🧠 | Use a LangGraph AI Agent (OpenAI GPT-5.4-mini) to reason over findings and generate fix suggestions |
| 📚 | Augment analysis with RAG retrieval of similar historical defects from your team's knowledge base |
| 📊 | Produce structured HTML, Markdown, or PDF reports with precise line-level location and Diff highlights |
| 🔀 | Integrate with GitHub, GitLab, and Bitbucket — writing results back as inline PR/MR comments |
| 🔄 | Plug into CI/CD pipelines via REST API and Webhooks, with configurable quality gates |

## 🌐 Supported Languages

`Python` `Java` `TypeScript` `JavaScript` `Go` `Rust` `C` `C++` `Ruby` `PHP` `Swift` `Kotlin` and more.

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Web API | Python 3.12 + FastAPI |
| AI Agent | LangChain + LangGraph |
| Static Analysis | Semgrep + Tree-sitter |
| RAG | LlamaIndex + pgvector |
| Task Queue | Celery + Redis |

## 📂 Documentation

Detailed design documents are located in the [Design/](Design/) folder.

| Document | Description |
|---|---|
| [design_version1.md](Design/design_version1.md) | Architecture & Feature Spec (English) |
| [design_version1_cn.md](Design/design_version1_cn.md) | 架构与功能设计文档（中文） |

## 📄 License

[Apache License 2.0](LICENSE)

---

<div align="center">
<sub>🛡️ <strong>CodeGuardian AI</strong> — Every line of code, in every language, held to the highest standard.</sub>
</div>
