import os
import sqlite3
from datetime import datetime, timedelta
from module.auth import generate_salt, hash_password, verify_password


class DatabaseManager:
    def __init__(self, db_name="gym.db"):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.join(base_dir, db_name)
        self.create_tables()
        self.migrate()
        self.seed_data()

    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    # ---------- Schema ----------

    def create_tables(self):
        with self.connect() as conn:
            cur = conn.cursor()

            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    full_name TEXT NOT NULL,
                    email TEXT,
                    phone TEXT,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_login TEXT
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS roles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role_name TEXT NOT NULL UNIQUE,
                    description TEXT
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS permissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    permission_key TEXT NOT NULL UNIQUE,
                    description TEXT
                )
            """)

            # Members are standalone records - no login/user account required.
            cur.execute("""
                CREATE TABLE IF NOT EXISTS membership_types (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type_name TEXT NOT NULL UNIQUE,
                    duration_days INTEGER NOT NULL DEFAULT 30,
                    price REAL DEFAULT 0,
                    description TEXT
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS members (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    phone TEXT,
                    email TEXT,
                    join_date TEXT DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    membership_type_id INTEGER,
                    membership_start TEXT,
                    membership_expiry TEXT,
                    notes TEXT,
                    FOREIGN KEY(membership_type_id) REFERENCES membership_types(id) ON DELETE SET NULL
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    member_id INTEGER NOT NULL,
                    attendance_date TEXT NOT NULL DEFAULT CURRENT_DATE,
                    check_in_time TEXT DEFAULT CURRENT_TIMESTAMP,
                    marked_by_user_id INTEGER,
                    status TEXT NOT NULL DEFAULT 'present',
                    FOREIGN KEY(member_id) REFERENCES members(id) ON DELETE CASCADE,
                    FOREIGN KEY(marked_by_user_id) REFERENCES users(id) ON DELETE SET NULL,
                    UNIQUE(member_id, attendance_date)
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_roles (
                    user_id INTEGER NOT NULL,
                    role_id INTEGER NOT NULL,
                    PRIMARY KEY (user_id, role_id),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS role_permissions (
                    role_id INTEGER NOT NULL,
                    permission_id INTEGER NOT NULL,
                    PRIMARY KEY (role_id, permission_id),
                    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
                    FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE
                )
            """)

    def migrate(self):
        """Lightweight migrations for databases created before email/phone
        columns or the standalone members redesign existed."""
        with self.connect() as conn:
            cur = conn.cursor()

            # users: add email/phone if missing
            cur.execute("PRAGMA table_info(users)")
            user_cols = {row[1] for row in cur.fetchall()}
            if "email" not in user_cols:
                cur.execute("ALTER TABLE users ADD COLUMN email TEXT")
            if "phone" not in user_cols:
                cur.execute("ALTER TABLE users ADD COLUMN phone TEXT")

            # members: if the old schema (user_id-linked) is present, migrate
            # to the new standalone schema, preserving full_name/phone/status.
            cur.execute("PRAGMA table_info(members)")
            member_cols = {row[1] for row in cur.fetchall()}
            if "user_id" in member_cols:
                cur.execute("""
                    SELECT m.id, u.full_name, m.phone, m.join_date, m.status
                    FROM members m JOIN users u ON m.user_id = u.id
                """)
                old_members = cur.fetchall()
                cur.execute("ALTER TABLE members RENAME TO members_old")
                cur.execute("""
                    CREATE TABLE members (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        full_name TEXT NOT NULL,
                        phone TEXT,
                        email TEXT,
                        join_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        status TEXT DEFAULT 'active',
                        membership_type_id INTEGER,
                        membership_start TEXT,
                        membership_expiry TEXT,
                        notes TEXT,
                        FOREIGN KEY(membership_type_id) REFERENCES membership_types(id) ON DELETE SET NULL
                    )
                """)
                for _, full_name, phone, join_date, status in old_members:
                    cur.execute("""
                        INSERT INTO members (full_name, phone, join_date, status)
                        VALUES (?, ?, ?, ?)
                    """, (full_name, phone, join_date, status))
                cur.execute("DROP TABLE members_old")

            conn.commit()

    def seed_data(self):
        with self.connect() as conn:
            cur = conn.cursor()

            cur.execute("SELECT COUNT(*) FROM users")
            if cur.fetchone()[0] > 0:
                self._seed_membership_types(cur)
                conn.commit()
                return

            roles = [
                ("Admin", "Full system administrator"),
                ("Staff", "Can manage users, members and assign trainers"),
                ("Trainer", "Can view members and mark attendance")
            ]

            permissions = [
                ("manage_users", "Create, update, delete staff/admin users"),
                ("manage_roles", "Create, update, delete roles"),
                ("manage_permissions", "Create, update, delete permissions"),
                ("assign_roles", "Assign roles to users"),
                ("assign_permissions", "Assign permissions to roles"),
                ("manage_members", "Create, update, delete gym members"),
                ("manage_membership_types", "Create, update, delete membership plans"),
                ("mark_attendance", "Mark and view member attendance"),
                ("view_reports", "View system reports")
            ]

            cur.executemany(
                "INSERT INTO roles (role_name, description) VALUES (?, ?)",
                roles
            )
            cur.executemany(
                "INSERT INTO permissions (permission_key, description) VALUES (?, ?)",
                permissions
            )

            self._insert_user(
                cur, "admin", "System Administrator", "admin123", 1
            )
            self._insert_user(cur, "staff", "Staff User", "staff123", 1)
            self._insert_user(cur, "trainer", "Trainer User", "trainer123", 1)

            admin_role_id = self.get_role_id_by_name("Admin", conn)
            staff_role_id = self.get_role_id_by_name("Staff", conn)
            trainer_role_id = self.get_role_id_by_name("Trainer", conn)

            admin_id = self.get_user_id_by_username("admin", conn)
            staff_id = self.get_user_id_by_username("staff", conn)
            trainer_id = self.get_user_id_by_username("trainer", conn)

            cur.execute(
                "INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)",
                (admin_id, admin_role_id)
            )
            cur.execute(
                "INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)",
                (staff_id, staff_role_id)
            )
            cur.execute(
                "INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)",
                (trainer_id, trainer_role_id)
            )

            cur.execute("SELECT id FROM permissions")
            all_permission_ids = [row[0] for row in cur.fetchall()]
            for permission_id in all_permission_ids:
                cur.execute(
                    "INSERT INTO role_permissions (role_id, permission_id) VALUES (?, ?)",
                    (admin_role_id, permission_id)
                )

            staff_permission_keys = [
                "manage_users", "manage_members", "manage_membership_types",
                "view_reports"
            ]
            for key in staff_permission_keys:
                pid = self.get_permission_id_by_key(key, conn)
                cur.execute(
                    "INSERT INTO role_permissions (role_id, permission_id) VALUES (?, ?)",
                    (staff_role_id, pid)
                )

            trainer_permission_keys = ["mark_attendance", "view_reports"]
            for key in trainer_permission_keys:
                pid = self.get_permission_id_by_key(key, conn)
                cur.execute(
                    "INSERT INTO role_permissions (role_id, permission_id) VALUES (?, ?)",
                    (trainer_role_id, pid)
                )

            self._seed_membership_types(cur)

            conn.commit()

    def _seed_membership_types(self, cur):
        cur.execute("SELECT COUNT(*) FROM membership_types")
        if cur.fetchone()[0] > 0:
            return
        default_types = [
            ("Monthly", 30, 30.0, "Standard monthly membership"),
            ("Quarterly", 90, 80.0, "3-month membership"),
            ("Annual", 365, 280.0, "12-month membership"),
        ]
        cur.executemany(
            "INSERT INTO membership_types (type_name, duration_days, price, description) VALUES (?, ?, ?, ?)",
            default_types
        )

    def _insert_user(self, cur, username, full_name, password, is_active=1,
                     email="", phone=""):
        salt = generate_salt()
        password_hash = hash_password(password, salt)
        cur.execute(
            "INSERT INTO users (username, full_name, email, phone, password_hash, salt, is_active) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (username, full_name, email, phone, password_hash, salt, is_active)
        )

    # ---------- Auth ----------

    def authenticate(self, username, password):
        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, username, full_name, password_hash, salt, is_active FROM users WHERE username=?", (username,))
            row = cur.fetchone()
            if not row or row[5] != 1:
                return None
            if verify_password(password, row[4], row[3]):
                cur.execute(
                    "UPDATE users SET last_login=CURRENT_TIMESTAMP WHERE id=?", (row[0],))
                conn.commit()
                return {"id": row[0], "username": row[1], "full_name": row[2]}
            return None

    def get_user_permissions(self, user_id):
        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT DISTINCT p.permission_key
                FROM permissions p
                JOIN role_permissions rp ON p.id = rp.permission_id
                JOIN user_roles ur ON rp.role_id = ur.role_id
                WHERE ur.user_id = ?
            """, (user_id,))
            return [row[0] for row in cur.fetchall()]

    def get_user_id_by_username(self, username, conn=None):
        close = False
        if conn is None:
            conn = self.connect()
            close = True
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE username=?", (username,))
        row = cur.fetchone()
        if close:
            conn.close()
        return row[0] if row else None

    def get_role_id_by_name(self, role_name, conn=None):
        close = False
        if conn is None:
            conn = self.connect()
            close = True
        cur = conn.cursor()
        cur.execute("SELECT id FROM roles WHERE role_name=?", (role_name,))
        row = cur.fetchone()
        if close:
            conn.close()
        return row[0] if row else None

    def get_permission_id_by_key(self, permission_key, conn=None):
        close = False
        if conn is None:
            conn = self.connect()
            close = True
        cur = conn.cursor()
        cur.execute("SELECT id FROM permissions WHERE permission_key=?",
                    (permission_key,))
        row = cur.fetchone()
        if close:
            conn.close()
        return row[0] if row else None

    # ---------- Users (staff/admin/trainer accounts) ----------

    def get_users(self):
        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT u.id, u.username, u.full_name, u.email, u.phone, u.is_active,
                    IFNULL(GROUP_CONCAT(r.role_name, ', '), '-') AS roles,
                    u.created_at, u.last_login
                FROM users u
                LEFT JOIN user_roles ur ON u.id = ur.user_id
                LEFT JOIN roles r ON ur.role_id = r.id
                GROUP BY u.id
                ORDER BY u.id DESC
            """)
            return cur.fetchall()

    def create_user(self, username, full_name, password, is_active=1, email="", phone=""):
        with self.connect() as conn:
            cur = conn.cursor()
            self._insert_user(cur, username, full_name,
                              password, is_active, email, phone)
            conn.commit()
            return cur.lastrowid

    def update_user(self, user_id, full_name, password=None, is_active=1, email="", phone=""):
        with self.connect() as conn:
            cur = conn.cursor()
            if password:
                salt = generate_salt()
                password_hash = hash_password(password, salt)
                cur.execute("""
                    UPDATE users SET full_name=?, email=?, phone=?, password_hash=?, salt=?, is_active=? WHERE id=?
                """, (full_name, email, phone, password_hash, salt, is_active, user_id))
            else:
                cur.execute("""
                    UPDATE users SET full_name=?, email=?, phone=?, is_active=? WHERE id=?
                """, (full_name, email, phone, is_active, user_id))
            conn.commit()

    def delete_user(self, user_id):
        with self.connect() as conn:
            conn.execute("DELETE FROM users WHERE id=?", (user_id,))
            conn.commit()

    def get_roles(self):
        with self.connect() as conn:
            return conn.execute("SELECT id, role_name, description FROM roles ORDER BY id DESC").fetchall()

    def create_role(self, role_name, description):
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO roles (role_name, description) VALUES (?, ?)", (role_name, description))
            conn.commit()

    def update_role(self, role_id, role_name, description):
        with self.connect() as conn:
            conn.execute("UPDATE roles SET role_name=?, description=? WHERE id=?",
                         (role_name, description, role_id))
            conn.commit()

    def delete_role(self, role_id):
        with self.connect() as conn:
            conn.execute("DELETE FROM roles WHERE id=?", (role_id,))
            conn.commit()

    def get_permissions(self):
        with self.connect() as conn:
            return conn.execute("SELECT id, permission_key, description FROM permissions ORDER BY id DESC").fetchall()

    def create_permission(self, permission_key, description):
        with self.connect() as conn:
            conn.execute("INSERT INTO permissions (permission_key, description) VALUES (?, ?)",
                         (permission_key, description))
            conn.commit()

    def update_permission(self, permission_id, permission_key, description):
        with self.connect() as conn:
            conn.execute("UPDATE permissions SET permission_key=?, description=? WHERE id=?",
                         (permission_key, description, permission_id))
            conn.commit()

    def delete_permission(self, permission_id):
        with self.connect() as conn:
            conn.execute("DELETE FROM permissions WHERE id=?",
                         (permission_id,))
            conn.commit()

    def assign_role_to_user(self, user_id, role_id):
        with self.connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO user_roles (user_id, role_id) VALUES (?, ?)", (user_id, role_id))
            conn.commit()

    def remove_role_from_user(self, user_id, role_id):
        with self.connect() as conn:
            conn.execute(
                "DELETE FROM user_roles WHERE user_id=? AND role_id=?", (user_id, role_id))
            conn.commit()

    def assign_permission_to_role(self, role_id, permission_id):
        with self.connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO role_permissions (role_id, permission_id) VALUES (?, ?)", (role_id, permission_id))
            conn.commit()

    def remove_permission_from_role(self, role_id, permission_id):
        with self.connect() as conn:
            conn.execute(
                "DELETE FROM role_permissions WHERE role_id=? AND permission_id=?", (role_id, permission_id))
            conn.commit()

    def get_user_role_assignments(self):
        with self.connect() as conn:
            return conn.execute("""
                SELECT u.id, u.username, r.id, r.role_name
                FROM user_roles ur
                JOIN users u ON ur.user_id = u.id
                JOIN roles r ON ur.role_id = r.id
                ORDER BY u.username
            """).fetchall()

    def get_role_permission_assignments(self):
        with self.connect() as conn:
            return conn.execute("""
                SELECT r.id, r.role_name, p.id, p.permission_key
                FROM role_permissions rp
                JOIN roles r ON rp.role_id = r.id
                JOIN permissions p ON rp.permission_id = p.id
                ORDER BY r.role_name
            """).fetchall()

    # ---------- Membership types ----------

    def get_membership_types(self):
        with self.connect() as conn:
            return conn.execute("""
                SELECT id, type_name, duration_days, price, description
                FROM membership_types ORDER BY duration_days
            """).fetchall()

    def create_membership_type(self, type_name, duration_days, price=0.0, description=""):
        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO membership_types (type_name, duration_days, price, description) VALUES (?, ?, ?, ?)",
                (type_name, duration_days, price, description)
            )
            conn.commit()
            return cur.lastrowid

    def update_membership_type(self, type_id, type_name, duration_days, price=0.0, description=""):
        with self.connect() as conn:
            conn.execute("""
                UPDATE membership_types SET type_name=?, duration_days=?, price=?, description=?
                WHERE id=?
            """, (type_name, duration_days, price, description, type_id))
            conn.commit()

    def delete_membership_type(self, type_id):
        with self.connect() as conn:
            conn.execute(
                "DELETE FROM membership_types WHERE id=?", (type_id,))
            conn.commit()

    # ---------- Members (standalone, no login) ----------

    def get_members(self):
        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT m.id, m.full_name, m.phone, m.email, m.join_date, m.status,
                    m.membership_type_id, IFNULL(mt.type_name, '-'),
                    m.membership_start, m.membership_expiry, m.notes
                FROM members m
                LEFT JOIN membership_types mt ON m.membership_type_id = mt.id
                ORDER BY m.id DESC
            """)
            return cur.fetchall()

    def get_member(self, member_id):
        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT m.id, m.full_name, m.phone, m.email, m.join_date, m.status,
                    m.membership_type_id, IFNULL(mt.type_name, '-'),
                    m.membership_start, m.membership_expiry, m.notes
                FROM members m
                LEFT JOIN membership_types mt ON m.membership_type_id = mt.id
                WHERE m.id=?
            """, (member_id,))
            return cur.fetchone()

    def create_member(self, full_name, phone="", email="", status="active",
                      membership_type_id=None, membership_start=None, notes=""):
        expiry = self._calc_expiry(membership_type_id, membership_start)
        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO members
                    (full_name, phone, email, status, membership_type_id,
                     membership_start, membership_expiry, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (full_name, phone, email, status, membership_type_id,
                  membership_start, expiry, notes))
            conn.commit()
            return cur.lastrowid

    def update_member(self, member_id, full_name, phone="", email="", status="active",
                      membership_type_id=None, membership_start=None, notes=""):
        expiry = self._calc_expiry(membership_type_id, membership_start)
        with self.connect() as conn:
            conn.execute("""
                UPDATE members SET full_name=?, phone=?, email=?, status=?,
                    membership_type_id=?, membership_start=?, membership_expiry=?, notes=?
                WHERE id=?
            """, (full_name, phone, email, status, membership_type_id,
                  membership_start, expiry, notes, member_id))
            conn.commit()

    def delete_member(self, member_id):
        with self.connect() as conn:
            conn.execute("DELETE FROM members WHERE id=?", (member_id,))
            conn.commit()

    def _calc_expiry(self, membership_type_id, membership_start):
        if not membership_type_id or not membership_start:
            return None
        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT duration_days FROM membership_types WHERE id=?",
                (membership_type_id,)
            )
            row = cur.fetchone()
        if not row:
            return None
        try:
            start = datetime.strptime(membership_start, "%Y-%m-%d")
        except ValueError:
            return None
        expiry = start + timedelta(days=row[0])
        return expiry.strftime("%Y-%m-%d")

    # ---------- Attendance ----------

    def mark_attendance(self, member_id, marked_by_user_id, status="present", attendance_date=None):
        attendance_date = attendance_date or datetime.now().strftime("%Y-%m-%d")
        with self.connect() as conn:
            conn.execute("""
                INSERT INTO attendance (member_id, attendance_date, marked_by_user_id, status)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(member_id, attendance_date)
                DO UPDATE SET status=excluded.status,
                    marked_by_user_id=excluded.marked_by_user_id,
                    check_in_time=CURRENT_TIMESTAMP
            """, (member_id, attendance_date, marked_by_user_id, status))
            conn.commit()

    def get_attendance(self, attendance_date=None, member_id=None):
        query = """
            SELECT a.id, a.member_id, m.full_name, a.attendance_date,
                a.check_in_time, a.status, IFNULL(u.username, '-')
            FROM attendance a
            JOIN members m ON a.member_id = m.id
            LEFT JOIN users u ON a.marked_by_user_id = u.id
            WHERE 1=1
        """
        params = []
        if attendance_date:
            query += " AND a.attendance_date=?"
            params.append(attendance_date)
        if member_id:
            query += " AND a.member_id=?"
            params.append(member_id)
        query += " ORDER BY a.attendance_date DESC, m.full_name"
        with self.connect() as conn:
            return conn.execute(query, params).fetchall()

    def delete_attendance(self, attendance_id):
        with self.connect() as conn:
            conn.execute(
                "DELETE FROM attendance WHERE id=?", (attendance_id,))
            conn.commit()
