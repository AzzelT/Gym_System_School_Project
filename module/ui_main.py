import os
from datetime import datetime, timedelta

from PyQt6.QtWidgets import (
    QDialog, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox, QTableWidget,
    QTableWidgetItem, QMessageBox, QHeaderView, QTabWidget, QTextEdit,
    QComboBox, QCheckBox, QDateEdit, QDoubleSpinBox, QSpinBox
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QIcon
from module.database import DatabaseManager

ICON_PATH = os.path.join(os.path.dirname(
    os.path.abspath(__file__)),"image", "icon.png")


APP_STYLE = """
QWidget {
    font-family: Segoe UI;
    font-size: 10.5pt;
    background-color: #121212;
    color: #f5f5f5;
}

QGroupBox {
    font-weight: bold;
    border: 1px solid #2d2d2d;
    border-radius: 10px;
    margin-top: 12px;
    padding-top: 14px;
    background-color: #1e1e1e;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px;
    color: #4caf50;
}

QLineEdit, QTextEdit, QComboBox, QDateEdit, QDoubleSpinBox, QSpinBox {
    min-height: 32px;
    border: 1px solid #3d3d3d;
    border-radius: 8px;
    padding: 4px 8px;
    background-color: #252525;
    color: #ffffff;
}

QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateEdit:focus,
QDoubleSpinBox:focus, QSpinBox:focus {
    border: 2px solid #4caf50;
}

QPushButton {
    min-height: 36px;
    min-width: 100px;
    border: none;
    border-radius: 8px;
    background-color: #4caf50;
    color: white;
    font-weight: bold;
    padding: 6px 14px;
}

QPushButton:hover {
    background-color: #43a047;
}

QPushButton:pressed {
    background-color: #388e3c;
}

QPushButton#danger {
    background-color: #e53935;
}

QPushButton#danger:hover {
    background-color: #c62828;
}

QPushButton#secondary {
    background-color: #424242;
}

QPushButton#secondary:hover {
    background-color: #303030;
}

QTableWidget {
    border: 1px solid #2d2d2d;
    gridline-color: #333333;
    background-color: #1e1e1e;
    alternate-background-color: #252525;
    selection-background-color: #4caf50;
    selection-color: white;
}

QHeaderView::section {
    background-color: #2c2c2c;
    color: #4caf50;
    padding: 8px;
    border: 1px solid #3d3d3d;
    font-weight: bold;
}

QLabel#title {
    font-size: 22pt;
    font-weight: bold;
    color: #4caf50;
}

QLabel#subtitle {
    color: #bdbdbd;
    font-size: 10pt;
}

QScrollBar:vertical {
    background: #1e1e1e;
    width: 12px;
}

QScrollBar::handle:vertical {
    background: #4caf50;
    border-radius: 6px;
}

QScrollBar::handle:vertical:hover {
    background: #43a047;
}
"""

DATE_FORMAT = "yyyy-MM-dd"


class LoginDialog(QDialog):
    def __init__(self, db: DatabaseManager):
        super().__init__()
        self.db = db
        self.current_user = None
        self.setWindowTitle("GYM Login")
        self.setFixedSize(420, 260)
        self.setStyleSheet(APP_STYLE)
        if os.path.exists(ICON_PATH):
            self.setWindowIcon(QIcon(ICON_PATH))
        self.build_ui()

    def build_ui(self):
        title = QLabel("GYM Login")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.username_input.returnPressed.connect(self.login)
        self.password_input.returnPressed.connect(self.login)

        form = QFormLayout()
        form.addRow("Username:", self.username_input)
        form.addRow("Password:", self.password_input)

        login_btn = QPushButton("Login")
        login_btn.clicked.connect(self.login)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondary")
        cancel_btn.clicked.connect(self.reject)
        btns = QHBoxLayout()
        btns.addStretch()
        btns.addWidget(cancel_btn)
        btns.addWidget(login_btn)

        main = QVBoxLayout()
        main.setContentsMargins(20, 20, 20, 20)
        main.addWidget(title)
        main.addLayout(form)
        main.addStretch()
        main.addLayout(btns)
        self.setLayout(main)

    def login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        user = self.db.authenticate(username, password)
        if user:
            self.current_user = user
            self.accept()
        else:
            QMessageBox.warning(self, "Login Failed",
                                "Invalid username, password, or inactive user.")


class RoleSelectDialog(QDialog):
    """Generic dialog to pick from a list of (id, label) pairs."""

    def __init__(self, title, items, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(320)
        self.selected_id = None

        layout = QVBoxLayout()
        self.combo = QComboBox()
        for item_id, label in items:
            self.combo.addItem(label, item_id)
        layout.addWidget(self.combo)

        btns = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondary")
        cancel_btn.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(cancel_btn)
        btns.addWidget(ok_btn)
        layout.addLayout(btns)
        self.setLayout(layout)

    def accept(self):
        self.selected_id = self.combo.currentData()
        super().accept()


class UserDialog(QDialog):
    def __init__(self, parent=None, user=None):
        super().__init__(parent)
        # user tuple: (id, username, full_name, email, phone, is_active, roles, created_at, last_login)
        self.user = user
        self.setWindowTitle("Edit User" if user else "New User")
        self.setMinimumWidth(380)
        self.build_ui()

    def build_ui(self):
        form = QFormLayout()

        self.username_input = QLineEdit()
        self.fullname_input = QLineEdit()
        self.email_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText(
            "Leave blank to keep current password" if self.user else "Password"
        )
        self.active_checkbox = QCheckBox("Active")
        self.active_checkbox.setChecked(True)

        if self.user:
            self.username_input.setText(self.user[1])
            self.username_input.setEnabled(False)
            self.fullname_input.setText(self.user[2])
            self.email_input.setText(self.user[3] or "")
            self.phone_input.setText(self.user[4] or "")
            self.active_checkbox.setChecked(bool(self.user[5]))

        form.addRow("Username:", self.username_input)
        form.addRow("Full name:", self.fullname_input)
        form.addRow("Email:", self.email_input)
        form.addRow("Phone:", self.phone_input)
        form.addRow("Password:", self.password_input)
        form.addRow("", self.active_checkbox)

        if self.user:
            meta = QLabel(
                f"Created: {self.user[7] or '-'}    Last login: {self.user[8] or 'Never'}")
            meta.setObjectName("subtitle")
            form.addRow("", meta)

        btns = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondary")
        cancel_btn.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(cancel_btn)
        btns.addWidget(save_btn)

        main = QVBoxLayout()
        main.addLayout(form)
        main.addLayout(btns)
        self.setLayout(main)

    def get_data(self):
        return {
            "username": self.username_input.text().strip(),
            "full_name": self.fullname_input.text().strip(),
            "email": self.email_input.text().strip(),
            "phone": self.phone_input.text().strip(),
            "password": self.password_input.text().strip(),
            "is_active": 1 if self.active_checkbox.isChecked() else 0,
        }


class RoleDialog(QDialog):
    def __init__(self, parent=None, role=None):
        super().__init__(parent)
        self.role = role  # (id, role_name, description) or None
        self.setWindowTitle("Edit Role" if role else "New Role")
        self.setMinimumWidth(360)
        self.build_ui()

    def build_ui(self):
        form = QFormLayout()
        self.name_input = QLineEdit()
        self.desc_input = QLineEdit()

        if self.role:
            self.name_input.setText(self.role[1])
            self.desc_input.setText(self.role[2] or "")

        form.addRow("Role name:", self.name_input)
        form.addRow("Description:", self.desc_input)

        btns = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondary")
        cancel_btn.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(cancel_btn)
        btns.addWidget(save_btn)

        main = QVBoxLayout()
        main.addLayout(form)
        main.addLayout(btns)
        self.setLayout(main)

    def get_data(self):
        return {
            "role_name": self.name_input.text().strip(),
            "description": self.desc_input.text().strip(),
        }


class PermissionDialog(QDialog):
    def __init__(self, parent=None, permission=None):
        super().__init__(parent)
        # (id, permission_key, description) or None
        self.permission = permission
        self.setWindowTitle(
            "Edit Permission" if permission else "New Permission")
        self.setMinimumWidth(360)
        self.build_ui()

    def build_ui(self):
        form = QFormLayout()
        self.key_input = QLineEdit()
        self.desc_input = QLineEdit()

        if self.permission:
            self.key_input.setText(self.permission[1])
            self.desc_input.setText(self.permission[2] or "")

        form.addRow("Permission key:", self.key_input)
        form.addRow("Description:", self.desc_input)

        btns = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondary")
        cancel_btn.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(cancel_btn)
        btns.addWidget(save_btn)

        main = QVBoxLayout()
        main.addLayout(form)
        main.addLayout(btns)
        self.setLayout(main)

    def get_data(self):
        return {
            "permission_key": self.key_input.text().strip(),
            "description": self.desc_input.text().strip(),
        }


class MembershipTypeDialog(QDialog):
    def __init__(self, parent=None, membership_type=None):
        super().__init__(parent)
        # (id, type_name, duration_days, price, description)
        self.membership_type = membership_type
        self.setWindowTitle(
            "Edit Membership Type" if membership_type else "New Membership Type")
        self.setMinimumWidth(360)
        self.build_ui()

    def build_ui(self):
        form = QFormLayout()
        self.name_input = QLineEdit()
        self.duration_input = QSpinBox()
        self.duration_input.setRange(1, 3650)
        self.duration_input.setValue(30)
        self.duration_input.setSuffix(" days")
        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(0, 1_000_000)
        self.price_input.setDecimals(2)
        self.price_input.setPrefix("$ ")
        self.desc_input = QLineEdit()

        if self.membership_type:
            self.name_input.setText(self.membership_type[1])
            self.duration_input.setValue(self.membership_type[2])
            self.price_input.setValue(self.membership_type[3] or 0)
            self.desc_input.setText(self.membership_type[4] or "")

        form.addRow("Plan name:", self.name_input)
        form.addRow("Duration:", self.duration_input)
        form.addRow("Price:", self.price_input)
        form.addRow("Description:", self.desc_input)

        btns = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondary")
        cancel_btn.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(cancel_btn)
        btns.addWidget(save_btn)

        main = QVBoxLayout()
        main.addLayout(form)
        main.addLayout(btns)
        self.setLayout(main)

    def get_data(self):
        return {
            "type_name": self.name_input.text().strip(),
            "duration_days": self.duration_input.value(),
            "price": self.price_input.value(),
            "description": self.desc_input.text().strip(),
        }


class MemberDialog(QDialog):
    def __init__(self, parent=None, member=None, membership_types=None):
        super().__init__(parent)
        # member tuple: (id, full_name, phone, email, join_date, status,
        #   membership_type_id, type_name, membership_start, membership_expiry, notes)
        self.member = member
        self.membership_types = membership_types or []
        self.setWindowTitle("Edit Member" if member else "New Member")
        self.setMinimumWidth(380)
        self.build_ui()

    def build_ui(self):
        form = QFormLayout()

        self.fullname_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.email_input = QLineEdit()
        self.status_combo = QComboBox()
        self.status_combo.addItems(["active", "inactive", "suspended"])

        self.membership_combo = QComboBox()
        self.membership_combo.addItem("None", None)
        for mt_id, type_name, duration_days, price, _desc in self.membership_types:
            self.membership_combo.addItem(
                f"{type_name} ({duration_days} days, ${price:.2f})", mt_id)

        self.start_date_input = QDateEdit()
        self.start_date_input.setDisplayFormat(DATE_FORMAT)
        self.start_date_input.setCalendarPopup(True)
        self.start_date_input.setDate(QDate.currentDate())

        self.notes_input = QTextEdit()
        self.notes_input.setFixedHeight(70)

        self.expiry_label = QLabel("-")
        self.expiry_label.setObjectName("subtitle")

        if self.member:
            self.fullname_input.setText(self.member[1])
            self.phone_input.setText(self.member[2] or "")
            self.email_input.setText(self.member[3] or "")
            idx = self.status_combo.findText(self.member[5])
            if idx >= 0:
                self.status_combo.setCurrentIndex(idx)
            mt_idx = self.membership_combo.findData(self.member[6])
            if mt_idx >= 0:
                self.membership_combo.setCurrentIndex(mt_idx)
            if self.member[8]:
                self.start_date_input.setDate(
                    QDate.fromString(self.member[8], DATE_FORMAT))
            self.notes_input.setPlainText(self.member[10] or "")
            self.expiry_label.setText(self.member[9] or "-")

        form.addRow("Full name:", self.fullname_input)
        form.addRow("Phone:", self.phone_input)
        form.addRow("Email:", self.email_input)
        form.addRow("Status:", self.status_combo)
        form.addRow("Membership type:", self.membership_combo)
        form.addRow("Membership start:", self.start_date_input)
        form.addRow("Current expiry:", self.expiry_label)
        form.addRow("Notes:", self.notes_input)

        btns = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondary")
        cancel_btn.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(cancel_btn)
        btns.addWidget(save_btn)

        main = QVBoxLayout()
        main.addLayout(form)
        main.addLayout(btns)
        self.setLayout(main)

    def get_data(self):
        return {
            "full_name": self.fullname_input.text().strip(),
            "phone": self.phone_input.text().strip(),
            "email": self.email_input.text().strip(),
            "status": self.status_combo.currentText(),
            "membership_type_id": self.membership_combo.currentData(),
            "membership_start": self.start_date_input.date().toString(DATE_FORMAT),
            "notes": self.notes_input.toPlainText().strip(),
        }


class MainWindow(QMainWindow):
    def __init__(self, db: DatabaseManager, current_user: dict):
        super().__init__()
        self.db = db
        self.current_user = current_user
        self.permissions = set(db.get_user_permissions(current_user["id"]))

        self.setWindowTitle("GYM Management System")
        self.resize(1100, 680)
        self.setStyleSheet(APP_STYLE)
        if os.path.exists(ICON_PATH):
            self.setWindowIcon(QIcon(ICON_PATH))

        self.build_ui()
        self.refresh_all()

    #  UI construction

    def build_ui(self):
        central = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)

        header = QHBoxLayout()
        title = QLabel("GYM Management System")
        title.setObjectName("title")
        subtitle = QLabel(
            f"Logged in as {self.current_user['full_name']} "
            f"({self.current_user['username']})"
        )
        subtitle.setObjectName("subtitle")
        title_box = QVBoxLayout()
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)
        header.addStretch()
        logout_btn = QPushButton("Logout")
        logout_btn.setObjectName("secondary")
        logout_btn.clicked.connect(self.logout)
        header.addWidget(logout_btn)
        layout.addLayout(header)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        if self.permissions:
            self.tabs.addTab(self.build_dashboard_tab(), "Dashboard")
        if "manage_users" in self.permissions:
            self.tabs.addTab(self.build_users_tab(), "Users")
        if "manage_members" in self.permissions:
            self.tabs.addTab(self.build_members_tab(), "Members")
        if "manage_membership_types" in self.permissions:
            self.tabs.addTab(self.build_membership_types_tab(),
                             "Membership Types")
        if "mark_attendance" in self.permissions:
            self.tabs.addTab(self.build_attendance_tab(), "Attendance")
        if "manage_roles" in self.permissions:
            self.tabs.addTab(self.build_roles_tab(), "Roles")
        if "manage_permissions" in self.permissions:
            self.tabs.addTab(self.build_permissions_tab(), "Permissions")
        if "assign_roles" in self.permissions or "assign_permissions" in self.permissions:
            self.tabs.addTab(self.build_assignments_tab(), "Assignments")
        if "view_reports" in self.permissions:
            self.tabs.addTab(self.build_reports_tab(), "Reports")

        if self.tabs.count() == 0:
            no_access = QLabel(
                "You do not have access to any management features.")
            no_access.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(no_access)

        central.setLayout(layout)
        self.setCentralWidget(central)

    def build_users_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        btn_row = QHBoxLayout()
        add_btn = QPushButton("Add User")
        add_btn.clicked.connect(self.add_user)
        edit_btn = QPushButton("Edit")
        edit_btn.setObjectName("secondary")
        edit_btn.clicked.connect(self.edit_user)
        delete_btn = QPushButton("Delete")
        delete_btn.setObjectName("danger")
        delete_btn.clicked.connect(self.delete_user)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(edit_btn)
        btn_row.addWidget(delete_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.users_table = self._make_table(
            ["ID", "Username", "Full Name", "Email", "Phone", "Active",
             "Roles", "Last Login"])
        self.users_table.itemDoubleClicked.connect(lambda *_: self.edit_user())
        layout.addWidget(self.users_table)
        btn_row.insertWidget(0, self._make_search_box(
            "Search by name, username, email...", self.users_table))

        widget.setLayout(layout)
        return widget

    def build_members_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        btn_row = QHBoxLayout()
        add_btn = QPushButton("Add Member")
        add_btn.clicked.connect(self.add_member)
        edit_btn = QPushButton("Edit")
        edit_btn.setObjectName("secondary")
        edit_btn.clicked.connect(self.edit_member)
        delete_btn = QPushButton("Delete")
        delete_btn.setObjectName("danger")
        delete_btn.clicked.connect(self.delete_member)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(edit_btn)
        btn_row.addWidget(delete_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.members_table = self._make_table(
            ["ID", "Full Name", "Phone", "Email", "Membership",
             "Start", "Expiry", "Status"])
        self.members_table.itemDoubleClicked.connect(
            lambda *_: self.edit_member())
        layout.addWidget(self.members_table)
        btn_row.insertWidget(0, self._make_search_box(
            "Search by name, phone, email...", self.members_table))

        widget.setLayout(layout)
        return widget

    def build_membership_types_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        btn_row = QHBoxLayout()
        add_btn = QPushButton("Add Plan")
        add_btn.clicked.connect(self.add_membership_type)
        edit_btn = QPushButton("Edit")
        edit_btn.setObjectName("secondary")
        edit_btn.clicked.connect(self.edit_membership_type)
        delete_btn = QPushButton("Delete")
        delete_btn.setObjectName("danger")
        delete_btn.clicked.connect(self.delete_membership_type)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(edit_btn)
        btn_row.addWidget(delete_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.membership_types_table = self._make_table(
            ["ID", "Plan Name", "Duration (days)", "Price", "Description"])
        self.membership_types_table.itemDoubleClicked.connect(
            lambda *_: self.edit_membership_type())
        layout.addWidget(self.membership_types_table)

        widget.setLayout(layout)
        return widget

    def build_attendance_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        mark_box = QGroupBox("Mark Attendance")
        mark_layout = QHBoxLayout()
        self.attendance_member_combo = QComboBox()
        self.attendance_member_combo.setEditable(True)
        self.attendance_member_combo.setInsertPolicy(
            QComboBox.InsertPolicy.NoInsert)
        self.attendance_status_combo = QComboBox()
        self.attendance_status_combo.addItems(["present", "absent"])
        mark_btn = QPushButton("Mark for Today")
        mark_btn.clicked.connect(self.mark_attendance)
        mark_layout.addWidget(QLabel("Member:"))
        mark_layout.addWidget(self.attendance_member_combo, 2)
        mark_layout.addWidget(QLabel("Status:"))
        mark_layout.addWidget(self.attendance_status_combo)
        mark_layout.addWidget(mark_btn)
        mark_box.setLayout(mark_layout)
        layout.addWidget(mark_box)

        btn_row = QHBoxLayout()
        self.attendance_date_filter = QDateEdit()
        self.attendance_date_filter.setDisplayFormat(DATE_FORMAT)
        self.attendance_date_filter.setCalendarPopup(True)
        self.attendance_date_filter.setDate(QDate.currentDate())
        self.attendance_date_filter.dateChanged.connect(
            lambda *_: self.refresh_attendance())
        today_btn = QPushButton("Today")
        today_btn.setObjectName("secondary")
        today_btn.clicked.connect(
            lambda: self.attendance_date_filter.setDate(QDate.currentDate()))
        show_all_check = QCheckBox("Show all dates")
        show_all_check.stateChanged.connect(
            lambda *_: self.refresh_attendance())
        self.attendance_show_all = show_all_check
        delete_btn = QPushButton("Delete Selected")
        delete_btn.setObjectName("danger")
        delete_btn.clicked.connect(self.delete_attendance_record)
        btn_row.addWidget(QLabel("Date:"))
        btn_row.addWidget(self.attendance_date_filter)
        btn_row.addWidget(today_btn)
        btn_row.addWidget(show_all_check)
        btn_row.addStretch()
        btn_row.addWidget(delete_btn)
        layout.addLayout(btn_row)

        self.attendance_table = self._make_table(
            ["ID", "Member", "Date", "Time", "Status"])
        layout.addWidget(self.attendance_table)

        widget.setLayout(layout)
        return widget

    def build_roles_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        btn_row = QHBoxLayout()
        add_btn = QPushButton("Add Role")
        add_btn.clicked.connect(self.add_role)
        edit_btn = QPushButton("Edit")
        edit_btn.setObjectName("secondary")
        edit_btn.clicked.connect(self.edit_role)
        delete_btn = QPushButton("Delete")
        delete_btn.setObjectName("danger")
        delete_btn.clicked.connect(self.delete_role)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(edit_btn)
        btn_row.addWidget(delete_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.roles_table = self._make_table(["ID", "Role Name", "Description"])
        self.roles_table.itemDoubleClicked.connect(lambda *_: self.edit_role())
        layout.addWidget(self.roles_table)

        widget.setLayout(layout)
        return widget

    def build_permissions_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        btn_row = QHBoxLayout()
        add_btn = QPushButton("Add Permission")
        add_btn.clicked.connect(self.add_permission)
        edit_btn = QPushButton("Edit")
        edit_btn.setObjectName("secondary")
        edit_btn.clicked.connect(self.edit_permission)
        delete_btn = QPushButton("Delete")
        delete_btn.setObjectName("danger")
        delete_btn.clicked.connect(self.delete_permission)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(edit_btn)
        btn_row.addWidget(delete_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.permissions_table = self._make_table(
            ["ID", "Permission Key", "Description"])
        self.permissions_table.itemDoubleClicked.connect(
            lambda *_: self.edit_permission())
        layout.addWidget(self.permissions_table)

        widget.setLayout(layout)
        return widget

    def build_assignments_tab(self):
        widget = QWidget()
        layout = QHBoxLayout()

        # --- User <-> Role assignment ---
        role_box = QGroupBox("User Roles")
        role_layout = QVBoxLayout()

        assign_row = QHBoxLayout()
        assign_role_btn = QPushButton("Assign Role to User")
        assign_role_btn.clicked.connect(self.assign_role_to_user)
        remove_role_btn = QPushButton("Remove Selected")
        remove_role_btn.setObjectName("danger")
        remove_role_btn.clicked.connect(self.remove_role_from_user)
        assign_row.addWidget(assign_role_btn)
        assign_row.addWidget(remove_role_btn)
        role_layout.addLayout(assign_row)

        self.user_roles_table = self._make_table(
            ["User ID", "Username", "Role ID", "Role Name"])
        role_layout.addWidget(self.user_roles_table)
        role_box.setLayout(role_layout)

        # Role, Permission assignment 
        perm_box = QGroupBox("Role Permissions")
        perm_layout = QVBoxLayout()

        assign_row2 = QHBoxLayout()
        assign_perm_btn = QPushButton("Assign Permission to Role")
        assign_perm_btn.clicked.connect(self.assign_permission_to_role)
        remove_perm_btn = QPushButton("Remove Selected")
        remove_perm_btn.setObjectName("danger")
        remove_perm_btn.clicked.connect(self.remove_permission_from_role)
        assign_row2.addWidget(assign_perm_btn)
        assign_row2.addWidget(remove_perm_btn)
        perm_layout.addLayout(assign_row2)

        self.role_permissions_table = self._make_table(
            ["Role ID", "Role Name", "Permission ID", "Permission Key"])
        perm_layout.addWidget(self.role_permissions_table)
        perm_box.setLayout(perm_layout)

        layout.addWidget(role_box)
        layout.addWidget(perm_box)
        widget.setLayout(layout)
        return widget

    def build_reports_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        summary_box = QGroupBox("System Summary")
        summary_layout = QVBoxLayout()
        self.reports_label = QLabel()
        self.reports_label.setWordWrap(True)
        summary_layout.addWidget(self.reports_label)
        summary_box.setLayout(summary_layout)

        expiring_box = QGroupBox("Memberships Expiring in Next 7 Days")
        expiring_layout = QVBoxLayout()
        self.expiring_table = self._make_table(
            ["Member", "Plan", "Expiry Date"])
        expiring_layout.addWidget(self.expiring_table)
        expiring_box.setLayout(expiring_layout)

        layout.addWidget(summary_box)
        layout.addWidget(expiring_box)
        widget.setLayout(layout)
        return widget

    def build_dashboard_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        welcome = QLabel(f"Welcome back, {self.current_user['full_name']}!")
        welcome.setObjectName("title")
        layout.addWidget(welcome)

        cards_row = QHBoxLayout()
        self.dashboard_cards = {}
        card_defs = [
            ("members", "Active Members"),
            ("expiring", "Expiring Soon (7d)"),
            ("attendance_today", "Checked In Today"),
            ("staff", "Staff Accounts"),
        ]
        for key, label in card_defs:
            box = QGroupBox(label)
            box_layout = QVBoxLayout()
            value_label = QLabel("0")
            value_label.setObjectName("title")
            value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            box_layout.addWidget(value_label)
            box.setLayout(box_layout)
            cards_row.addWidget(box)
            self.dashboard_cards[key] = value_label
        layout.addLayout(cards_row)

        actions_box = QGroupBox("Quick Actions")
        actions_layout = QHBoxLayout()
        if "manage_members" in self.permissions:
            quick_add_member = QPushButton("Add Member")
            quick_add_member.clicked.connect(self.add_member)
            actions_layout.addWidget(quick_add_member)
        if "mark_attendance" in self.permissions:
            quick_attendance = QPushButton("Go to Attendance")
            quick_attendance.setObjectName("secondary")
            quick_attendance.clicked.connect(
                lambda: self._switch_to_tab("Attendance"))
            actions_layout.addWidget(quick_attendance)
        if "manage_users" in self.permissions:
            quick_add_user = QPushButton("Add User")
            quick_add_user.setObjectName("secondary")
            quick_add_user.clicked.connect(self.add_user)
            actions_layout.addWidget(quick_add_user)
        actions_layout.addStretch()
        actions_box.setLayout(actions_layout)
        layout.addWidget(actions_box)

        expiring_box = QGroupBox("Memberships Expiring Soon")
        expiring_layout = QVBoxLayout()
        self.dashboard_expiring_table = self._make_table(
            ["Member", "Plan", "Expiry Date"])
        expiring_layout.addWidget(self.dashboard_expiring_table)
        expiring_box.setLayout(expiring_layout)
        layout.addWidget(expiring_box)

        widget.setLayout(layout)
        return widget

    def _switch_to_tab(self, tab_label):
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == tab_label:
                self.tabs.setCurrentIndex(i)
                return

    #UI helpers

    def _toast(self, message):
        self.statusBar().showMessage(message, 4000)

    def _make_search_box(self, placeholder, table, columns=None):
        box = QLineEdit()
        box.setPlaceholderText(placeholder)
        box.textChanged.connect(
            lambda text: self._filter_table(table, text, columns))
        return box

    def _filter_table(self, table, text, columns=None):
        text = text.strip().lower()
        cols = columns if columns is not None else range(table.columnCount())
        for row in range(table.rowCount()):
            if not text:
                table.setRowHidden(row, False)
                continue
            match = False
            for col in cols:
                item = table.item(row, col)
                if item and text in item.text().lower():
                    match = True
                    break
            table.setRowHidden(row, not match)

    @staticmethod
    def _make_table(headers):
        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.setSortingEnabled(True)
        return table

    # Refresh helpers 

    def refresh_all(self):
        if hasattr(self, "dashboard_cards"):
            self.refresh_dashboard()
        if hasattr(self, "users_table"):
            self.refresh_users()
        if hasattr(self, "members_table"):
            self.refresh_members()
        if hasattr(self, "membership_types_table"):
            self.refresh_membership_types()
        if hasattr(self, "attendance_table"):
            self.refresh_attendance()
        if hasattr(self, "roles_table"):
            self.refresh_roles()
        if hasattr(self, "permissions_table"):
            self.refresh_permissions()
        if hasattr(self, "user_roles_table"):
            self.refresh_assignments()
        if hasattr(self, "reports_label"):
            self.refresh_reports()

    def refresh_users(self):
        self.users_table.setSortingEnabled(False)
        users = self.db.get_users()
        self.users_table.setRowCount(0)
        for row_idx, (uid, username, full_name, email, phone, is_active,
                      roles, created_at, last_login) in enumerate(users):
            self.users_table.insertRow(row_idx)
            self.users_table.setItem(row_idx, 0, QTableWidgetItem(str(uid)))
            self.users_table.setItem(row_idx, 1, QTableWidgetItem(username))
            self.users_table.setItem(row_idx, 2, QTableWidgetItem(full_name))
            self.users_table.setItem(row_idx, 3, QTableWidgetItem(email or ""))
            self.users_table.setItem(row_idx, 4, QTableWidgetItem(phone or ""))
            self.users_table.setItem(
                row_idx, 5, QTableWidgetItem("Yes" if is_active else "No"))
            self.users_table.setItem(row_idx, 6, QTableWidgetItem(roles))
            self.users_table.setItem(
                row_idx, 7, QTableWidgetItem(last_login or "Never"))
        self.users_table.setSortingEnabled(True)

    def refresh_members(self):
        self.members_table.setSortingEnabled(False)
        members = self.db.get_members()
        self.members_table.setRowCount(0)
        for row_idx, (mid, full_name, phone, email, join_date, status,
                      mt_id, type_name, start, expiry, notes) in enumerate(members):
            self.members_table.insertRow(row_idx)
            self.members_table.setItem(row_idx, 0, QTableWidgetItem(str(mid)))
            self.members_table.setItem(row_idx, 1, QTableWidgetItem(full_name))
            self.members_table.setItem(
                row_idx, 2, QTableWidgetItem(phone or ""))
            self.members_table.setItem(
                row_idx, 3, QTableWidgetItem(email or ""))
            self.members_table.setItem(row_idx, 4, QTableWidgetItem(type_name))
            self.members_table.setItem(
                row_idx, 5, QTableWidgetItem(start or ""))

            expiry_item = QTableWidgetItem(expiry or "-")
            if expiry:
                try:
                    if datetime.strptime(expiry, "%Y-%m-%d") < datetime.now():
                        expiry_item.setForeground(Qt.GlobalColor.red)
                except ValueError:
                    pass
            self.members_table.setItem(row_idx, 6, expiry_item)
            self.members_table.setItem(
                row_idx, 7, QTableWidgetItem(status or ""))
        self.members_table.setSortingEnabled(True)

        # Keep the attendance member dropdown in sync
        if hasattr(self, "attendance_member_combo"):
            current = self.attendance_member_combo.currentData()
            self.attendance_member_combo.clear()
            for mid, full_name, *_ in members:
                self.attendance_member_combo.addItem(full_name, mid)
            if current is not None:
                idx = self.attendance_member_combo.findData(current)
                if idx >= 0:
                    self.attendance_member_combo.setCurrentIndex(idx)

    def refresh_membership_types(self):
        self.membership_types_table.setSortingEnabled(False)
        types_ = self.db.get_membership_types()
        self.membership_types_table.setRowCount(0)
        for row_idx, (tid, type_name, duration_days, price, description) in enumerate(types_):
            self.membership_types_table.insertRow(row_idx)
            self.membership_types_table.setItem(
                row_idx, 0, QTableWidgetItem(str(tid)))
            self.membership_types_table.setItem(
                row_idx, 1, QTableWidgetItem(type_name))
            self.membership_types_table.setItem(
                row_idx, 2, QTableWidgetItem(str(duration_days)))
            self.membership_types_table.setItem(
                row_idx, 3, QTableWidgetItem(f"${price:.2f}"))
            self.membership_types_table.setItem(
                row_idx, 4, QTableWidgetItem(description or ""))
        self.membership_types_table.setSortingEnabled(True)

    def refresh_attendance(self):
        self.attendance_table.setSortingEnabled(False)
        attendance_date = None
        if hasattr(self, "attendance_show_all") and not self.attendance_show_all.isChecked():
            attendance_date = self.attendance_date_filter.date().toString(DATE_FORMAT)
        records = self.db.get_attendance(attendance_date=attendance_date)
        self.attendance_table.setRowCount(0)
        for row_idx, (aid, member_id, full_name, attendance_date_val,
                      check_in_time, status, marked_by) in enumerate(records):
            self.attendance_table.insertRow(row_idx)
            self.attendance_table.setItem(
                row_idx, 0, QTableWidgetItem(str(aid)))
            self.attendance_table.setItem(
                row_idx, 1, QTableWidgetItem(full_name))
            self.attendance_table.setItem(
                row_idx, 2, QTableWidgetItem(attendance_date_val))
            self.attendance_table.setItem(
                row_idx, 3, QTableWidgetItem(check_in_time or ""))
            status_item = QTableWidgetItem(status)
            if status == "absent":
                status_item.setForeground(Qt.GlobalColor.red)
            self.attendance_table.setItem(row_idx, 4, status_item)
        self.attendance_table.setSortingEnabled(True)

    def refresh_roles(self):
        self.roles_table.setSortingEnabled(False)
        roles = self.db.get_roles()
        self.roles_table.setRowCount(0)
        for row_idx, (rid, role_name, description) in enumerate(roles):
            self.roles_table.insertRow(row_idx)
            self.roles_table.setItem(row_idx, 0, QTableWidgetItem(str(rid)))
            self.roles_table.setItem(row_idx, 1, QTableWidgetItem(role_name))
            self.roles_table.setItem(
                row_idx, 2, QTableWidgetItem(description or ""))
        self.roles_table.setSortingEnabled(True)

    def refresh_permissions(self):
        self.permissions_table.setSortingEnabled(False)
        perms = self.db.get_permissions()
        self.permissions_table.setRowCount(0)
        for row_idx, (pid, key, description) in enumerate(perms):
            self.permissions_table.insertRow(row_idx)
            self.permissions_table.setItem(
                row_idx, 0, QTableWidgetItem(str(pid)))
            self.permissions_table.setItem(
                row_idx, 1, QTableWidgetItem(key))
            self.permissions_table.setItem(
                row_idx, 2, QTableWidgetItem(description or ""))
        self.permissions_table.setSortingEnabled(True)

    def refresh_assignments(self):
        self.user_roles_table.setSortingEnabled(False)
        self.role_permissions_table.setSortingEnabled(False)
        user_roles = self.db.get_user_role_assignments()
        self.user_roles_table.setRowCount(0)
        for row_idx, (uid, username, rid, role_name) in enumerate(user_roles):
            self.user_roles_table.insertRow(row_idx)
            self.user_roles_table.setItem(
                row_idx, 0, QTableWidgetItem(str(uid)))
            self.user_roles_table.setItem(
                row_idx, 1, QTableWidgetItem(username))
            self.user_roles_table.setItem(
                row_idx, 2, QTableWidgetItem(str(rid)))
            self.user_roles_table.setItem(
                row_idx, 3, QTableWidgetItem(role_name))
        self.user_roles_table.setSortingEnabled(True)

        role_perms = self.db.get_role_permission_assignments()
        self.role_permissions_table.setRowCount(0)
        for row_idx, (rid, role_name, pid, perm_key) in enumerate(role_perms):
            self.role_permissions_table.insertRow(row_idx)
            self.role_permissions_table.setItem(
                row_idx, 0, QTableWidgetItem(str(rid)))
            self.role_permissions_table.setItem(
                row_idx, 1, QTableWidgetItem(role_name))
            self.role_permissions_table.setItem(
                row_idx, 2, QTableWidgetItem(str(pid)))
            self.role_permissions_table.setItem(
                row_idx, 3, QTableWidgetItem(perm_key))
        self.role_permissions_table.setSortingEnabled(True)

    def refresh_reports(self):
        users = self.db.get_users()
        roles = self.db.get_roles()
        perms = self.db.get_permissions()
        members = self.db.get_members()
        active_users = sum(1 for u in users if u[5])
        active_members = sum(1 for m in members if m[5] == "active")
        text = (
            f"Total users: {len(users)} (active: {active_users})\n"
            f"Total roles: {len(roles)}\n"
            f"Total permissions: {len(perms)}\n"
            f"Total members: {len(members)} (active: {active_members})"
        )
        self.reports_label.setText(text)
        self._populate_expiring_table(self.expiring_table, members)

    def refresh_dashboard(self):
        if not hasattr(self, "dashboard_cards"):
            return
        members = self.db.get_members()
        active_members = [m for m in members if m[5] == "active"]
        expiring = self._members_expiring_soon(members)
        today = datetime.now().strftime("%Y-%m-%d")
        today_attendance = self.db.get_attendance(attendance_date=today)
        users = self.db.get_users()

        self.dashboard_cards["members"].setText(str(len(active_members)))
        self.dashboard_cards["expiring"].setText(str(len(expiring)))
        self.dashboard_cards["attendance_today"].setText(
            str(len(today_attendance)))
        self.dashboard_cards["staff"].setText(str(len(users)))

        self._populate_expiring_table(self.dashboard_expiring_table, members)

    @staticmethod
    def _members_expiring_soon(members, days=7):
        soon = datetime.now() + timedelta(days=days)
        results = []
        for m in members:
            expiry = m[9]
            if not expiry:
                continue
            try:
                expiry_dt = datetime.strptime(expiry, "%Y-%m-%d")
            except ValueError:
                continue
            if datetime.now() <= expiry_dt <= soon:
                results.append(m)
        return results

    def _populate_expiring_table(self, table, members):
        expiring = self._members_expiring_soon(members)
        table.setSortingEnabled(False)
        table.setRowCount(0)
        for row_idx, m in enumerate(expiring):
            table.insertRow(row_idx)
            table.setItem(row_idx, 0, QTableWidgetItem(m[1]))
            table.setItem(row_idx, 1, QTableWidgetItem(m[7]))
            expiry_item = QTableWidgetItem(m[9])
            expiry_item.setForeground(Qt.GlobalColor.yellow)
            table.setItem(row_idx, 2, expiry_item)
        table.setSortingEnabled(True)

    #  Selection helpers

    def _selected_row_value(self, table, column):
        row = table.currentRow()
        if row < 0:
            return None
        item = table.item(row, column)
        return item.text() if item else None

    # User actions 

    def add_user(self):
        dialog = UserDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if not data["username"] or not data["password"]:
                QMessageBox.warning(
                    self, "Missing Data", "Username and password are required.")
                return
            try:
                self.db.create_user(
                    data["username"], data["full_name"],
                    data["password"], data["is_active"],
                    data["email"], data["phone"]
                )
                self.refresh_users()
                self.refresh_assignments()
                self.refresh_dashboard()
                self._toast(f"User '{data['username']}' created.")
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Could not create user: {e}")

    def edit_user(self):
        uid = self._selected_row_value(self.users_table, 0)
        if uid is None:
            QMessageBox.information(
                self, "No Selection", "Select a user first.")
            return
        row = self.users_table.currentRow()
        user_tuple = (
            int(uid),
            self.users_table.item(row, 1).text(),
            self.users_table.item(row, 2).text(),
            self.users_table.item(row, 3).text(),
            self.users_table.item(row, 4).text(),
            1 if self.users_table.item(row, 5).text() == "Yes" else 0,
            self.users_table.item(row, 6).text(),
            None,
            self.users_table.item(row, 7).text(),
        )
        dialog = UserDialog(self, user=user_tuple)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                self.db.update_user(
                    int(uid), data["full_name"],
                    data["password"] if data["password"] else None,
                    data["is_active"], data["email"], data["phone"]
                )
                self.refresh_users()
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Could not update user: {e}")

    def delete_user(self):
        uid = self._selected_row_value(self.users_table, 0)
        if uid is None:
            QMessageBox.information(
                self, "No Selection", "Select a user first.")
            return
        confirm = QMessageBox.question(
            self, "Confirm Delete", "Delete this user? This cannot be undone.")
        if confirm == QMessageBox.StandardButton.Yes:
            self.db.delete_user(int(uid))
            self.refresh_users()
            self.refresh_assignments()

    #  Member actions
    def add_member(self):
        membership_types = self.db.get_membership_types()
        dialog = MemberDialog(self, membership_types=membership_types)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if not data["full_name"]:
                QMessageBox.warning(
                    self, "Missing Data", "Full name is required.")
                return
            try:
                self.db.create_member(
                    data["full_name"], data["phone"], data["email"],
                    data["status"], data["membership_type_id"],
                    data["membership_start"], data["notes"]
                )
                self.refresh_members()
                self.refresh_dashboard()
                self._toast(f"Member '{data['full_name']}' added.")
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Could not create member: {e}")

    def edit_member(self):
        mid = self._selected_row_value(self.members_table, 0)
        if mid is None:
            QMessageBox.information(
                self, "No Selection", "Select a member first.")
            return
        member_tuple = self.db.get_member(int(mid))
        if not member_tuple:
            return
        membership_types = self.db.get_membership_types()
        dialog = MemberDialog(self, member=member_tuple,
                              membership_types=membership_types)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                self.db.update_member(
                    int(mid), data["full_name"], data["phone"], data["email"],
                    data["status"], data["membership_type_id"],
                    data["membership_start"], data["notes"]
                )
                self.refresh_members()
                self.refresh_dashboard()
                self._toast(f"Member '{data['full_name']}' updated.")
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Could not update member: {e}")

    def delete_member(self):
        mid = self._selected_row_value(self.members_table, 0)
        if mid is None:
            QMessageBox.information(
                self, "No Selection", "Select a member first.")
            return
        confirm = QMessageBox.question(
            self, "Confirm Delete", "Delete this member? This cannot be undone.")
        if confirm == QMessageBox.StandardButton.Yes:
            self.db.delete_member(int(mid))
            self.refresh_members()
            self.refresh_dashboard()
            self._toast("Member deleted.")

    #Membership type actions

    def add_membership_type(self):
        dialog = MembershipTypeDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if not data["type_name"]:
                QMessageBox.warning(
                    self, "Missing Data", "Plan name is required.")
                return
            try:
                self.db.create_membership_type(
                    data["type_name"], data["duration_days"],
                    data["price"], data["description"]
                )
                self.refresh_membership_types()
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Could not create plan: {e}")

    def edit_membership_type(self):
        tid = self._selected_row_value(self.membership_types_table, 0)
        if tid is None:
            QMessageBox.information(
                self, "No Selection", "Select a plan first.")
            return
        row = self.membership_types_table.currentRow()
        price_text = self.membership_types_table.item(
            row, 3).text().replace("$", "")
        type_tuple = (
            int(tid),
            self.membership_types_table.item(row, 1).text(),
            int(self.membership_types_table.item(row, 2).text()),
            float(price_text or 0),
            self.membership_types_table.item(row, 4).text(),
        )
        dialog = MembershipTypeDialog(self, membership_type=type_tuple)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                self.db.update_membership_type(
                    int(tid), data["type_name"], data["duration_days"],
                    data["price"], data["description"]
                )
                self.refresh_membership_types()
                self.refresh_members()
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Could not update plan: {e}")

    def delete_membership_type(self):
        tid = self._selected_row_value(self.membership_types_table, 0)
        if tid is None:
            QMessageBox.information(
                self, "No Selection", "Select a plan first.")
            return
        confirm = QMessageBox.question(
            self, "Confirm Delete",
            "Delete this plan? Members on this plan will be unassigned.")
        if confirm == QMessageBox.StandardButton.Yes:
            self.db.delete_membership_type(int(tid))
            self.refresh_membership_types()
            self.refresh_members()

    #Attendance actions

    def mark_attendance(self):
        member_id = self.attendance_member_combo.currentData()
        if member_id is None:
            QMessageBox.information(
                self, "No Members", "There are no members to mark attendance for.")
            return
        status = self.attendance_status_combo.currentText()
        try:
            self.db.mark_attendance(
                member_id, self.current_user["id"], status)
            self.refresh_attendance()
            self.refresh_dashboard()
            self._toast(f"Attendance marked: {status}.")
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Could not mark attendance: {e}")

    def delete_attendance_record(self):
        aid = self._selected_row_value(self.attendance_table, 0)
        if aid is None:
            QMessageBox.information(
                self, "No Selection", "Select an attendance record first.")
            return
        confirm = QMessageBox.question(
            self, "Confirm Delete", "Delete this attendance record?")
        if confirm == QMessageBox.StandardButton.Yes:
            self.db.delete_attendance(int(aid))
            self.refresh_attendance()

    #Role actions

    def add_role(self):
        dialog = RoleDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if not data["role_name"]:
                QMessageBox.warning(self, "Missing Data",
                                    "Role name is required.")
                return
            try:
                self.db.create_role(data["role_name"], data["description"])
                self.refresh_roles()
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Could not create role: {e}")

    def edit_role(self):
        rid = self._selected_row_value(self.roles_table, 0)
        if rid is None:
            QMessageBox.information(
                self, "No Selection", "Select a role first.")
            return
        row = self.roles_table.currentRow()
        role_tuple = (
            int(rid),
            self.roles_table.item(row, 1).text(),
            self.roles_table.item(row, 2).text(),
        )
        dialog = RoleDialog(self, role=role_tuple)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                self.db.update_role(
                    int(rid), data["role_name"], data["description"])
                self.refresh_roles()
                self.refresh_assignments()
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Could not update role: {e}")

    def delete_role(self):
        rid = self._selected_row_value(self.roles_table, 0)
        if rid is None:
            QMessageBox.information(
                self, "No Selection", "Select a role first.")
            return
        confirm = QMessageBox.question(
            self, "Confirm Delete", "Delete this role? This cannot be undone.")
        if confirm == QMessageBox.StandardButton.Yes:
            self.db.delete_role(int(rid))
            self.refresh_roles()
            self.refresh_assignments()

    #Permission actions

    def add_permission(self):
        dialog = PermissionDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if not data["permission_key"]:
                QMessageBox.warning(
                    self, "Missing Data", "Permission key is required.")
                return
            try:
                self.db.create_permission(
                    data["permission_key"], data["description"])
                self.refresh_permissions()
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Could not create permission: {e}")

    def edit_permission(self):
        pid = self._selected_row_value(self.permissions_table, 0)
        if pid is None:
            QMessageBox.information(
                self, "No Selection", "Select a permission first.")
            return
        row = self.permissions_table.currentRow()
        perm_tuple = (
            int(pid),
            self.permissions_table.item(row, 1).text(),
            self.permissions_table.item(row, 2).text(),
        )
        dialog = PermissionDialog(self, permission=perm_tuple)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                self.db.update_permission(
                    int(pid), data["permission_key"], data["description"])
                self.refresh_permissions()
                self.refresh_assignments()
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Could not update permission: {e}")

    def delete_permission(self):
        pid = self._selected_row_value(self.permissions_table, 0)
        if pid is None:
            QMessageBox.information(
                self, "No Selection", "Select a permission first.")
            return
        confirm = QMessageBox.question(
            self, "Confirm Delete", "Delete this permission? This cannot be undone.")
        if confirm == QMessageBox.StandardButton.Yes:
            self.db.delete_permission(int(pid))
            self.refresh_permissions()
            self.refresh_assignments()

    #Assignment actions

    def assign_role_to_user(self):
        users = self.db.get_users()
        roles = self.db.get_roles()
        if not users or not roles:
            QMessageBox.information(
                self, "Unavailable", "Need at least one user and one role.")
            return

        user_dialog = RoleSelectDialog(
            "Select User", [(u[0], f"{u[1]} ({u[2]})") for u in users], self)
        if user_dialog.exec() != QDialog.DialogCode.Accepted:
            return
        user_id = user_dialog.selected_id

        role_dialog = RoleSelectDialog(
            "Select Role", [(r[0], r[1]) for r in roles], self)
        if role_dialog.exec() != QDialog.DialogCode.Accepted:
            return
        role_id = role_dialog.selected_id

        self.db.assign_role_to_user(user_id, role_id)
        self.refresh_assignments()
        self.refresh_users()

    def remove_role_from_user(self):
        row = self.user_roles_table.currentRow()
        if row < 0:
            QMessageBox.information(
                self, "No Selection", "Select a user-role assignment first.")
            return
        user_id = int(self.user_roles_table.item(row, 0).text())
        role_id = int(self.user_roles_table.item(row, 2).text())
        confirm = QMessageBox.question(
            self, "Confirm Remove", "Remove this role from the user?")
        if confirm == QMessageBox.StandardButton.Yes:
            self.db.remove_role_from_user(user_id, role_id)
            self.refresh_assignments()
            self.refresh_users()

    def assign_permission_to_role(self):
        roles = self.db.get_roles()
        perms = self.db.get_permissions()
        if not roles or not perms:
            QMessageBox.information(
                self, "Unavailable", "Need at least one role and one permission.")
            return

        role_dialog = RoleSelectDialog(
            "Select Role", [(r[0], r[1]) for r in roles], self)
        if role_dialog.exec() != QDialog.DialogCode.Accepted:
            return
        role_id = role_dialog.selected_id

        perm_dialog = RoleSelectDialog(
            "Select Permission", [(p[0], p[1]) for p in perms], self)
        if perm_dialog.exec() != QDialog.DialogCode.Accepted:
            return
        permission_id = perm_dialog.selected_id

        self.db.assign_permission_to_role(role_id, permission_id)
        self.refresh_assignments()

    def remove_permission_from_role(self):
        row = self.role_permissions_table.currentRow()
        if row < 0:
            QMessageBox.information(
                self, "No Selection", "Select a role-permission assignment first.")
            return
        role_id = int(self.role_permissions_table.item(row, 0).text())
        permission_id = int(self.role_permissions_table.item(row, 2).text())
        confirm = QMessageBox.question(
            self, "Confirm Remove", "Remove this permission from the role?")
        if confirm == QMessageBox.StandardButton.Yes:
            self.db.remove_permission_from_role(role_id, permission_id)
            self.refresh_assignments()

    # Misc

    def logout(self):
        confirm = QMessageBox.question(
            self, "Confirm Logout", "Are you sure you want to log out?")
        if confirm == QMessageBox.StandardButton.Yes:
            self.close()
