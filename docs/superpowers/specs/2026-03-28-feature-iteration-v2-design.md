# Feature Iteration v2 — Design Spec

**Date:** 2026-03-28
**Project:** AI Vision Translate Assistant
**Scope:** Settings UI, Multi-panel (FIFO), Multi-turn Follow-up, Prompt History, Custom Title

---

## 1. Overview

Three independent but architecturally connected feature modules:

| Module | Summary |
|--------|---------|
| Settings UI | Tray-accessible dialog to edit API credentials, model, panel title, and system prompt with history |
| Multi-panel (dual mode) | Up to 2 simultaneous floating panels; FIFO eviction; hidden panels still count toward limit |
| Multi-turn follow-up | Per-panel conversation history; inline follow-up input; streaming append |

---

## 2. Key Design Decisions

| Question | Decision |
|----------|---------|
| Hidden panel — does it count toward the 2-panel limit? | **Yes (占位)** — only `deleteLater()` frees a slot |
| Where to persist prompt history and custom title? | `.env` → API Key / Base URL / Model; `settings.json` → panel title / system prompt / history |
| When settings change, do already-open panels use new config? | **Yes, immediately** — shared mutable `config_store` dict read at `ApiWorker.run()` time |

---

## 3. Architecture

### 3.1 Shared Config Store

A single `dict` held in `main.py` and passed by reference to all components:

```python
config_store = {
    "api_key":       str,   # from .env  KIMI_API_KEY
    "api_base":      str,   # from .env  KIMI_API_BASE
    "model":         str,   # from .env  KIMI_MODEL  (default: "kimi-k2.5")
    "system_prompt": str,   # from settings.json
    "panel_title":   str,   # from settings.json
}
```

`ApiWorker.run()` reads `config_store` keys at execution time — not at construction time — so any settings save takes effect on the next API call without restarting.

### 3.2 Persistence Files

**`.env`** (existing, extended):
```
KIMI_API_KEY=sk-...
KIMI_API_BASE=https://api.moonshot.cn/v1
KIMI_MODEL=kimi-k2.5
```

**`settings.json`** (new, project root, added to `.gitignore`):
```json
{
  "panel_title":    "朱鸿宇的AI翻译助手",
  "system_prompt":  "你是一个智能视觉助手...",
  "prompt_history": ["prompt_a", "prompt_b"]
}
```
`prompt_history` max length: 10 (FIFO, newest first).

---

## 4. File Changes

### New files
| File | Purpose |
|------|---------|
| `ui/settings_window.py` | Settings QDialog |

### Modified files
| File | Changes |
|------|---------|
| `config.py` | Add `load_settings()`, `save_settings()`, `save_env_config()` |
| `core/api_client.py` | `ApiWorker` accepts `(config_store, messages)` instead of individual params |
| `ui/floating_panel.py` | `panel_closing` signal; `config_store` param; `start_session()`; follow-up `QLineEdit`; streaming buffer |
| `ui/tray_icon.py` | Add "⚙️ 设置" menu item; `on_settings` callback param |
| `main.py` | `config_store` dict; `PanelManager` class; wire settings window |

---

## 5. Module Designs

### 5.1 config.py — New Functions

```python
def load_settings() -> dict:
    """Read settings.json. Returns defaults if file absent."""
    # defaults: panel_title="朱鸿宇的AI翻译助手", system_prompt=SYSTEM_PROMPT, prompt_history=[]

def save_settings(data: dict) -> None:
    """Write panel_title / system_prompt / prompt_history to settings.json."""

def save_env_config(api_key: str, api_base: str, model: str) -> None:
    """Overwrite KIMI_API_KEY / KIMI_API_BASE / KIMI_MODEL in .env."""
```

`load_config()` is unchanged (backwards-compatible for existing tests). It additionally reads `KIMI_MODEL` with default `"kimi-k2.5"`.

---

### 5.2 ui/settings_window.py

**Class:** `SettingsWindow(QDialog)`

**Layout (top → bottom):**
```
[API Key    ] [•••••••••••••••] [👁 show/hide]
[Base URL   ] [https://...]
[Model      ] [kimi-k2.5     ]
─────────────────────────────
[面板标题   ] [朱鸿宇的AI翻译助手]
─────────────────────────────
历史提示词   [下拉选择...   ▼]
系统提示词
┌─────────────────────────────┐
│ (QTextEdit, 5 rows min)     │
└─────────────────────────────┘
─────────────────────────────
[测试连接]          [取消] [保存]
  ● 状态文字 (green/red inline)
```

**On open:** populate all fields from `config_store`; load `prompt_history` into QComboBox.

**Prompt history dropdown:** selecting an entry copies it into the QTextEdit.

**Test Connection (async):**
- Instantiates `ApiTestWorker(QThread)` with current field values (not yet saved)
- Sends a minimal text-only ping: `{"role":"user","content":"hi"}`
- On success → green "✓ 连接成功"; on failure → red error message
- Button disabled while test is running

**Save logic (in order):**
1. In-place update of `config_store` — all live panels immediately see new values
2. Write `.env` via `save_env_config()`
3. If current system_prompt differs from all entries in history → prepend to history list; trim to 10
4. Write `settings.json` via `save_settings()`
5. Close dialog

**Style:** matches existing dark frosted panel aesthetic (rgba(20,20,20,242) background, white/grey text).

---

### 5.3 core/api_client.py — ApiWorker Refactor

**New signature:**
```python
ApiWorker(config_store: dict, messages: list[dict])
```

`run()` reads `config_store["api_key"]`, `["api_base"]`, `["model"]` at execution time.

`messages` is the complete OpenAI-format messages array, already assembled by `FloatingPanel`.

