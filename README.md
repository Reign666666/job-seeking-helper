# PM 智投 · PM Scout

> 面向产品经理的「简历 × JD」智能求职分析工具 —— 上传简历、粘贴目标岗位 JD，即可获得 **岗位匹配度、简历优化建议、打招呼话术、面试准备建议** 四项结构化分析。

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/Framework-FastAPI-009688)](https://fastapi.tiangolo.com)
[![Frontend](https://img.shields.io/badge/Frontend-Vanilla%20JS-3b5bdb)](https://developer.mozilla.org/zh-CN/docs/Web/JavaScript)
[![Privacy](https://img.shields.io/badge/Privacy-Local%20First-important)](https://github.com/Reign666666/job-seeking-helper)
[![Deploy](https://img.shields.io/badge/Deploy-Docker%20%2F%20Render-blueviolet)](https://render.com)
[![Live Demo](https://img.shields.io/badge/Live%20Demo-Online-brightgreen)](https://job-seeking-helper.onrender.com/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## 项目简介

求职场景中，简历与目标岗位的匹配度判断、简历针对性优化、打招呼话术与面试准备，通常是耗时且低效的手工工作。本项目提供一个**本地优先（Local-First）**的 Web 工具，以 LLM 驱动的结构化分析替代人工拆解：

- **四维输出**：匹配度评分（五维模型 + 硬性否决项）、简历优化建议（关键词覆盖率 / STAR 量化改写）、打招呼话术（简洁 / 专业 / 热情 三版）、面试准备建议（预测题型 / 深挖点 / 素材清单）
- **隐私优先**：简历解析、脱敏、分析全部在本机完成；发送给大模型的仅为脱敏后的文本
- **模型无关**：兼容任意 OpenAI 标准接口（DeepSeek / 通义千问 / 智谱 GLM 等），页面内一键配置

🔗 **在线体验**：[job-seeking-helper.onrender.com](https://job-seeking-helper.onrender.com/) —— 云端演示实例，可在页面右上角「模型设置」中配置自己的 API Key 后直接使用（免费实例闲置后需等待约 1 分钟冷启动）。

项目理念受开源项目 [ai-job-search](https://github.com/MadsLorentzen/ai-job-search) 启发，针对中国大陆招聘市场与产品经理岗位语义进行了重新设计。

---

## 功能特性

| 模块 | 说明 |
| --- | --- |
| 📄 简历解析 | 支持 PDF / DOCX / TXT，浏览器本地解析，文件不落盘 |
| 🎯 岗位匹配度 | 五维评分（硬技能 / 经验 / 行业 / 方向 / 软性）+ 学历年限等一票否决项 + 差距清单 |
| ✍️ 简历优化建议 | JD 关键词覆盖率逐词分析、STAR 量化改写示例、亮点置顶与减分项建议 |
| 💬 打招呼话术 | 三版可复制话术（简洁版 ≤40 字 / 专业版 / 热情版），贴合 Boss直聘 语境 |
| 🗂️ 面试准备 | 结合目标 JD 与简历生成预测题型、被追问点与素材清单 |
| 🔒 隐私保护 | 发送 LLM 前自动脱敏（手机 / 邮箱 / 微信 / 姓名等 → 占位符），可预览待发送内容 |
| 🛡️ 诚实规则 | 分析仅基于简历真实内容，绝不虚构经历与技能 |

---

## 快速开始

### 环境要求

- Python 3.11+
- 一个 OpenAI 兼容的大模型 API Key（DeepSeek / 通义千问 / 智谱 GLM 等）

### 方式一：一键启动（Windows）

```bat
start.bat
```

首次运行会自动安装依赖，启动后自动打开浏览器访问 `http://127.0.0.1:8765`。

### 方式二：手动启动

```bash
# 1. 创建虚拟环境并安装依赖
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. 启动服务
python main.py
```

### 方式三：Docker

```bash
docker build -t pm-scout .
docker run -p 8765:8765 -e PM_SCOUT_HOST=0.0.0.0 pm-scout
```

---

## 使用指南

1. **上传简历**：支持 PDF / DOCX / TXT（仅本机解析），也可直接粘贴文本或使用内置示例数据
2. **填写目标岗位 JD**：从招聘平台复制粘贴完整 JD（职责 + 要求 + 薪资）
3. **配置模型**：点击右上角「模型设置」，下拉选择常用模型（自动填充 Base URL 与模型名）→ 填入 API Key → 保存
4. **开始分析**：点击「开始分析」，等待约 10-30 秒生成四项结果
5. **历史记录**：分析记录保存在本机 `data/history.json`，支持逐条删除与一键清空

---

## 模型配置

支持任意 OpenAI 兼容接口，在页面「模型设置」中通过下拉选择或自定义配置：

| 服务商 | Base URL | 模型示例 |
| --- | --- | --- |
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-v4-flash` / `deepseek-v4-pro` |
| 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-plus` / `qwen-max` |
| 智谱 GLM | `https://open.bigmodel.cn/api/paas/v4` | `glm-4-flash` / `glm-4-plus` |
| 其他 | 任意 OpenAI 兼容地址 | 自定义 |

**配置优先级**：UI（模型设置弹窗）＞ 环境变量 ＞ 默认值。API Key 留空时保留已保存的 Key；测试连接优先使用弹窗当前参数。

---

## 隐私与安全

- **本地优先**：简历解析、JD 解析、脱敏处理全部在本机完成，上传文件不落盘
- **发送前脱敏**：仅「脱敏后的简历文本 + JD」发送至用户自行配置的大模型服务商；手机号、邮箱、微信号、身份证、姓名等自动替换为占位符，发送前可在页面预览
- **凭证本地化**：API Key 仅保存在本机 `data/config.json`（云端部署时可通过环境变量 `PM_SCOUT_API_KEY` 注入，不进入代码仓库）
- **无跟踪**：无账号体系、无云同步、无埋点

---

## 云端部署

仓库内置 `Dockerfile` 与 `render.yaml`（Render Blueprints），支持一键部署。当前线上实例：[job-seeking-helper.onrender.com](https://job-seeking-helper.onrender.com/)（免费套餐，闲置自动休眠，首次访问需等待冷启动）：

1. Fork 本仓库并推送至自己的 GitHub
2. 在 [Render](https://render.com) 创建 Blueprint，关联仓库
3. （可选）配置环境变量：

| 环境变量 | 说明 |
| --- | --- |
| `PM_SCOUT_API_KEY` | API Key 兜底（便于跨重新部署持久化） |
| `PM_SCOUT_BASE_URL` | 可选，默认 `https://api.deepseek.com/v1` |
| `PM_SCOUT_MODEL` | 可选，默认 `deepseek-chat` |

健康检查路径为 `/api/health`。云端实例的分析历史存于临时磁盘，重启即清空。

> ⚠️ 本项目不包含任何招聘平台自动化功能，使用时应遵守各平台用户协议。

---

## 技术栈

| 层 | 技术 | 说明 |
| --- | --- | --- |
| 后端 | Python 3.11+ · FastAPI · Uvicorn | 轻量异步 Web 服务，单文件可运行 |
| 前端 | 原生 HTML / CSS / JavaScript | 单页应用，无构建步骤，零依赖 |
| LLM 接入 | httpx（OpenAI 兼容协议） | 适配 DeepSeek / 通义 / GLM 等，含错误映射与 JSON 稳健解析 |
| 文档解析 | pypdf · python-docx | 内存解析，文件不落盘 |
| 数据存储 | SQLite / JSON（本地） | API Key 与历史记录仅存本机 |
| 部署 | Docker · Render Blueprint | 跨平台运行与云端一键部署 |

---

## 项目结构

```
pm-scout/
├── main.py            # FastAPI 服务入口（含全部 API 路由）
├── llm.py             # OpenAI 兼容客户端 + JSON 稳健解析 + 错误映射
├── parsers.py         # 简历文本提取（PDF / DOCX / TXT，内存解析）
├── sanitize.py        # 脱敏引擎（手机 / 邮箱 / 微信 / 姓名等）
├── prompts.py         # LLM Prompt 模板（四段式结构化 JSON 输出）
├── storage.py         # 本地配置与历史存储（data/）
├── static/index.html  # 前端单页应用
├── docs/              # 产品设计文档（完整蓝图 / 第一期方案）
├── Dockerfile         # 云端部署镜像
├── render.yaml        # Render Blueprints 配置
├── requirements.txt
└── start.bat          # Windows 一键启动脚本
```

---

## Roadmap

| 阶段 | 方向 |
| --- | --- |
| v1.0（当前） | 简历 × JD 智能分析：匹配度 / 优化建议 / 打招呼话术 / 面试准备 |
| v2.0 | 招聘平台自动化接入（Playwright + 登录态复用，半自动人工确认模式） |
| v2.x | 多平台适配、投递追踪看板、面试模拟对话练习 |

详细设计见 `docs/`。

---

## License

[MIT](LICENSE) © 2026 pm-scout contributors

## Acknowledgments

- [ai-job-search](https://github.com/MadsLorentzen/ai-job-search) —— 项目理念与工作流设计启发
- [boss-cli (kabi-boss-cli)](https://github.com/jackwener/boss-cli) —— BOSS直聘自动化生态参考
- [OpenCLI](https://github.com/jackwener/opencli) —— 浏览器登录态复用方案参考
