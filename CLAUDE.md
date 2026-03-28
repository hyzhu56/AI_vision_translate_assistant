# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI Vision Translate Assistant — Windows 桌面悬浮工具，通过全局快捷键 `Ctrl + CapsLock` 触发区域截图，将图片发送到 Moonshot (Kimi k2.5) API 进行智能分析（英文翻译或代码解析），并在选区附近以悬浮面板展示 Markdown 格式结果。

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
4. **API 调用** (`core/api_client.py`) — `ApiWorker(QThread)` 调用 Moonshot API（model: `kimi-k2.5`，OpenAI 兼容格式），流式返回，通过 `stream_chunk` / `stream_done` / `stream_error` 信号传递结果
5. **悬浮面板** (`ui/floating_panel.py`) — 深色磨砂圆角无边框窗口（420×360），`QTextBrowser` 渲染 Markdown；`show_near_region(QRect)` 智能定位到选区右侧/下方/备用位置；支持图钉（固定/浮动）模式
6. **系统托盘** (`ui/tray_icon.py`) — QPainter 绘制内联图标（无外部资源），右键菜单包含"退出"选项

## Key Design Decisions

- **图片不落盘**：截图仅在内存中以 Base64 传递给 API
- **悬浮面板行为**：未固定时失焦自动隐藏；固定后强制置顶不消失
- **悬浮面板定位**：优先显示在选区右侧，其次下方，均放不下则右下角兜底
- **托盘图标**：用 QPainter 程序化绘制，避免外部 PNG 资源依赖
- **API 模型**：`kimi-k2.5`（Moonshot 多模态视觉模型），兼容 OpenAI SDK
- **System Prompt**：分析图片内容——普通英文文本给出信达雅中译，编程代码给出深度解析（逻辑、语法、关键函数），输出使用 Markdown 格式

## File Structure

```
├── config.py                # .env 加载与验证
├── main.py                  # 入口，组件连线
├── core/
│   ├── api_client.py        # ApiWorker + streaming
│   ├── hotkey_listener.py   # HotkeyThread (pynput)
│   └── screenshot.py        # grab_fullscreen / crop_region / image_to_base64
├── ui/
│   ├── floating_panel.py    # 悬浮结果面板
│   ├── overlay_window.py    # 全屏框选覆盖层
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

在项目根目录创建 `.env` 文件（已加入 `.gitignore`）：

```env
KIMI_API_KEY=sk-xxxxxxxxxxxxxxxx
KIMI_API_BASE=https://api.moonshot.cn/v1
```
