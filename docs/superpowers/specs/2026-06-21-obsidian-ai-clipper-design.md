# Obsidian AI Clipper 设计文档

**日期：** 2026-06-21  
**版本：** 1.0  
**状态：** 待实现

---

## 1. 项目目标

构建一套个人网页剪藏系统：

- 通过 Chrome 扩展将当前网页 URL 发送至服务端。
- 服务端抓取网页内容，使用 AI（Kimi Code / kimi2.6）提取核心内容并生成 Markdown。
- 将 Markdown 与相关图片、代码附件保存到 Obsidian Vault，按主题/标签自动分类归档。
- 提供安全的 HTTPS Web 界面，方便浏览、搜索和管理已剪藏内容。
- 内容必须被可靠处理，任何阶段的失败都不应导致内容被静默丢弃。

---

## 2. 核心决策

| 项目 | 选择 |
|---|---|
| 服务端技术栈 | Python + FastAPI |
| 部署方式 | 公网服务器 / 云主机 |
| Vault 归档方式 | 按主题/标签自动分类 |
| AI 模型 | Kimi Code 平台，kimi2.6 |
| 浏览器扩展 | 仅支持 Chrome，只发送 URL |
| 网页抓取 | 静态优先（httpx），失败回退 Playwright 动态渲染 |
| Web 浏览 | 剪藏管理页 + 单篇 Markdown 渲染 + 搜索/过滤 |
| 认证安全 | API Key + 速率限制 + IP 白名单 + 失败日志 |
| HTTPS 证书 | Let's Encrypt（PEM），自动续期；同时支持 p12 证书挂载 |
| 内容提取 | 专用库提取 + Kimi 整理/分类/摘要 |
| 图片处理 | 下载到本地，与 Markdown 同目录 |
| 保存流程 | 完全自动保存 |
| 请求超时 | 3 分钟 |

---

## 3. 系统架构

```text
┌─────────────────┐     HTTPS/POST /api/clip      ┌─────────────────────────────┐
│  Chrome         │ ─────────────────────────────▶│  FastAPI Service (Docker)   │
│  Extension      │   Header: Authorization:      │                             │
│  (sends URL)    │          Bearer <API_KEY>     │  ┌───────────────────────┐  │
└─────────────────┘                               │  │ Auth & Rate Limit     │  │
                                                  │  └───────────┬───────────┘  │
                                                  │              ▼              │
                                                  │  ┌───────────────────────┐  │
                                                  │  │ URL Validation        │  │
                                                  │  └───────────┬───────────┘  │
                                                  │              ▼              │
                                                  │  ┌───────────────────────┐  │
                                                  │  │ 1. Persist Job        │  │
                                                  │  │    (SQLite queue)     │  │
                                                  │  └───────────┬───────────┘  │
                                                  │              ▼              │
                                                  │  ┌───────────────────────┐  │
                                                  │  │ 2. Fetch Web Page     │  │
                                                  │  │    httpx → Playwright │  │
                                                  │  └───────────┬───────────┘  │
                                                  │              ▼              │
                                                  │  ┌───────────────────────┐  │
                                                  │  │ 3. Extract Content    │  │
                                                  │  │    trafilatura + BS4  │  │
                                                  │  └───────────┬───────────┘  │
                                                  │              ▼              │
                                                  │  ┌───────────────────────┐  │
                                                  │  │ 4. AI Process (Kimi)  │  │
                                                  │  │    classify/summarize │  │
                                                  │  └───────────┬───────────┘  │
                                                  │              ▼              │
                                                  │  ┌───────────────────────┐  │
                                                  │  │ 5. Save to Vault      │  │
                                                  │  │    Markdown + images  │  │
                                                  │  └───────────┬───────────┘  │
                                                  │              ▼              │
                                                  │  ┌───────────────────────┐  │
                                                  │  │ 6. Update Job Status  │  │
                                                  │  │    success / failed   │  │
                                                  │  └───────────────────────┘  │
                                                  └─────────────────────────────┘
                                                                │
                                                                ▼
                                                  ┌─────────────────────────────┐
                                                  │  Web UI: /web/clips         │
                                                  │  list / search / filter     │
                                                  │  /web/clips/<id>            │
                                                  └─────────────────────────────┘
```

---

## 4. 模块说明

### 4.1 Chrome 扩展

- 点击扩展图标，获取当前页面 URL。
- 发送 `POST /api/clip` 到服务端，请求头携带 API Key。
- 弹出面板显示发送状态、返回的 `job_id` 和简要错误提示。
- 配置页：服务端地址、API Key。
- 可选：右键菜单"保存到 Vault"。

扩展权限：

- `activeTab`
- `storage`
- `contextMenus`（可选）

### 4.2 认证与接口匹配

- 扩展请求必须包含：
  - `Authorization: Bearer <API_KEY>`
  - `Content-Type: application/json`
  - `X-Client-Version: <version>`
