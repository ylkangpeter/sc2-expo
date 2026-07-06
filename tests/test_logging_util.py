# -*- coding: utf-8 -*-


def test_setup_logger_uses_base_dir_log_file(tmp_path, monkeypatch):
    import logging_util

    calls = {}

    class FakeFileHandler:
        def __init__(self, path, encoding, mode):
            calls["file_handler"] = (path, encoding, mode)

    class FakeStreamHandler:
        pass

    monkeypatch.setattr(logging_util.logging, "FileHandler", FakeFileHandler)
    monkeypatch.setattr(logging_util.logging, "StreamHandler", FakeStreamHandler)
    monkeypatch.setattr(logging_util.logging, "basicConfig", lambda **kwargs: calls.update(kwargs))
    monkeypatch.setattr(logging_util.config, "LOG_LEVEL", "WARNING")

    logging_util.setup_logger(str(tmp_path))

    assert (tmp_path / "log").exists()
    assert calls["file_handler"] == (str(tmp_path / "log" / "sc2_timer.log"), "utf-8", "a")
    assert calls["level"] == logging_util.logging.WARNING
    assert calls["format"] == "%(asctime)s - %(levelname)s - %(message)s"