Signals unchanged: `stream_chunk(str)`, `stream_done()`, `stream_error(str)`.

**New class: `ApiTestWorker(QThread)`**
```python
ApiTestWorker(api_key, api_base, model)
# Signals: test_ok(), test_error(str)
```
Sends a minimal non-image request; used exclusively by `SettingsWindow`.

---

### 5.4 ui/floating_panel.py — Follow-up + Multi-panel

**Constructor change:**
```python
FloatingPanel(config_store: dict)
```

**New signal:**
```python
panel_closing = pyqtSignal(object)   # emits self
```
X button now emits `panel_closing` instead of calling `hide()`.

**New attributes:**
```python
self._messages: list[dict] = []
self._streaming_buffer: str = ""     # accumulates current streaming response
self._config_store: dict             # reference to shared store
```

**New methods:**

`start_session(image_base64: str)` — called by `main.py` after region selection:
```
1. Build messages: [system, user(image)]
2. Store in self._messages
3. Call _run_worker()
```

`_run_worker()` — creates `ApiWorker(config_store, _messages)`, connects signals, starts thread.

`_on_stream_done()` — appends `{"role":"assistant","content": _streaming_buffer}` to `_messages`; clears `_streaming_buffer`.

`_on_follow_up()` — triggered by QLineEdit returnPressed:
```
1. Read + clear input field; disable input line
2. Append "**你：** {text}\n\n" to display (raw text append, not full re-render)
3. Append {"role":"user","content": text} to _messages
4. Call _run_worker()
5. On stream_done or stream_error: re-enable input line
```

**Streaming render strategy:**
- During streaming: accumulate chunks in `_streaming_buffer`; append raw text to `QTextBrowser` using `insertPlainText` for performance
- On `stream_done`: rebuild `_content_text` from full `_messages` assistant turns + user labels; call `setMarkdown()` once for final clean render

**Title dynamic update:** `show_near_region()` reads `config_store["panel_title"]` and sets the title `QLabel` text before showing.

**UI layout addition (bottom):**
```python
self._input_line = QLineEdit()
self._input_line.setPlaceholderText("继续追问...")
self._input_line.returnPressed.connect(self._on_follow_up)
```
Placed below `QTextBrowser`, above bottom bar.

---

### 5.5 main.py — PanelManager + Wiring

**`PanelManager` (inner class in main.py):**
```python
class PanelManager:
    MAX = 2

    def acquire(self, config_store) -> FloatingPanel:
        if len(self._panels) >= self.MAX:
            oldest = self._panels.popleft()
            oldest.panel_closing.disconnect()
            oldest.close()
            oldest.deleteLater()
        panel = FloatingPanel(config_store)
        panel.panel_closing.connect(self._on_closing)
        self._panels.append(panel)
        return panel

    def _on_closing(self, panel):
        if panel in self._panels:
            self._panels.remove(panel)
        panel.deleteLater()
```

**Startup flow:**
```python
config_store = {**load_config(), **load_settings()}
# load_config() returns api_key, api_base, model
# load_settings() returns system_prompt, panel_title

manager = PanelManager()
tray = create_tray_icon(app, on_settings=lambda: open_settings(config_store))
```

**`on_region_selected` new flow:**
```python
panel = manager.acquire(config_store)
panel.clear_content()
panel.show_near_region(region)
panel.start_session(image_base64)   # replaces manual ApiWorker wiring
```

---

### 5.6 ui/tray_icon.py

`create_tray_icon(app, on_settings)` — adds callback parameter.

Menu:
```
⚙️ 设置      → on_settings()
─────────
退出         → app.quit()
```

---

## 6. Data Flow Diagrams

### Settings Save Flow
```
User clicks Save
  → config_store updated in-place
  → save_env_config() writes .env
  → prepend to prompt_history if new
  → save_settings() writes settings.json
  → dialog closes
  → next ApiWorker.run() reads new config_store values
```

### New Panel + Follow-up Flow
```
Ctrl+CapsLock
  → grab_fullscreen() → OverlayWindow
  → region_selected signal
  → manager.acquire(config_store) → new FloatingPanel
  → panel.start_session(image_b64)
      → builds messages list
      → ApiWorker(config_store, messages).start()
      → stream_chunk → append to display
      → stream_done → finalize messages, re-render Markdown

User types in input box + Enter
  → _on_follow_up()
  → append user label to display
  → append to messages
  → new ApiWorker(config_store, messages).start()
  → stream appended to display
  → stream_done → finalize
```

### FIFO Eviction Flow
```
3rd Ctrl+CapsLock
  → manager.acquire() sees len == 2
  → oldest = panels.popleft()
  → oldest.close() + deleteLater()
  → new panel created, appended
```

---

## 7. Error Handling

| Scenario | Behavior |
|----------|---------|
| settings.json missing on startup | `load_settings()` returns defaults, no crash |
| .env missing KIMI_MODEL | defaults to `"kimi-k2.5"` |
| API test fails in settings | inline red error text, button re-enabled |
| Follow-up API error | `show_error()` appends red error message at bottom of existing content |
| Panel evicted mid-stream | active `ApiWorker` is stopped via `worker.quit()` + `worker.wait()` before `deleteLater()` to prevent signal-after-delete crashes |

---

## 8. Testing Notes

- Existing 13 unit tests must continue to pass unchanged
- `ApiWorker` signature change requires updating `tests/test_api_client.py` mocks
- New functions in `config.py` (`load_settings`, `save_settings`, `save_env_config`) should have unit tests with tmp file fixtures
- `ApiTestWorker` can reuse the same mock pattern as `ApiWorker` tests