- 服务端校验：
  - API Key 有效
  - 客户端版本在支持范围内
  - 请求体严格符合 JSON Schema
- 任何不匹配直接返回 400/401，不处理。

### 4.3 任务队列与持久化

使用 SQLite 持久化所有任务，确保内容不丢失。

核心任务字段：

| 字段 | 说明 |
|---|---|
| `id` | 唯一任务 ID |
| `url` | 原始 URL |
| `status` | pending / fetching / extracting / ai_processing / saving / done / failed |
| `retry_count` | 已重试次数 |
| `max_retries` | 最大重试次数（默认 3） |
| `stage` | 当前处理阶段 |
| `last_error` | 最后一次错误信息 |
| `raw_html_path` | 原始 HTML 暂存路径 |
| `extracted_json_path` | 提取结果暂存路径 |
| `vault_path` | 最终 Markdown 保存路径 |
| `created_at` / `updated_at` | 时间戳 |

状态流转：

```
pending → fetching → extracting → ai_processing → saving → done
   ↓          ↓           ↓              ↓           ↓
 failed    failed      failed         failed       failed
```

失败任务保留在数据库中，可通过 Web UI 查看原因并手动触发重试。

### 4.4 网页抓取

- 首先使用 `httpx` 进行静态抓取，超时 3 分钟。
- 静态抓取失败或内容为空/过短时，回退到 Playwright 动态渲染。
- 抓取失败自动重试，最多 3 次，使用指数退避。
- 禁止访问内网地址、私有 IP、非 http/https 协议。
- 原始 HTML 暂存到本地，供后续重试和调试。

### 4.5 内容提取

- 使用 `trafilatura` 提取正文。
- 使用 `BeautifulSoup` 辅助提取图片、代码块、标题、作者、发布时间等。
- 提取结果保存为 JSON，供 AI 处理。
- 如果提取内容为空或过短，标记为 `needs_review`，不丢弃。

### 4.6 AI 处理（Kimi Code）

输入给 Kimi 的 JSON：

```json
{
  "url": "https://example.com/article",
  "title": "原始标题",
  "domain": "example.com",
  "content": "正文纯文本（已清洗）",
  "images": [
    {"src": "https://...", "alt": "..."}
  ],
  "code_blocks": [
    {"language": "python", "code": "..."}
  ]
}
```

要求 Kimi 返回：

```json
{
  "title": "优化后的标题",
  "category": "人工智能",
  "tags": ["AI", "大模型", "Kimi"],
  "summary": "3-5 句话摘要",
  "content_markdown": "正文 Markdown（保留图片引用和代码块）",
  "author": "作者名",
  "published_at": "2026-06-20"
}
```

失败处理：

- Kimi API 调用失败：指数退避重试 3 次。
- 返回非标准 JSON：尝试修复解析；无法修复时使用原始提取内容生成基础 Markdown。
- 分类不明确：放入 `未分类/`。

Prompt 模板放在 `prompts/clip.md`，支持热更新。

### 4.7 文件存储

Vault 目录结构：

```
/Vault/
├── Clips/
│   ├── 人工智能/
│   │   ├── 2026-06-21-<slug>/
│   │   │   ├── index.md
│   │   │   ├── image_1.png
│   │   │   ├── image_2.jpg
│   │   │   └── code_snippet_1.py
│   │   └── ...
│   ├── 编程开发/
│   │   └── ...
│   └── 未分类/
│       └── ...
```

- 每个剪藏一个独立目录，`index.md` 为正文。
- 图片、代码附件与 Markdown 同目录。
- 目录名安全处理，去除非法字符，限制长度。
- 文件写入采用临时文件 + 原子重命名。
- 图片下载失败时，Markdown 中保留原始 URL 作为 fallback。
- 目录已存在时追加时间戳或序号，避免覆盖。

Markdown frontmatter 示例：

```markdown
---
title: "文章标题"
source_url: "https://example.com/article"
domain: "example.com"
category: "人工智能"
tags:
  - "AI"
  - "大模型"
summary: "这是 AI 生成的摘要..."
author: "作者名"
published_at: "2026-06-20"
clipped_at: "2026-06-21T12:30:00Z"
job_id: "clip_abc123"
status: "done"
---
```

### 4.8 Web 浏览界面

路由：

- `/web` — 剪藏列表
- `/web/clips/<id>` — 单篇查看
- `/web/failed` — 失败任务列表，支持重新处理
- `/web/queue` — 处理中队列状态

功能：

- 列表页：按状态、分类、标签、时间过滤，支持关键词搜索。
- 单篇页：渲染 Markdown，显示元数据。
- 失败任务页：查看错误原因，一键重新处理。
- 队列页：查看当前处理中任务数量、阶段分布。

### 4.9 安全设计

