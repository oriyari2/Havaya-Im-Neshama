import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Havaya Im Neshama")
        self.resize(900, 600)

        welcome_label = QLabel("Havaya Im Neshama Management System")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCentralWidget(welcome_label)


def main() -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
