# -*- coding: utf-8 -*-

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))


def test_schedule_time_helpers_parse_and_format_values():
    from ui.map_schedule import format_game_time, parse_time_to_seconds

    assert parse_time_to_seconds("01:05") == 65
    assert parse_time_to_seconds("01:02:03") == 3723
    assert parse_time_to_seconds("bad") is None
    assert format_game_time(65) == "01:05"
    assert format_game_time(3723) == "01:02:03"


def test_map_variant_detection_supports_ab_lr_and_plain_maps():
    from ui.map_schedule import detect_map_variant

    maps = ["往日神庙-A", "往日神庙-B", "虚空撕裂-左", "虚空撕裂-右", "亡者之夜"]

    assert detect_map_variant("往日神庙-A", maps) == ("AB", "A", ("A", "B"))
    assert detect_map_variant("虚空撕裂-右", maps) == ("LR", "右", ("左", "右"))
    assert detect_map_variant("亡者之夜", maps) is None


def test_parse_schedule_content_preserves_two_three_and_freeform_rows():
    from ui.map_schedule import parse_schedule_content

    rows = parse_schedule_content("00:30\tfirst\n\n01:00\tsecond\tT1\nfreeform")

    assert [(row.time_text, row.event_text, row.army_text, row.raw_text) for row in rows] == [
        ("00:30", "first", "", "00:30\tfirst"),
        ("01:00", "second", "T1", "01:00\tsecond\tT1"),
        ("", "freeform", "", "freeform"),
    ]


def test_mutator_config_parser_ignores_invalid_lines():
    from ui.mutator_alerts import MUTATOR_TYPES, parse_mutator_config_lines

    assert MUTATOR_TYPES == ("deployment", "propagator", "voidrifts", "killbots", "bombbots")
    assert parse_mutator_config_lines(["00:30\tfirst", "", "bad\tignored", "01:05\tsecond", "02:10"]) == [
        (30, "first"),
        (65, "second"),
        (130, ""),
    ]


def test_source_config_path_points_to_src_config_after_ui_package_move():
    from ui.paths import source_config_path

    config_path = source_config_path()

    assert config_path.name == "config.py"
    assert config_path.parent.name == "src"
    assert config_path.exists()


def test_mutator_toggle_clear_scope_covers_all_mutator_types():
    from ui.mutator_alerts import on_mutator_toggled

    class FakeButton:
        gray_icon = object()

        def setIcon(self, icon):
            self.icon = icon

        def setGraphicsEffect(self, effect):
            self.effect = effect

    class FakeWindow:
        pass

    window = FakeWindow()
    window.mutator_buttons = [FakeButton() for _ in range(5)]
    window.killbots_time_points = [30]
    window.alerted_killbots_time_points = {30}

    on_mutator_toggled(window, window.mutator_buttons[3], False)

    assert window.killbots_time_points == []
    assert not hasattr(window, "alerted_killbots_time_points")


def test_timer_layout_imports_platform_dependency():
    import ui.timer_layout as timer_layout

    assert hasattr(timer_layout, "sys")


def test_update_game_time_sets_default_when_no_playerdata(monkeypatch):
    from ui import map_schedule
    import mainfunctions

    class FakeLogger:
        def debug(self, _message):
            pass

        def error(self, _message):
            pass

    class FakeLabel:
        def __init__(self):
            self.value = None

        def setText(self, value):
            self.value = value

    window = type("Window", (), {})()
    window.logger = FakeLogger()
    window.time_label = FakeLabel()

    monkeypatch.setattr(mainfunctions, "most_recent_playerdata", None)

    map_schedule.update_game_time(window)

    assert window.time_label.value == "00:00"


def test_update_game_time_styles_army_column_for_active_row(monkeypatch):
    from ui import map_schedule
    import mainfunctions

    class FakeLogger:
        def debug(self, _message):
            pass

        def error(self, _message):
            pass

    class FakeLabel:
        def __init__(self):
            self.value = ""

        def text(self):
            return self.value

        def setText(self, value):
            self.value = value

    class FakeItem:
        def __init__(self, value):
            self.value = value
            self.foregrounds = []
            self.backgrounds = []

        def text(self):
            return self.value

        def setForeground(self, brush):
            self.foregrounds.append(brush)

        def setBackground(self, brush):
            self.backgrounds.append(brush)

    class FakeTable:
        def __init__(self):
            self.items = {
                (0, 0): FakeItem("00:30"),
                (0, 1): FakeItem("event"),
                (0, 2): FakeItem("T1"),
            }

        def rowCount(self):
            return 1

        def item(self, row, column):
            return self.items.get((row, column))

    class FakeToastManager:
        def is_toast_visible(self):
            return True

    window = type("Window", (), {})()
    window.logger = FakeLogger()
    window.time_label = FakeLabel()
    window.table_area = FakeTable()
    window.toast_manager = FakeToastManager()
    window._last_ui_second = None
    window._last_centered_row = None
    window._last_toast_event_key = None
    window.centered_rows = []
    window.center_table_on_row = lambda row: window.centered_rows.append(row)

    monkeypatch.setattr(mainfunctions, "most_recent_playerdata", {"time": 10})

    map_schedule.update_game_time(window)

    army_item = window.table_area.item(0, 2)
    assert army_item.foregrounds
    assert army_item.backgrounds
    assert window.centered_rows == [0]
