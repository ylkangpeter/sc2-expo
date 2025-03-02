from qt_gui import TimerWindow
import sys
from PyQt5.QtWidgets import QApplication

def main():
    app = QApplication(sys.argv)
    timer = TimerWindow()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()