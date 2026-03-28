import logging

from openai import OpenAI
from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)


class ApiWorker(QThread):
    """Worker thread that calls the configured API with a full messages list."""

    stream_chunk = pyqtSignal(str)
    stream_done = pyqtSignal()
    stream_error = pyqtSignal(str)

    def __init__(self, config_store: dict, messages: list):
        super().__init__()
        self._config_store = config_store   # reference — read at run() time
        self._messages = messages

    def run(self):
        try:
            client = OpenAI(
                api_key=self._config_store["api_key"],
                base_url=self._config_store["api_base"],
            )
            logger.debug("Starting streaming API request")
            response = client.chat.completions.create(
                model=self._config_store["model"],
                messages=self._messages,
                stream=True,
                timeout=15,
            )
            chunk_count = 0
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    text = chunk.choices[0].delta.content
                    self.stream_chunk.emit(text)
                    chunk_count += 1
            logger.debug("Stream complete, received %d chunks", chunk_count)
            self.stream_done.emit()
        except Exception as e:
            logger.error("API request failed: %s", e)
            self.stream_error.emit(str(e))


class ApiTestWorker(QThread):
    """Lightweight connectivity test worker used by SettingsWindow."""

    test_ok = pyqtSignal()
    test_error = pyqtSignal(str)

    def __init__(self, api_key: str, api_base: str, model: str):
        super().__init__()
        self._api_key = api_key
        self._api_base = api_base
        self._model = model

    def run(self):
        try:
            client = OpenAI(api_key=self._api_key, base_url=self._api_base)
            client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=1,
                stream=False,
            )
            self.test_ok.emit()
        except Exception as e:
            self.test_error.emit(str(e))
