# -*- coding: utf-8 -*-


class FakeLogger:
    def __init__(self):
        self.errors = []
        self.infos = []

    def error(self, message):
        self.errors.append(message)

    def info(self, message):
        self.infos.append(message)


class FakeButton:
    def __init__(self):
        self._text = ""
        self.checked = None

    def setText(self, value):
        self._text = value

    def text(self):
        return self._text

    def setChecked(self, value):
        self.checked = value


class FakeGroup:
    def __init__(self):
        self.visible = None

    def show(self):
        self.visible = True

    def hide(self):
        self.visible = False


class FakeCombo:
    def __init__(self, names):
        self.names = names

    def count(self):
        return len(self.names)

    def itemText(self, index):
        return self.names[index]


class FakeTable:
    def __init__(self):
        self.row_count = 0
        self.items = {}
        self.spans = []

    def setRowCount(self, row_count):
        self.row_count = row_count
        self.items.clear()
        self.spans.clear()

    def rowCount(self):
        return self.row_count

    def setItem(self, row, column, item):
        self.items[(row, column)] = item

    def item(self, row, column):
        return self.items.get((row, column))

    def setSpan(self, row, column, row_span, column_span):
        self.spans.append((row, column, row_span, column_span))


def test_on_map_selected_updates_variant_buttons_and_populates_table(tmp_path, monkeypatch):
    from ui import map_schedule

    map_file = tmp_path / "Temple-B"
    map_file.write_text("00:30\tfirst\nfreeform\n01:00\tsecond\tT1\n", encoding="utf-8")
    monkeypatch.setattr(map_schedule, "get_resources_dir", lambda *parts: str(map_file))

    class FakeWindow:
        def __init__(self):
            self.manual_map_selection = False
            self.combo_box = FakeCombo(["Temple-A", "Temple-B"])
            self.version_buttons = [FakeButton(), FakeButton()]
            self.map_version_group = FakeGroup()
            self.table_area = FakeTable()
            self.logger = FakeLogger()

        def sender(self):
            return self.combo_box

    window = FakeWindow()
    map_schedule.on_map_selected(window, "Temple-B")

    assert window.manual_map_selection is True
    assert [button.text() for button in window.version_buttons] == ["A", "B"]
    assert [button.checked for button in window.version_buttons] == [False, True]
    assert window.map_version_group.visible is True
    assert window.table_area.rowCount() == 3
    assert window.table_area.item(0, 0).text() == "00:30"
    assert window.table_area.item(0, 1).text() == "first"
    assert window.table_area.item(1, 0).text() == "freeform"
    assert window.table_area.spans == [(1, 0, 1, 3)]
    assert window.table_area.item(2, 2).text() == "T1"
