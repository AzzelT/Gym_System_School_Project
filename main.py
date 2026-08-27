import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont, QIcon
from module.database import DatabaseManager
from module.ui_main import LoginDialog, MainWindow, ICON_PATH
import os


def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("Arial, 10"))
    if os.path.exists(ICON_PATH):
        app.setWindowIcon(QIcon(ICON_PATH))
    db = DatabaseManager()

    while True:
        login = LoginDialog(db)
        if login.exec() != LoginDialog.DialogCode.Accepted:
            break

        window = MainWindow(db, login.current_user)
        window.show()
        app.exec()  # returns when the window closes (e.g. via Logout)

    sys.exit(0)


if __name__ == "__main__":
    main()
