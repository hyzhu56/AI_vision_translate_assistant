import logging

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from config import save_env_config, save_settings
from core.api_client import ApiTestWorker

logger = logging.getLogger(__name__)

_FIELD_STYLE = """
    QLineEdit, QTextEdit {
        background: rgba(255,255,255,8);
        border: 1px solid rgba(255,255,255,20);
        border-radius: 6px;
        color: #d0d0d0;
        padding: 4px 8px;
        font-size: 12px;
    }
    QLineEdit:focus, QTextEdit:focus {
        border: 1px solid rgba(91,143,249,150);
    }
"""

_LABEL_STYLE = "color: #999999; font-size: 12px;"


class SettingsWindow(QDialog):
    """Dark-themed settings dialog — reads/writes config_store, .env, settings.json."""

    def __init__(self, config_store: dict, parent=None):
        super().__init__(parent)
        self._config_store = config_store
        self._test_worker: ApiTestWorker | None = None

        self.setWindowTitle("设置")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(500)

        self._setup_ui()
        self._populate()
        self._setup_shadow()

    # ── UI construction ───────────────────────────────────────────────────────

    def _setup_ui(self):
        self._container = QWidget(self)
        self._container.setObjectName("sw_container")
        self._container.setStyleSheet("""
            #sw_container {
                background-color: rgba(28, 28, 28, 252);
                border-radius: 12px;
                border: 1px solid rgba(255,255,255,30);
            }
        """)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self._container)

        lay = QVBoxLayout(self._container)
        lay.setContentsMargins(22, 18, 22, 18)
        lay.setSpacing(10)

        # Title bar
        tb = QHBoxLayout()
        title = QLabel("⚙️  设置")
        title.setStyleSheet("color: #cccccc; font-size: 14px; font-weight: bold;")
        tb.addWidget(title)
        tb.addStretch()
        x_btn = QPushButton("✕")
        x_btn.setFixedSize(24, 24)
        x_btn.setStyleSheet(
            "QPushButton{background:transparent;border:none;color:#666;font-size:13px;}"
            "QPushButton:hover{color:#aaa;}"
        )
        x_btn.clicked.connect(self.reject)
        tb.addWidget(x_btn)
        lay.addLayout(tb)
        lay.addWidget(self._sep())

        # API Key row (with eye toggle)
        key_row = QHBoxLayout()
        key_lbl = QLabel("API Key")
        key_lbl.setFixedWidth(90)
        key_lbl.setStyleSheet(_LABEL_STYLE)
        self._key_edit = QLineEdit()
        self._key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._key_edit.setStyleSheet(_FIELD_STYLE)
        eye_btn = QPushButton("👁")
        eye_btn.setFixedSize(28, 28)
        eye_btn.setCheckable(True)
        eye_btn.setStyleSheet(
            "QPushButton{background:transparent;border:none;font-size:13px;color:#555;}"
            "QPushButton:checked{color:#aaa;}"
        )
        eye_btn.toggled.connect(
            lambda on: self._key_edit.setEchoMode(
                QLineEdit.EchoMode.Normal if on else QLineEdit.EchoMode.Password
            )
        )
        key_row.addWidget(key_lbl)
        key_row.addWidget(self._key_edit)
        key_row.addWidget(eye_btn)
        lay.addLayout(key_row)

        # Base URL
        self._base_edit = QLineEdit()
        self._base_edit.setStyleSheet(_FIELD_STYLE)
        lay.addLayout(self._labeled_row("Base URL", self._base_edit))

        # Model
        self._model_edit = QLineEdit()
        self._model_edit.setStyleSheet(_FIELD_STYLE)
        lay.addLayout(self._labeled_row("Model", self._model_edit))
        lay.addWidget(self._sep())

        # Panel title
        self._panel_title_edit = QLineEdit()
        self._panel_title_edit.setStyleSheet(_FIELD_STYLE)
        lay.addLayout(self._labeled_row("面板标题", self._panel_title_edit))
        lay.addWidget(self._sep())

        # Prompt history dropdown
        hist_row = QHBoxLayout()
        hist_lbl = QLabel("历史提示词")
        hist_lbl.setStyleSheet(_LABEL_STYLE)
        hist_row.addWidget(hist_lbl)
        self._history_combo = QComboBox()
        self._history_combo.setStyleSheet("""
            QComboBox {
                background: rgba(255,255,255,8);
                border: 1px solid rgba(255,255,255,20);
                border-radius: 6px;
                color: #d0d0d0;
                padding: 4px 8px;
                font-size: 12px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background: rgba(40,40,40,252);
                color: #d0d0d0;
                selection-background-color: rgba(91,143,249,100);
                border: 1px solid rgba(255,255,255,20);
            }
        """)
        self._history_combo.currentIndexChanged.connect(self._on_history_selected)
        hist_row.addWidget(self._history_combo)
        lay.addLayout(hist_row)

        # System prompt label + text area
        prompt_lbl = QLabel("系统提示词")
        prompt_lbl.setStyleSheet(_LABEL_STYLE)
        lay.addWidget(prompt_lbl)
        self._prompt_edit = QTextEdit()
        self._prompt_edit.setMinimumHeight(100)
        self._prompt_edit.setMaximumHeight(150)
        self._prompt_edit.setStyleSheet(_FIELD_STYLE)
        lay.addWidget(self._prompt_edit)
        lay.addWidget(self._sep())

        # Status label
        self._status_lbl = QLabel("")
        self._status_lbl.setStyleSheet("font-size: 11px; color: #666666;")
        self._status_lbl.setWordWrap(True)
        lay.addWidget(self._status_lbl)

        # Button row
        btn_row = QHBoxLayout()
        self._test_btn = QPushButton("测试连接")
        self._test_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,10);
                border: 1px solid rgba(255,255,255,25);
                border-radius: 6px; color: #aaaaaa;
                padding: 6px 14px; font-size: 12px;
            }
            QPushButton:hover { background: rgba(255,255,255,15); color: #cccccc; }
            QPushButton:disabled { color: #444444; }
        """)
        self._test_btn.clicked.connect(self._on_test)
        btn_row.addWidget(self._test_btn)
        btn_row.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: 1px solid rgba(255,255,255,20);
                border-radius: 6px; color: #888888;
                padding: 6px 14px; font-size: 12px;
            }
            QPushButton:hover { color: #aaaaaa; }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        save_btn = QPushButton("保存")
        save_btn.setStyleSheet("""
            QPushButton {
                background: rgba(91,143,249,180);
                border: none; border-radius: 6px;
                color: #ffffff; padding: 6px 20px;
                font-size: 12px; font-weight: bold;
            }
            QPushButton:hover { background: rgba(91,143,249,220); }
        """)
        save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(save_btn)
        lay.addLayout(btn_row)

    def _setup_shadow(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(0, 4)
        self._container.setGraphicsEffect(shadow)

    @staticmethod
    def _sep() -> QWidget:
        w = QWidget()
        w.setFixedHeight(1)
        w.setStyleSheet("background-color: rgba(255,255,255,18);")
        return w

    @staticmethod
    def _labeled_row(label_text: str, widget: QWidget) -> QHBoxLayout:
        row = QHBoxLayout()
        lbl = QLabel(label_text)
        lbl.setFixedWidth(90)
        lbl.setStyleSheet(_LABEL_STYLE)
        row.addWidget(lbl)
        row.addWidget(widget)
        return row

    # ── Data population ───────────────────────────────────────────────────────

    def _populate(self):
        self._key_edit.setText(self._config_store.get("api_key", ""))
        self._base_edit.setText(self._config_store.get("api_base", ""))
        self._model_edit.setText(self._config_store.get("model", "kimi-k2.5"))
        self._panel_title_edit.setText(self._config_store.get("panel_title", ""))
        self._prompt_edit.setPlainText(self._config_store.get("system_prompt", ""))

        history: list[str] = self._config_store.get("prompt_history", [])
        self._history_combo.blockSignals(True)
        self._history_combo.clear()
        self._history_combo.addItem("选择历史提示词...")
        for prompt in history:
            display = prompt[:60] + ("…" if len(prompt) > 60 else "")
            self._history_combo.addItem(display, prompt)
        self._history_combo.blockSignals(False)

    # ── Interactions ──────────────────────────────────────────────────────────

    def _on_history_selected(self, index: int):
        if index <= 0:
            return
        full_prompt = self._history_combo.itemData(index)
        if full_prompt:
            self._prompt_edit.setPlainText(full_prompt)

    def _on_test(self):
        self._test_btn.setEnabled(False)
        self._status_lbl.setText("测试中…")
        self._status_lbl.setStyleSheet("color: #888888; font-size: 11px;")
        self._test_worker = ApiTestWorker(
            api_key=self._key_edit.text().strip(),
            api_base=self._base_edit.text().strip(),
            model=self._model_edit.text().strip(),
        )
        self._test_worker.test_ok.connect(self._on_test_ok)
        self._test_worker.test_error.connect(self._on_test_error)
        self._test_worker.start()

    def _on_test_ok(self):
        self._status_lbl.setText("✓ 连接成功")
        self._status_lbl.setStyleSheet("color: #4caf50; font-size: 11px;")
        self._test_btn.setEnabled(True)
        self._test_worker = None

    def _on_test_error(self, msg: str):
        self._status_lbl.setText(f"✕ {msg}")
        self._status_lbl.setStyleSheet("color: #ff6b6b; font-size: 11px;")
        self._test_btn.setEnabled(True)
        self._test_worker = None

    def _on_save(self):
        api_key = self._key_edit.text().strip()
        api_base = self._base_edit.text().strip()
        model = self._model_edit.text().strip() or "kimi-k2.5"
        panel_title = self._panel_title_edit.text().strip() or "AI翻译助手"
        system_prompt = self._prompt_edit.toPlainText().strip()

        # 1. Update shared config_store in-place (live panels see changes immediately)
        self._config_store["api_key"] = api_key
        self._config_store["api_base"] = api_base
        self._config_store["model"] = model
        self._config_store["panel_title"] = panel_title
        self._config_store["system_prompt"] = system_prompt

        # 2. Persist API credentials to .env
        save_env_config(api_key, api_base, model)

        # 3. Update prompt history (prepend if truly new, cap at 10)
        history: list[str] = list(self._config_store.get("prompt_history", []))
        if system_prompt and system_prompt not in history:
            history.insert(0, system_prompt)
            history = history[:10]
        self._config_store["prompt_history"] = history

        # 4. Persist UI settings to settings.json
        save_settings({
            "panel_title": panel_title,
            "system_prompt": system_prompt,
            "prompt_history": history,
        })

        logger.debug("Settings saved")
        self.accept()
