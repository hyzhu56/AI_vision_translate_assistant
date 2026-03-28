# AI Vision Translate Assistant — 设计规范

## 概述

Windows 桌面悬浮工具，通过全局快捷键 `Ctrl + CapsLock` 触发区域截图，将图片发送到 Moonshot (Kimi 2.5) 多模态 API 进行智能分析（英文翻译或代码解析），在框选区域附近以悬浮面板流式展示 Markdown 格式结果。

## 技术选型

| 项 | 选择 | 理由 |
|---|---|---|
| GUI 框架 | PyQt6 | 成熟的桌面 GUI 框架，原生支持信号槽、线程、系统托盘 |
| 热键监听 | pynput | 无需管理员权限，Windows 桌面工具事实标准 |
| 截图/图像 | Pillow | `ImageGrab.grab()` 全屏截图 + 裁剪 + Base64 转换 |
| API 客户端 | openai | 对接 Moonshot Kimi 2.5 的 OpenAI 兼容接口 |
| 配置管理 | python-dotenv | 从 `.env` 文件加载 API Key |
| 测试 | pytest + pytest-qt | 单元测试 + Qt 集成测试 |

## 架构：多线程分层

主线程运行 PyQt6 事件循环，独立守护线程用 pynput 监听全局热键，API 流式请求用 QThread 执行。组件间通过 Qt signal/slot 解耦。

### 线程模型

```
主线程 (Qt Event Loop)
├── TrayIcon          系统托盘，右键菜单退出
├── OverlayWindow     全屏遮罩框选
├── FloatingPanel     结果悬浮面板
│
守护线程
├── HotkeyThread      pynput 监听 Ctrl+CapsLock → triggered signal
│
工作线程
├── ApiWorker         openai 流式请求 → stream_chunk / stream_done / stream_error signal
```

### 数据流

1. **HotkeyThread** 检测到 `Ctrl+CapsLock` → 发射 `triggered` signal
2. **主线程** 收到 signal → `Pillow.ImageGrab.grab()` 全屏截图 → 创建并显示 `OverlayWindow`
3. **OverlayWindow** 用户框选完成 → 发射 `region_selected(QRect)` signal → 窗口自行关闭
4. **主线程** 收到 region → 裁剪截图 → Base64 编码（内存中，不落盘） → 启动 `ApiWorker`
5. **ApiWorker** 调用 `client.chat.completions.create(stream=True)` → 每个 chunk 通过 `stream_chunk(str)` signal 推送
6. **FloatingPanel** 实时追加并渲染 Markdown；流结束显示完整结果；出错显示红色提示

## 项目结构

```
AI_vision_translate_assistant/
├── main.py                  # 入口：QApplication、托盘、热键线程、信号连接
├── core/
│   ├── hotkey_listener.py   # pynput 守护线程，监听 Ctrl+CapsLock
│   ├── screenshot.py        # Pillow 全屏截图 + 裁剪 → Base64
│   └── api_client.py        # QThread，openai 流式 API 调用
├── ui/
│   ├── overlay_window.py    # 全屏无边框遮罩窗口：框选交互
│   ├── floating_panel.py    # 结果悬浮面板：极简磨砂黑风格
│   └── tray_icon.py         # 系统托盘图标 + 右键菜单
├── config.py                # python-dotenv 加载 .env 配置
├── .env                     # KIMI_API_KEY, KIMI_API_BASE
├── requirements.txt         # 项目依赖
└── tests/
    ├── test_config.py       # .env 加载测试
    ├── test_screenshot.py   # 截图裁剪 + Base64 测试
    └── test_api_client.py   # API mock 测试
```

## UI 组件规范

### OverlayWindow（全屏遮罩框选）

- **窗口属性**：`FramelessWindowHint | WindowStaysOnTopHint`，全屏显示
- **背景**：Pillow 截图作为底图，上覆 `rgba(0,0,0,0.5)` 半透明遮罩
- **框选交互**：
  - `mousePressEvent` → 记录起点坐标
  - `mouseMoveEvent` → 实时绘制矩形，框选区域透明显示原图，外部保持遮罩
  - `mouseReleaseEvent` → 发射 `region_selected(QRect)` signal，关闭自身
- **光标**：`Qt.CrossCursor`
- **取消**：`Esc` 键关闭遮罩，不触发后续操作

### FloatingPanel（悬浮结果面板）

