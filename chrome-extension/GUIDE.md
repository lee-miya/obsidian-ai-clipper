# Chrome Extension 使用指南

## 安装

1. 打开 Chrome 浏览器，地址栏输入 `chrome://extensions/`
2. 打开右上角 **开发者模式** 开关
3. 点击左上角 **加载已解压的扩展程序**
4. 选择项目中的 `chrome-extension/` 目录
5. 扩展图标会出现在浏览器工具栏

## 配置

1. 点击浏览器工具栏中的扩展图标，如果提示未配置，点击 **设置**
2. 或在地址栏输入 `chrome://extensions/`，找到 "Obsidian AI Clipper"，点击 **详情 → 扩展程序选项**
3. 填写以下信息：
   - **Server URL**：服务端地址，例如 `https://clipper.example.com` 或 `http://192.168.1.100:8000`
   - **API Key**：运行 `scripts/deploy.sh` 时自动生成的 Authorization Key（服务端 `.env` 中的 `API_KEYS` 值）
4. 点击 **Save** 保存配置

## 使用

1. 浏览到想要保存的网页
2. 点击浏览器工具栏中的 **Obsidian AI Clipper** 图标
3. 在弹出的面板中点击 **Save to Vault** 按钮
4. 稍等片刻，面板会显示保存状态：
   - `Saved. Job: clip_xxxxxxxx` — 保存成功，正在后台处理
   - `Error: ...` — 发送失败，请检查网络和服务端配置

## 查看结果

打开浏览器访问服务端 Web 界面（例如 `http://127.0.0.1:8000/web`）：

- **剪藏列表** — 查看所有已处理的页面
- **失败任务** — 查看处理失败的任务及错误信息
- **队列** — 查看等待中的任务数量

处理完成后，Markdown 文件会保存到服务端配置的 Obsidian Vault 目录中，按 AI 自动分类的目录结构存放。

## 注意事项

- 服务端必须在扩展所在的网络环境中可达（内网或公网均可）
- 如果使用自签名证书或 HTTP，请确保 Chrome 允许不安全连接（仅限测试环境）
- 扩展仅发送当前页面 URL，不读取页面内容
- 每个 URL 24 小时内仅处理一次，重复发送会返回 409 错误
