from unittest.mock import MagicMock, patch

import pytest
from PyQt6.QtCore import QCoreApplication

from core.api_client import ApiWorker

SYSTEM_PROMPT = (
    "你是一个智能视觉助手。请分析用户提供的图片。"
    "如果图片主体是普通英文文本，请提供信达雅的中文翻译。"
    "如果图片主体是编程代码，请提供深度的代码解析"
    "（包含编程逻辑、语法解析、关键函数分析）。"
    "使用 Markdown 格式输出。"
)


@pytest.fixture(autouse=True)
def qapp():
    """Ensure QCoreApplication exists for signal/slot tests."""
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])
    yield app


def _make_mock_chunk(content: str):
    """Create a mock streaming chunk with the given content."""
    choice = MagicMock()
    choice.delta.content = content
    chunk = MagicMock()
    chunk.choices = [choice]
    return chunk


def _make_mock_empty_chunk():
    """Create a mock streaming chunk with None content (final chunk)."""
    choice = MagicMock()
    choice.delta.content = None
    chunk = MagicMock()
    chunk.choices = [choice]
    return chunk


@patch("core.api_client.OpenAI")
def test_stream_chunks_emitted(mock_openai_cls):
    """Each chunk's content is emitted via stream_chunk signal."""
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.return_value = iter([
        _make_mock_chunk("Hello"),
        _make_mock_chunk(" World"),
        _make_mock_empty_chunk(),
    ])

    worker = ApiWorker("fake-key", "https://api.example.com/v1", "dGVzdA==")
    received = []
    worker.stream_chunk.connect(lambda text: received.append(text))

    worker.run()

    assert received == ["Hello", " World"]


@patch("core.api_client.OpenAI")
def test_stream_done_emitted(mock_openai_cls):
    """stream_done signal fires after all chunks are consumed."""
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.return_value = iter([
        _make_mock_chunk("Hi"),
        _make_mock_empty_chunk(),
    ])

    worker = ApiWorker("fake-key", "https://api.example.com/v1", "dGVzdA==")
    done_called = []
    worker.stream_done.connect(lambda: done_called.append(True))

    worker.run()

    assert done_called == [True]


@patch("core.api_client.OpenAI")
def test_stream_error_on_exception(mock_openai_cls):
    """Network errors are caught and emitted via stream_error signal."""
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.side_effect = Exception("Connection refused")

    worker = ApiWorker("fake-key", "https://api.example.com/v1", "dGVzdA==")
    errors = []
    worker.stream_error.connect(lambda msg: errors.append(msg))

    worker.run()

    assert len(errors) == 1
    assert "Connection refused" in errors[0]