- **窗口属性**：`FramelessWindowHint | Tool`（不出现在任务栏）
- **视觉风格 — 极简磨砂黑**：
  - 背景 `rgba(20,20,20,0.95)`
  - 圆角 12px（`setStyleSheet` + `setAttribute(WA_TranslucentBackground)`）
  - 1px `rgba(255,255,255,0.08)` 边框
  - `QGraphicsDropShadowEffect` 外阴影
- **位置逻辑**：出现在框选区域附近，优先放在选区右侧或下方，贴近但不遮挡选区；空间不足时回退到屏幕右下角
- **布局**：
  - 顶栏：左侧"AI 助手"标签 + 右侧图钉按钮、关闭按钮
  - 内容区：`QTextBrowser`，通过 `setMarkdown()` 渲染
  - 底栏：右下角 "Kimi 2.5" 灰色小字
- **图钉行为**：
  - 未固定（默认）：`focusOutEvent` 时 `hide()`
  - 已固定：添加 `WindowStaysOnTopHint`，忽略失焦事件
  - 点击图钉按钮切换状态，图标视觉反馈区分两态
- **流式渲染**：收到每个 chunk 追加文本，调用 `setMarkdown()` 重新渲染全部内容
- **错误状态**：红色文字 `"⚠ 请求失败: {error_message}"`

### TrayIcon（系统托盘）

- `QSystemTrayIcon` + `QMenu`
- 菜单项：`退出` → `QApplication.quit()`
- 图标：base64 内嵌的小 PNG 图标

## 配置管理

通过 `.env` 文件加载，使用 `python-dotenv`：

```env
KIMI_API_KEY=sk-xxxxxxxx
KIMI_API_BASE=https://api.moonshot.cn/v1
```

`config.py` 启动时校验：Key 缺失或为空时抛出明确异常并退出。

## API 调用规范

- **模型**：通过 openai 库调用 Moonshot Kimi 2.5 多模态接口
- **System Prompt**：`"你是一个智能视觉助手。请分析用户提供的图片。如果图片主体是普通英文文本，请提供信达雅的中文翻译。如果图片主体是编程代码，请提供深度的代码解析（包含编程逻辑、语法解析、关键函数分析）。使用 Markdown 格式输出。"`
- **消息格式**：`[{"role":"system","content":"..."},{"role":"user","content":[{"type":"image_url","image_url":{"url":"data:image/png;base64,..."}}]}]`
- **流式输出**：`stream=True`，逐 chunk 通过 signal 推送
- **超时**：15 秒无响应自动取消，`stream_error` 通知面板
- **错误处理**：捕获网络异常、API 错误、Key 无效等，统一通过 `stream_error(str)` signal 传递

## 测试策略

### 单元测试（pytest）

**test_config.py：**
- `.env` 存在时正确加载 `KIMI_API_KEY` 和 `KIMI_API_BASE`
- `.env` 缺失时抛出明确异常
- Key 值为空字符串时抛出异常

**test_screenshot.py：**
- `grab_fullscreen()` 返回 `PIL.Image` 且尺寸 > 0
- `crop_region(image, rect)` 裁剪结果尺寸与 rect 一致
- `image_to_base64(image)` 返回合法 base64 字符串，可解码回原图

**test_api_client.py：**
- mock `client.chat.completions.create`，验证流式 chunk 逐个通过 signal 发射
- mock 网络错误，验证 `stream_error` signal 携带正确错误信息
- mock API 返回空内容，验证优雅处理

### 集成测试（pytest-qt）

- 验证 `HotkeyThread.triggered` signal 能正确触发 `OverlayWindow` 显示
- 验证 `OverlayWindow.region_selected` signal 能正确启动 `ApiWorker`
- 验证 `ApiWorker` 的 signal 能正确驱动 `FloatingPanel` 渲染

### 手动测试

- 完整端到端流程：热键 → 截图 → 框选 → API → 面板展示
- 图钉切换 + 失焦隐藏行为
- Esc 取消框选
- 网络断开时的错误提示

## 调试支持

- `main.py --debug` 开启 `logging.DEBUG` 级别控制台日志
- 关键日志点：热键触发、框选完成(含坐标)、API 请求发出、chunk 接收计数、错误详情
- API 超时 15 秒自动取消

## 依赖清单（requirements.txt）

```
PyQt6>=6.6.0
pynput>=1.7.6
Pillow>=10.0.0
openai>=1.0.0
python-dotenv>=1.0.0
pytest>=7.0.0
pytest-qt>=4.2.0
```
