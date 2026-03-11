import os
import sys
from PyQt5.QtWidgets import QApplication, QAction, QMenu, QSystemTrayIcon
from PyQt5.QtGui import QIcon

from fileutil import get_resources_dir
import config
from logging_util import get_logger


class TrayManager:
    def __init__(self, parent=None):
        self.parent = parent
        self.logger = get_logger(__name__)
        self.tray_icon = None
        self.tray_menu = None
        self.init_tray()

    def dispose(self):
        if self.tray_icon is None:
            return
        try:
            self.tray_icon.activated.disconnect(self.on_tray_activated)
        except Exception:
            pass
        self.tray_icon.hide()
        self.tray_icon.deleteLater()
        self.tray_icon = None
        self.tray_menu = None

    def init_tray(self):
        self.dispose()

        self.tray_icon = QSystemTrayIcon(self.parent)

        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.dirname(__file__))

        icon_path = os.path.join(base_path, 'ico', 'fav.ico')
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))

        self.tray_menu = QMenu(self.parent)
        show_action = QAction(self.parent.get_text('show_action'), self.parent)
        quit_action = QAction(self.parent.get_text('quit_action'), self.parent)

        show_action.triggered.connect(self.parent.show)
        quit_action.triggered.connect(QApplication.instance().quit)

        language_menu = QMenu(self.parent.get_text('language_menu'), self.parent)
        maps_dir = get_resources_dir('resources', 'maps')
        if maps_dir and os.path.isdir(maps_dir):
            for lang_dir in os.listdir(maps_dir):
                lang_path = os.path.join(maps_dir, lang_dir)
                if os.path.isdir(lang_path) and lang_dir not in ['.', '..']:
                    language_action = QAction(lang_dir, self.parent)
                    if lang_dir == config.current_language:
                        language_action.setText(f'{lang_dir} (current)')
                    language_action.triggered.connect(
                        lambda checked, lang=lang_dir: self.parent.on_language_changed(lang)
                    )
                    language_menu.addAction(language_action)

        self.tray_menu.addAction(show_action)
        self.tray_menu.addMenu(language_menu)
        self.tray_menu.addAction(quit_action)

        # Let Qt render and position right-click menu natively.
        self.tray_icon.setContextMenu(self.tray_menu)
        # Only keep light left-click behavior.
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.parent.show()