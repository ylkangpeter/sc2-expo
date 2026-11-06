# -*- coding: utf-8 -*-


class FakeLogger:
    def __init__(self):
        self.debugs = []
        self.errors = []
        self.infos = []

    def debug(self, message):
        self.debugs.append(message)

    def error(self, message):
        self.errors.append(message)

    def info(self, message):
        self.infos.append(message)


def test_load_mutator_config_returns_sorted_time_points(tmp_path, monkeypatch):
    from ui import mutator_alerts

    config_dir = tmp_path / "resources" / "mutator"
    config_dir.mkdir(parents=True)
    (config_dir / "deployment.txt").write_text(
        "01:05\tsecond\nbad\tignored\n00:30\tfirst\n02:10\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    class FakeWindow:
        logger = FakeLogger()

    assert mutator_alerts.load_mutator_config(FakeWindow(), "deployment") == [30, 65, 130]


def test_load_mutator_config_uses_resource_resolver_and_caches_messages(tmp_path, monkeypatch):
    from ui import mutator_alerts

    config_file = tmp_path / "deployment.txt"
    config_file.write_text("00:30\tfirst\n01:05\tsecond\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path / "..")
    monkeypatch.setattr(mutator_alerts, "get_resources_dir", lambda *parts: str(config_file))

    class FakeWindow:
        logger = FakeLogger()

    window = FakeWindow()

    assert mutator_alerts.load_mutator_config(window, "deployment") == [30, 65]
    assert window.mutator_alert_messages == {"deployment": {30: "first", 65: "second"}}


def test_check_mutator_alerts_triggers_once_with_config_text(tmp_path, monkeypatch):
    import mainfunctions
    from ui import mutator_alerts

    config_dir = tmp_path / "resources" / "mutator"
    config_dir.mkdir(parents=True)
    (config_dir / "deployment.txt").write_text("00:30\tdrop wave\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(mutator_alerts.config, "MUTATION_FACTOR_ALERT_SECONDS", 10)
    monkeypatch.setattr(mainfunctions, "most_recent_playerdata", {"time": 25})

    class FakeButton:
        def __init__(self, checked):
            self._checked = checked

        def isChecked(self):
            return self._checked

    class FakeWindow:
        def __init__(self):
            self.logger = FakeLogger()
            self.mutator_buttons = [FakeButton(True)] + [FakeButton(False) for _ in range(4)]
            self.deployment_time_points = [30]
            self.alerts = []

        def show_mutator_alert(self, message, mutator_type):
            self.alerts.append((message, mutator_type))

    window = FakeWindow()

    mutator_alerts.check_mutator_alerts(window)
    mutator_alerts.check_mutator_alerts(window)

    assert window.alerts == [("5 秒后 drop wave", "deployment")]
    assert window.alerted_deployment_time_points == {30}


def test_check_mutator_alerts_uses_cached_message_without_reopening_file(monkeypatch):
    import mainfunctions
    from ui import mutator_alerts

    monkeypatch.setattr(mutator_alerts.config, "MUTATION_FACTOR_ALERT_SECONDS", 10)
    monkeypatch.setattr(mainfunctions, "most_recent_playerdata", {"time": 25})
    monkeypatch.setattr(mutator_alerts, "get_resources_dir", lambda *parts: (_ for _ in ()).throw(AssertionError("no IO")))

    class FakeButton:
        def __init__(self, checked):
            self._checked = checked

        def isChecked(self):
            return self._checked

    class FakeWindow:
        def __init__(self):
            self.logger = FakeLogger()
            self.mutator_buttons = [FakeButton(True)] + [FakeButton(False) for _ in range(4)]
            self.deployment_time_points = [30]
            self.mutator_alert_messages = {"deployment": {30: "cached"}}
            self.alerts = []

        def show_mutator_alert(self, message, mutator_type):
            self.alerts.append((message, mutator_type))

    window = FakeWindow()

    mutator_alerts.check_mutator_alerts(window)

    assert window.alerts == [("5 秒后 cached", "deployment")]


def test_check_mutator_alerts_resets_deduplication_when_game_time_rewinds(monkeypatch):
    import mainfunctions
    from ui import mutator_alerts

    monkeypatch.setattr(mutator_alerts.config, "MUTATION_FACTOR_ALERT_SECONDS", 10)
    monkeypatch.setattr(mainfunctions, "most_recent_playerdata", {"time": 25})

    class FakeButton:
        def isChecked(self):
            return True

    class FakeWindow:
        def __init__(self):
            self.logger = FakeLogger()
            self.mutator_buttons = [FakeButton()] + [type("B", (), {"isChecked": lambda _self: False})() for _ in range(4)]
            self.deployment_time_points = [30]
            self.mutator_alert_messages = {"deployment": {30: "drop"}}
            self.alerts = []

        def show_mutator_alert(self, message, mutator_type):
            self.alerts.append((message, mutator_type))

    window = FakeWindow()
    mutator_alerts.check_mutator_alerts(window)
    assert window.alerts == [("5 秒后 drop", "deployment")]

    monkeypatch.setattr(mainfunctions, "most_recent_playerdata", {"time": 2})
    mutator_alerts.check_mutator_alerts(window)
    assert len(window.alerts) == 1

    monkeypatch.setattr(mainfunctions, "most_recent_playerdata", {"time": 25})
    mutator_alerts.check_mutator_alerts(window)
    assert window.alerts[-1] == ("5 秒后 drop", "deployment")
    assert len(window.alerts) == 2