- 认证：API Key，失败统一返回 401，记录失败日志。
- 速率限制：单 IP 10 次/分钟，全局 100 次/分钟，失败认证 IP 连续 5 次失败封禁 1 小时。
- URL 过滤：禁止内网、私有 IP、非 http/https。
- 请求体大小限制：扩展请求 ≤ 1KB。
- 抓取限制：Playwright 沙箱运行，禁止访问内网。
- 图片下载限制：单图 ≤ 10MB，MIME 白名单 image/*。
- XSS 防护：Web 渲染使用安全模板，过滤 AI 输出。
- HTTPS：生产环境使用 Let's Encrypt 自动申请和续期；如用户已有 p12 证书，可直接挂载使用。
- 容器安全：Docker 以非 root 运行，最小挂载。
- 安全响应头：HSTS、CSP、X-Frame-Options、X-Content-Type-Options。

---

## 5. 接口定义

### 5.1 POST /api/clip

**请求：**

```http
POST /api/clip
Content-Type: application/json
Authorization: Bearer <API_KEY>
X-Client-Version: 1.0.0

{
  "url": "https://example.com/article",
  "submitted_at": "2026-06-21T12:30:00Z",
  "client_version": "1.0.0"
}
```

**成功响应（202 Accepted）：**

```json
{
  "job_id": "clip_abc123",
  "status": "pending",
  "message": "已接收，正在后台处理"
}
```

**失败响应：**

- `400 Bad Request`：请求体格式错误
- `401 Unauthorized`：API Key 无效
- `429 Too Many Requests`：速率限制
- `409 Conflict`：同一 URL 24 小时内已处理

### 5.2 GET /api/jobs/{job_id}

查询任务状态。

**响应：**

```json
{
  "job_id": "clip_abc123",
  "status": "done",
  "stage": "saving",
  "retry_count": 0,
  "vault_path": "Clips/人工智能/2026-06-21-example-article/index.md",
  "created_at": "2026-06-21T12:30:00Z",
  "updated_at": "2026-06-21T12:31:15Z"
}
```

---

## 6. 部署方案

### 6.1 运行环境

- Docker + docker-compose
- Python 3.12+
- 挂载 Obsidian Vault 目录到容器
- 挂载 SQLite 数据库持久化目录

### 6.2 环境变量

| 变量 | 说明 |
|---|---|
| `API_KEYS` | 逗号分隔的 API Key 列表 |
| `KIMI_API_KEY` | Kimi Code API Key |
| `KIMI_MODEL` | 模型名称，默认 `kimi2.6` |
| `VAULT_PATH` | Obsidian Vault 根目录 |
| `DATABASE_PATH` | SQLite 数据库路径 |
| `LOG_LEVEL` | 日志级别，默认 `INFO` |
| `RATE_LIMIT_IP` | 单 IP 速率限制 |
| `RATE_LIMIT_GLOBAL` | 全局速率限制 |
| `MAX_RETRY` | 任务最大重试次数 |

### 6.3 HTTPS

- 优先使用 Let's Encrypt 自动申请和续期 PEM 证书。
- 如用户提供 p12 格式证书，服务支持直接挂载 p12 文件并提供 HTTPS。
- 生产环境通过 Nginx 或 Traefik 反向代理到 FastAPI 服务。
- 若暂时无域名，可用自签名证书作为测试方案。

---

## 7. 错误处理与可靠性

### 7.1 不丢弃内容的保证

1. 任务一接收即写入 SQLite。
2. 每个阶段失败都会更新状态为 `failed` 并记录错误。
3. 原始 HTML、提取结果等中间产物持久化到本地。
4. 失败任务可通过 Web UI 手动重试。
5. AI 处理最终失败时，仍保存原始提取内容到 Vault，并标记 `ai_failed`。

### 7.2 重试策略

- 抓取阶段：最多 3 次，指数退避。
- AI 调用阶段：最多 3 次，指数退避。
- 保存阶段：最多 3 次。

### 7.3 监控与日志

- 记录所有 API 请求（不含敏感信息）。
- 记录认证失败尝试。
- 记录任务状态流转。
- 提供 `/health` 健康检查接口。

---

## 8. 后续可扩展项

以下内容不在首版实现范围，但架构预留扩展空间：

- 支持 Firefox/Edge 扩展。
- 扩展端预览/编辑后再保存。
- Web UI 用户登录与多用户支持。
- 图片压缩、WebP 转换、缩略图生成。
- 全文搜索（如集成 Elasticsearch/Meilisearch）。
- 任务队列升级到 Redis + arq。
- 多语言内容识别与分类。
- 与 Obsidian 官方同步服务集成。

---

## 9. 待确认事项

- [ ] 是否需要预定义分类列表？
- [ ] Obsidian Vault 是否已存在，服务端是否有写权限？
- [ ] 服务器是否已有域名和 80/443 端口可用？
- [ ] 是否需要邮件/通知告警（如连续失败任务过多）？

---

## 10. 变更记录

| 日期 | 版本 | 说明 |
|---|---|---|
| 2026-06-21 | 1.0 | 初始版本 |
