from unittest.mock import MagicMock, patch

import pytest
from PyQt6.QtCore import QCoreApplication

from core.api_client import ApiTestWorker, ApiWorker


@pytest.fixture(autouse=True)
def qapp():
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])
    yield app


def _make_mock_chunk(content: str):
    choice = MagicMock()
    choice.delta.content = content
    chunk = MagicMock()
    chunk.choices = [choice]
    return chunk


def _make_mock_empty_chunk():
    choice = MagicMock()
    choice.delta.content = None
    chunk = MagicMock()
    chunk.choices = [choice]
    return chunk


_STORE = {"api_key": "fake-key", "api_base": "https://api.example.com/v1", "model": "test-model"}
_MSGS = [{"role": "user", "content": "hi"}]


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
    worker = ApiWorker(dict(_STORE), list(_MSGS))
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
    worker = ApiWorker(dict(_STORE), list(_MSGS))
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
    worker = ApiWorker(dict(_STORE), list(_MSGS))
    errors = []
    worker.stream_error.connect(lambda msg: errors.append(msg))
    worker.run()
    assert len(errors) == 1
    assert "Connection refused" in errors[0]


@patch("core.api_client.OpenAI")
def test_worker_reads_config_at_run_time(mock_openai_cls):
    """ApiWorker reads model from config_store at run() time, enabling real-time updates."""
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.return_value = iter([_make_mock_empty_chunk()])
    store = {"api_key": "key", "api_base": "base", "model": "model-v1"}
    worker = ApiWorker(store, list(_MSGS))
    store["model"] = "model-v2"   # mutate AFTER construction
    worker.run()
    call_kwargs = mock_client.chat.completions.create.call_args[1]
    assert call_kwargs["model"] == "model-v2"


@patch("core.api_client.OpenAI")
def test_api_test_worker_emits_ok(mock_openai_cls):
    """ApiTestWorker emits test_ok on successful connection."""
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.return_value = MagicMock()
    worker = ApiTestWorker("key", "base", "model")
    ok_called = []
    worker.test_ok.connect(lambda: ok_called.append(True))
    worker.run()
    assert ok_called == [True]


@patch("core.api_client.OpenAI")
def test_api_test_worker_emits_error(mock_openai_cls):
    """ApiTestWorker emits test_error with message on failure."""
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.side_effect = Exception("Auth failed")
    worker = ApiTestWorker("key", "base", "model")
    errors = []
    worker.test_error.connect(lambda msg: errors.append(msg))
    worker.run()
    assert errors == ["Auth failed"]
