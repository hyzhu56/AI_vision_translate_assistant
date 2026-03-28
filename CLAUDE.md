# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI Vision Translate Assistant — Windows 桌面悬浮工具，通过全局快捷键 `Ctrl + CapsLock` 触发区域截图，将图片发送到 Moonshot (Kimi k2.5) API 进行智能分析（英文翻译或代码解析），并在选区附近以悬浮面板展示 Markdown 格式结果。支持多开双面板、多轮追问对话、托盘设置界面。

## Commands

```bash
# 安装依赖
pip install -r requirements.txt

# 运行应用
python main.py

# 运行测试
python -m pytest tests/ -v
```

## Architecture

单体 Python 桌面应用，仅支持 Windows。核心流程：

1. **热键监听** (`core/hotkey_listener.py`) — 后台 `HotkeyThread(QThread)` 监听 `Ctrl + CapsLock`，触发时发射 `triggered` 信号
2. **全屏截图 + 框选** (`core/screenshot.py`, `ui/overlay_window.py`) — `grab_fullscreen()` 截全屏后，`OverlayWindow` 显示无边框 PyQt6 全屏覆盖层，用户拖拽框选目标区域，发射 `region_selected(QRect)` 信号
3. **图像处理** (`core/screenshot.py`) — `crop_region()` + `image_to_base64()` 将选区转 Base64，不落盘
4. **API 调用** (`core/api_client.py`) — `ApiWorker(config_store, messages)` 接受完整 messages 列表，从 `config_store` 读取 key/model（运行时读取，支持实时生效）；`ApiTestWorker` 供设置窗口连通性测试
5. **悬浮面板** (`ui/floating_panel.py`) — 每个面板独立持有 `_messages` 多轮对话历史；`start_session(image_base64)` 发起首轮；底部 `QLineEdit` 支持追问；`panel_closing` 信号通知 `PanelManager` 释放槽位
6. **多开管理** (`main.py` → `PanelManager`) — `deque` 最多 2 个面板，FIFO 淘汰；`panel_closing` 信号触发 `cleanup() + deleteLater()`
7. **设置窗口** (`ui/settings_window.py`) — 深色对话框，编辑 API Key/Base URL/Model/面板标题/系统提示词；历史提示词下拉（最多10条）；异步"测试连接"；保存写 `.env` + `settings.json` 并原地更新 `config_store`
8. **系统托盘** (`ui/tray_icon.py`) — QPainter 绘制内联图标（无外部资源），右键菜单含"⚙️ 设置"和"退出"

## Key Design Decisions

- **图片不落盘**：截图仅在内存中以 Base64 传递给 API
- **悬浮面板行为**：未固定时失焦自动隐藏；固定（图钉）后强制置顶不消失
- **悬浮面板定位**：优先显示在选区右侧，其次下方，均放不下则右下角兜底
- **托盘图标**：用 QPainter 程序化绘制，避免外部 PNG 资源依赖
- **API 模型**：`kimi-k2.5`（Moonshot 多模态视觉模型），兼容 OpenAI SDK
- **config_store**：主进程持有的单一可变 dict，传引用给所有组件，`ApiWorker.run()` 运行时读取，Settings 保存后立即生效无需重启
- **FIFO 双开**：隐藏中的面板仍占位（`deleteLater()` 才释放），第三次触发时自动淘汰最老面板
- **System Prompt**：可在设置界面修改，默认分析图片——普通英文文本给出信达雅中译，编程代码给出深度解析（逻辑、语法、关键函数），Markdown 格式输出

## File Structure

```
├── config.py                # .env + settings.json 加载/保存
├── main.py                  # 入口；PanelManager；组件连线
├── core/
│   ├── api_client.py        # ApiWorker(config_store, messages) + ApiTestWorker
│   ├── hotkey_listener.py   # HotkeyThread (pynput)
│   └── screenshot.py        # grab_fullscreen / crop_region / image_to_base64
├── ui/
│   ├── floating_panel.py    # 悬浮结果面板（多轮对话 + 追问输入）
│   ├── overlay_window.py    # 全屏框选覆盖层
│   ├── settings_window.py   # 设置对话框
│   └── tray_icon.py         # 系统托盘图标
└── tests/
    ├── test_api_client.py
    ├── test_config.py
    └── test_screenshot.py
```

## Environment Variables

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `KIMI_API_KEY` | Moonshot API 密钥（必填） | — |
| `KIMI_API_BASE` | API 端点（OpenAI 兼容地址） | `https://api.moonshot.cn/v1` |
| `KIMI_MODEL` | 模型名称 | `kimi-k2.5` |

在项目根目录创建 `.env` 文件（已加入 `.gitignore`）：

```env
KIMI_API_KEY=sk-xxxxxxxxxxxxxxxx
KIMI_API_BASE=https://api.moonshot.cn/v1
KIMI_MODEL=kimi-k2.5
```

用户界面设置（面板标题、系统提示词、历史提示词）持久化至 `settings.json`（已加入 `.gitignore`）。
