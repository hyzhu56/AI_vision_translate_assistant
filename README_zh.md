# AI Vision Translate Assistant

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/UI-PyQt6-41cd52?logo=qt)](https://www.riverbankcomputing.com/software/pyqt/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Platform](https://img.shields.io/badge/平台-Windows-0078d4?logo=windows)](https://github.com/hyzhu56/AI_vision_translate_assistant/releases)
[![Release](https://img.shields.io/github/v/release/hyzhu56/AI_vision_translate_assistant)](https://github.com/hyzhu56/AI_vision_translate_assistant/releases)

> Windows 桌面悬浮助手——通过全局快捷键框选屏幕任意区域，即可获得 AI 驱动的翻译或深度代码解析，无需切换窗口。

**简体中文** | [English](README.md)

---

## ✨ 核心特性

| 功能 | 说明 |
|---|---|
| **全局快捷键** | `Ctrl + CapsLock` — 在任何前台应用中触发 |
| **区域截图** | 拖拽框选任意区域；图像仅驻内存，绝不落盘 |
| **智能分析** | 英文文本 → 信达雅中译；代码 → 逻辑 + 语法 + 关键函数深度解析 |
| **流式输出** | 结果逐 token 流入悬浮 Markdown 面板 |
| **多轮追问** | 在同一面板继续追问，每个窗口独立维护对话历史 |
| **双开 FIFO** | 最多同时 2 个面板；触发第 3 次时自动淘汰最旧面板 |
| **托盘设置** | 随时修改 API Key、端点、模型、系统提示词，无需重启 |
| **API 历史** | 一键保存/切换多套 API 配置，最多保留 10 条 |
| **零外部资源** | 图标由 QPainter 程序化绘制，无任何内嵌图片或字体 |

---

## 🚀 快速开始

### 方式 A — 下载可执行文件（推荐）

1. 从 [Releases](https://github.com/hyzhu56/AI_vision_translate_assistant/releases) 下载最新 `.exe`
2. 在同目录创建 `.env` 文件：
   ```env
   KIMI_API_KEY=sk-你的密钥
   KIMI_API_BASE=https://api.moonshot.cn/v1
   KIMI_MODEL=kimi-k2.5
   ```
3. 双击运行——系统托盘出现图标
4. 按 `Ctrl + CapsLock`，拖拽框选区域，查看结果

### 方式 B — 源码运行

```bash
# 1. 克隆仓库
git clone https://github.com/hyzhu56/AI_vision_translate_assistant.git
cd AI_vision_translate_assistant/AI_vision_translate_assistant

# 2. 创建虚拟环境（可选但推荐）
python -m venv .venv
.venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置 API
copy .env.example .env   # 然后填入你的 API Key

# 5. 启动
python main.py
# 调试模式（输出详细日志）
python main.py --debug
```

---

## 🔌 API 兼容性

本工具使用 **OpenAI 兼容的 Chat Completions 接口 + 视觉能力**（消息中传入 `image_url`）。

| 服务商 | Base URL | 视觉模型示例 |
|---|---|---|
| **Moonshot（Kimi）** | `https://api.moonshot.cn/v1` | `kimi-k2.5` ✅ 默认 |
| **阿里云（通义千问）** | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-vl-plus` |
| **OpenAI** | `https://api.openai.com/v1` | `gpt-4o` |
| **Ollama（本地）** | `http://localhost:11434/v1` | `llava` |
| **任意 OpenAI 兼容端点** | 你的端点地址 | 任意视觉模型 |

> **注意：** 所使用的模型必须支持多模态输入（消息中 Base64 图片）。纯文本模型会拒绝图片请求。

---

## ⚙️ 配置说明

### 通过托盘图标（推荐）

右键托盘图标 → **⚙️ 设置**，在弹出的对话框中可配置：

- **API Key** — 密码遮罩显示，保存至 `.env`
- **Base URL** — API 端点地址
- **Model** — 模型名称
- **历史 API 组合** — 下拉菜单保存/恢复完整配置（最多 10 条，可单条删除）
- **面板标题** — 悬浮窗标题栏文字
- **系统提示词** — 每次会话前发送给 AI 的指令
- **历史提示词** — 快速复用之前用过的系统提示词
- **测试连接** — 异步验证当前配置是否可用

### 通过 `.env` 文件

```env
KIMI_API_KEY=sk-xxxxxxxxxxxxxxxx
KIMI_API_BASE=https://api.moonshot.cn/v1
KIMI_MODEL=kimi-k2.5
```

### 通过 `settings.json`（自动生成）

存储面板标题、系统提示词、历史提示词、API 历史记录。已加入 `.gitignore`，不会被提交。

---

## 💡 系统提示词模板

将以下任意模板粘贴到设置界面的「系统提示词」输入框：

<details>
<summary><strong>📖 英译中（默认）</strong></summary>

```
你是一个智能视觉助手。请分析用户提供的图片。
如果图片主体是普通英文文本，请提供信达雅的中文翻译。
如果图片主体是编程代码，请提供深度的代码解析
（包含编程逻辑、语法解析、关键函数分析）。
使用 Markdown 格式输出。
```
</details>

<details>
<summary><strong>🔍 代码 Review</strong></summary>

```
You are a senior software engineer. Analyze the code in the image:
1. Summarize what it does in one sentence.
2. Identify any bugs, security issues, or anti-patterns.
3. Suggest concrete improvements with examples.
Reply in the same language as the code comments, or English if unclear.
Use Markdown with code blocks.
```
</details>

<details>
<summary><strong>🖼️ UI/UX 分析</strong></summary>

```
你是一位资深 UX 设计师。请分析截图中的界面：
1. 说明界面类型及主要用途。
2. 列出最多 3 个可用性优点。
3. 列出最多 3 个可用性问题并给出改进建议。
4. 评价视觉层级与无障碍性（1-10 分并说明理由）。
使用 Markdown 格式输出。
```
</details>

<details>
<summary><strong>📚 学术阅读助手</strong></summary>

```
你是一位学术阅读助手。针对图片中的文字：
1. 用 2-3 句话总结核心论点。
2. 解释领域专用术语。
3. 如有公式或图表，进行解读。
4. 提出 2-3 个有助于深入理解的延伸问题。
用中文回复，使用 Markdown 格式。
```
</details>

---

## 🏗️ 项目架构

```
main.py              入口；PanelManager（FIFO deque，MAX=2）；组件连线
config.py            .env + settings.json 加载/保存；api_history 辅助函数
core/
  api_client.py      ApiWorker(config_store, messages) 流式调用；ApiTestWorker
  hotkey_listener.py HotkeyThread（pynput）— Ctrl+CapsLock → triggered 信号
  screenshot.py      grab_fullscreen / crop_region / image_to_base64（不落盘）
ui/
  floating_panel.py  悬浮结果面板；独立 _messages；底部追问 QLineEdit
  overlay_window.py  全屏拖拽框选覆盖层
  settings_window.py 深色设置对话框；API 配置 + 历史；异步测试；可拖动
  tray_icon.py       QPainter 内联图标；⚙️ 设置 + 退出菜单
```

**核心设计决策：**

- `config_store` 是单一共享可变 `dict`，以引用形式传给所有组件；`ApiWorker.run()` 在执行时读取，设置变更立即生效，无需重启。
- 截图不落盘，Base64 直接写入 API 消息。
- 悬浮面板无边框 + 半透明；未固定时失焦自动隐藏，固定（图钉）后强制置顶。

---

## 🧪 运行测试

```bash
python -m pytest tests/ -v
```

共 28 个单元测试，覆盖 `config.py`（设置读写、.env 更新）、`core/api_client.py`（Worker 信号）、`core/screenshot.py`（裁剪 + Base64）。

---

## 📦 从源码打包（PyInstaller）

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name AI-Vision-Assistant main.py
# 产物：dist/AI-Vision-Assistant.exe
```

---

## 📄 开源协议

MIT © 2026 [朱鸿宇 (Zhu Hongyu)](https://github.com/hyzhu56)

---

## 🙏 致谢

- [Moonshot AI](https://www.moonshot.cn/) — Kimi k2.5 多模态大模型
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) — 桌面 UI 框架
- [pynput](https://pynput.readthedocs.io/) — 全局热键监听
- [Pillow](https://python-pillow.org/) — 图像处理
- [python-openai](https://github.com/openai/openai-python) — API 客户端
