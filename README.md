# PM 智投 · 第一期

面向中国大陆互联网产品经理的本地 AI 求职工具（Web 网页版）。
仿照 [MadsLorentzen/ai-job-search](https://github.com/MadsLorentzen/ai-job-search) 的理念设计，
第一期聚焦「简历 × JD 智能分析」：上传简历 → 填写目标岗位 JD → 输出
**① 岗位匹配度 / ② 简历优化建议 / ③ 打招呼话术 / ④ 面试准备建议**。

> ⚠️ 本项目是**个人本地工具**，不涉及招聘平台自动化（自动化将于二期接入，且保持半自动模式）。
> 使用前请遵守各招聘平台用户协议；个人信息仅保存在本机。

## 快速开始

### 方式一：一键启动（Windows）

```bat
start.bat
```
服务启动后会自动打开浏览器访问 `http://127.0.0.1:8765`。

### 方式二：手动启动

```bash
# 1. 准备 Python 环境（3.11+）
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt   # Windows
# 2. 启动
.venv\Scripts\python main.py
```

## 使用流程

1. **上传简历**（PDF / DOCX / TXT，仅本机解析）——也可直接粘贴简历文本（右上角可「填入示例简历」）
2. **填写目标岗位 JD**（从 Boss直聘等平台复制粘贴）
3. 点击 **开始分析**（首次使用需先点击右上角 **⚙ 模型设置**，配置你的 API Key）
4. 查看四项结果：匹配度（五维雷达/否决项/差距）、优化建议（关键词覆盖率/STAR 改写）、
   打招呼话术（3 版可复制）、面试准备建议（预测题型/深挖点/素材清单）
5. 历史记录保存在本机 `data/history.json`，可逐条删除或一键清空

## 隐私说明

- 简历解析、JD 解析、脱敏**全部在本机完成**，文件不落盘
- 发送给大模型的仅为**脱敏后的简历文本 + JD**（手机号/邮箱/微信/姓名等自动替换为占位符），
  发送前可在页面上展开「查看即将发送给模型的内容」
- 大模型 API Key 仅保存在本机 `data/config.json`，不经过任何第三方服务器
- 无账号、无云同步、无埋点

## 模型配置

支持任意 OpenAI 兼容接口（在页面右上角「模型设置」中配置）：

| 服务商 | Base URL | 模型示例 |
|--------|----------|----------|
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat` |
| 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-plus` |
| 智谱 GLM | `https://open.bigmodel.cn/api/paas/v4` | `glm-4-flash` |
| 其他 | 任意 OpenAI 兼容地址 | — |

> 配置优先级：**UI（模型设置弹窗）＞ 环境变量 ＞ 默认值**。Base URL 与模型名在页面下拉选择后自动填充，无需配置环境变量；环境变量仅作为兜底（云端部署时可用 `PM_SCOUT_API_KEY` 提供 API Key，避免进入代码仓库）。

## 云端部署

仓库内置 Dockerfile 与 `render.yaml`（Render Blueprints）。部署后**直接在页面的「模型设置」里选择模型并填写 API Key 即可**（UI 配置优先）。可选环境变量：

| 环境变量 | 说明 |
|---|---|
| `PM_SCOUT_API_KEY` | 可选，API Key 兜底（便于跨重新部署持久化） |
| `PM_SCOUT_BASE_URL` | 可选，默认 `https://api.deepseek.com/v1` |
| `PM_SCOUT_MODEL` | 可选，默认 `deepseek-chat` |

服务端口由平台注入（Render 的 `$PORT`），健康检查路径 `/api/health`。注意：云端实例的分析历史存于临时磁盘，重启会清空（隐私更友好，如需持久化请自备存储）。

## 项目结构

```
pm-scout/
├── main.py          # FastAPI 服务入口（一键启动）
├── parsers.py       # 简历文本提取（PDF/DOCX/TXT，内存解析）
├── sanitize.py      # 脱敏引擎（手机/邮箱/微信/姓名等）
├── prompts.py       # LLM Prompt 模板（四段式 JSON schema）
├── llm.py           # OpenAI 兼容客户端 + JSON 稳健解析
├── storage.py       # 本地配置与历史存储（data/）
├── static/index.html # 前端单页应用
├── data/            # 运行时数据（config.json / history.json）
├── start.bat        # Windows 一键启动
└── requirements.txt
```

## 二期规划（不在本期）

Boss直聘自动化接入（Playwright + 登录态复用，半自动人工确认）、多平台适配、投递追踪看板等。
设计蓝图见 `docs/`（01-完整蓝图-v1.0 / 02-第一期方案-v1.1）。
