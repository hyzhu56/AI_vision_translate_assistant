# AI Vision Translate Assistant

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/UI-PyQt6-41cd52?logo=qt)](https://www.riverbankcomputing.com/software/pyqt/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078d4?logo=windows)](https://github.com/hyzhu56/AI_vision_translate_assistant/releases)
[![Release](https://img.shields.io/github/v/release/hyzhu56/AI_vision_translate_assistant)](https://github.com/hyzhu56/AI_vision_translate_assistant/releases)

> A Windows desktop floating assistant that captures any screen region with a global hotkey and delivers AI-powered translation or deep code analysis in a sleek overlay — without switching windows.

[简体中文](README_zh.md) | **English**

---

## ✨ Highlights

| Feature | Details |
|---|---|
| **Global Hotkey** | `Ctrl + CapsLock` — trigger from any foreground app |
| **Region Capture** | Drag-select any area; image stays in memory, never touches disk |
| **Smart Analysis** | English prose → fluent Chinese translation; code → deep logic & syntax breakdown |
| **Streaming Output** | Results stream token-by-token into a floating Markdown panel |
| **Multi-turn Chat** | Ask follow-up questions in the same panel; full conversation history per window |
| **Dual-panel FIFO** | Up to 2 panels simultaneously; oldest auto-closes when a third is triggered |
| **Tray Settings** | Change API key, endpoint, model, and system prompt without restarting |
| **API History** | Save and switch between multiple API configurations in one click |
| **No External Assets** | Icon drawn with QPainter; zero bundled images or fonts |

---

## 🚀 Quick Start

### Option A — Download Binary (Recommended)

1. Download the latest `.exe` from [Releases](https://github.com/hyzhu56/AI_vision_translate_assistant/releases)
2. Create a `.env` file in the same folder:
   ```env
   KIMI_API_KEY=sk-your-key-here
   KIMI_API_BASE=https://api.moonshot.cn/v1
   KIMI_MODEL=kimi-k2.5
   ```
3. Double-click the executable — a tray icon appears in the system tray
4. Press `Ctrl + CapsLock`, drag to select a region, and see the result

### Option B — Run from Source

```bash
# 1. Clone
git clone https://github.com/hyzhu56/AI_vision_translate_assistant.git
cd AI_vision_translate_assistant/AI_vision_translate_assistant

# 2. Create virtual environment (optional but recommended)
python -m venv .venv
.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure
copy .env.example .env   # then edit with your API key

# 5. Launch
python main.py
# Add --debug for verbose logging
python main.py --debug
```

---

## 🔌 API Compatibility

The assistant uses the **OpenAI-compatible Chat Completions API with Vision** (`image_url` in messages).

| Provider | Base URL | Vision Model Example |
|---|---|---|
| **Moonshot (Kimi)** | `https://api.moonshot.cn/v1` | `kimi-k2.5` ✅ default |
| **Alibaba Cloud (Qwen)** | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-vl-plus` |
| **OpenAI** | `https://api.openai.com/v1` | `gpt-4o` |
| **Ollama (local)** | `http://localhost:11434/v1` | `llava` |
| **Any OpenAI-compatible** | your endpoint | any vision model |

> **Note:** The model must support multimodal/vision input (Base64 image in `image_url`). Text-only models will reject image requests.

---

## ⚙️ Configuration

### Via Tray Icon (recommended)

Right-click the tray icon → **⚙️ Settings** to open the settings dialog:

- **API Key** — masked input, saved to `.env`
- **Base URL** — API endpoint
- **Model** — model name
- **API History** — drop-down to save/restore full API configurations (max 10)
- **Panel Title** — floating window title bar text
- **System Prompt** — instruction sent to the AI before every session
- **Prompt History** — reuse previous system prompts
- **Test Connection** — async ping to verify credentials before saving

### Via `.env` File

```env
KIMI_API_KEY=sk-xxxxxxxxxxxxxxxx
KIMI_API_BASE=https://api.moonshot.cn/v1
KIMI_MODEL=kimi-k2.5
```

### Via `settings.json` (auto-generated)

Stores panel title, system prompt, prompt history, and API configuration history. Gitignored by default.

---

## 💡 System Prompt Templates

Paste any of these into the **System Prompt** field in Settings:

<details>
<summary><strong>📖 English Translation (default)</strong></summary>

```
你是一个智能视觉助手。请分析用户提供的图片。
如果图片主体是普通英文文本，请提供信达雅的中文翻译。
如果图片主体是编程代码，请提供深度的代码解析
（包含编程逻辑、语法解析、关键函数分析）。
使用 Markdown 格式输出。
```
</details>

<details>
<summary><strong>🔍 Code Review</strong></summary>

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
<summary><strong>🖼️ UI/UX Analysis</strong></summary>

```
You are a UX designer. Analyze the UI screenshot:
1. Identify the type of interface and its main purpose.
2. List usability strengths (max 3).
3. List usability issues and suggest fixes (max 3).
4. Rate visual hierarchy and accessibility (1–10 with reason).
Use Markdown.
```
</details>

<details>
<summary><strong>📚 Academic Paper Helper</strong></summary>

```
You are an academic reading assistant. For the text in the image:
1. Summarize the core argument in 2–3 sentences.
2. Define any domain-specific terms.
3. Explain key formulas or figures if present.
4. Suggest 2–3 follow-up questions for deeper understanding.
Reply in Chinese. Use Markdown.
```
</details>

---

## 🏗️ Architecture

```
main.py              Entry point; PanelManager (FIFO deque, MAX=2); component wiring
config.py            .env + settings.json load/save; api_history helpers
core/
  api_client.py      ApiWorker(config_store, messages) streaming; ApiTestWorker
  hotkey_listener.py HotkeyThread (pynput) — Ctrl+CapsLock → triggered signal
  screenshot.py      grab_fullscreen / crop_region / image_to_base64 (no disk write)
ui/
  floating_panel.py  Floating result panel; owns _messages; follow-up QLineEdit
  overlay_window.py  Fullscreen drag-select overlay
  settings_window.py Dark dialog; API config + history; async test; drag to move
  tray_icon.py       QPainter inline icon; ⚙️ Settings + Exit menu
```

**Key design decisions:**

- `config_store` is a single shared mutable `dict`; workers read it at `run()` time so settings changes apply immediately without restart.
- Screenshots never touch disk — Base64 is passed directly in the API message.
- The floating panel is frameless + translucent; it auto-hides on focus loss unless pinned.

---

## 🧪 Running Tests

```bash
python -m pytest tests/ -v
```

All 28 unit tests cover `config.py` (settings CRUD, env rewrite), `core/api_client.py` (worker signals), and `core/screenshot.py` (crop / base64).

---

## 📦 Building from Source (PyInstaller)

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name AI-Vision-Assistant main.py
# Output: dist/AI-Vision-Assistant.exe
```

---

## 📄 License

MIT © 2026 [朱鸿宇 (Zhu Hongyu)](https://github.com/hyzhu56)

---

## 🙏 Acknowledgements

- [Moonshot AI](https://www.moonshot.cn/) — Kimi k2.5 multimodal model
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) — Desktop UI framework
- [pynput](https://pynput.readthedocs.io/) — Global hotkey listener
- [Pillow](https://python-pillow.org/) — Image processing
- [python-openai](https://github.com/openai/openai-python) — API client
