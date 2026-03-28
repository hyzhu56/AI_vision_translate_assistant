import logging

from openai import OpenAI
from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "你是一个智能视觉助手。请分析用户提供的图片。"
    "如果图片主体是普通英文文本，请提供信达雅的中文翻译。"
    "如果图片主体是编程代码，请提供深度的代码解析"
    "（包含编程逻辑、语法解析、关键函数分析）。"
    "使用 Markdown 格式输出。"
)


class ApiWorker(QThread):
    """Worker thread that calls Kimi API with streaming and emits results."""

    stream_chunk = pyqtSignal(str)
    stream_done = pyqtSignal()
    stream_error = pyqtSignal(str)

    def __init__(self, api_key: str, api_base: str, image_base64: str):
        super().__init__()
        self._api_key = api_key
        self._api_base = api_base
        self._image_base64 = image_base64

    def run(self):
        try:
            client = OpenAI(api_key=self._api_key, base_url=self._api_base)
            logger.debug("Starting streaming API request")

            response = client.chat.completions.create(
                model="kimi-k2.5",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{self._image_base64}"
                                },
                            }
                        ],
                    },
                ],
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
