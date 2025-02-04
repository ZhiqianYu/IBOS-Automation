import sqlite3
import logging
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DBManager:
    def __init__(self, db_path="bills.db"):
        self.db_path = db_path
        self._create_tables()

    def _create_tables(self):
        """创建数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.executescript("""
                CREATE TABLE IF NOT EXISTS employees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    department TEXT NOT NULL,
                    vehicle_name TEXT NOT NULL,
                    UNIQUE(name, vehicle_name)
                );

                CREATE TABLE IF NOT EXISTS bills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bill_number TEXT UNIQUE NOT NULL,
                    date TEXT NOT NULL,
                    user_name TEXT NOT NULL,
                    vehicle_name TEXT NOT NULL,
                    FOREIGN KEY (user_name, vehicle_name) REFERENCES employees(name, vehicle_name)
                );

                CREATE TABLE IF NOT EXISTS bill_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bill_id INTEGER,
                    item_name TEXT NOT NULL,
                    amount REAL NOT NULL,
                    tax REAL NOT NULL,
                    tax_rate TEXT NOT NULL,
                    total_amount REAL NOT NULL,
                    FOREIGN KEY (bill_id) REFERENCES bills(id)
                );
            """)
            conn.commit()
            logger.debug("数据库表已初始化")

    def add_employee(self, name: str, department: str, vehicle_name: str) -> int:
        """添加员工信息"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM employees WHERE name = ? AND vehicle_name = ?",
                (name, vehicle_name)
            )
            result = cursor.fetchone()
            if result:
                logger.info(f"员工信息已存在: {name}, {vehicle_name}")
                return result[0]
            else:
                cursor.execute(
                    "INSERT INTO employees (name, department, vehicle_name) VALUES (?, ?, ?)",
                    (name, department, vehicle_name)
                )
                conn.commit()
                logger.debug(f"员工信息已添加: {name}, {vehicle_name}")
                return cursor.lastrowid

    def get_employee_id(self, name: str, vehicle_name: str) -> Optional[int]:
        """获取员工ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM employees WHERE name = ? AND vehicle_name = ?", (name, vehicle_name))
            result = cursor.fetchone()
            return result[0] if result else None

    def add_bill(self, bill_data: Dict, pdf_filename: str) -> int:
        """添加账单信息，并在日志中显示文件名"""
        employee_id = self.add_employee(bill_data["user_name"], "Unknown", bill_data["vehicle_name"])
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM bills WHERE bill_number = ?",
                (bill_data["bill_number"],)
            )
            result = cursor.fetchone()
            if result:
                logger.info(f"账单信息已存在: {bill_data['bill_number']}")
                return result[0]
            else:
                cursor.execute(
                    "INSERT INTO bills (bill_number, date, user_name, vehicle_name) VALUES (?, ?, ?, ?)",
                    (bill_data["bill_number"], bill_data["date"], bill_data["user_name"], bill_data["vehicle_name"])
                )
                conn.commit()
                bill_id = cursor.lastrowid
                logger.info(f"账单 {bill_data['bill_number']} ({pdf_filename}) 已存入数据库")
                return bill_id

    def get_bill_id(self, bill_number: str) -> Optional[int]:
        """获取账单ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM bills WHERE bill_number = ?", (bill_number,))
            result = cursor.fetchone()
            return result[0] if result else None

    def add_bill_item(self, bill_id: int, item: Dict):
        """添加账单详细信息"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 1 FROM bill_items
                WHERE bill_id = ? AND item_name = ? AND amount = ? AND tax = ? AND tax_rate = ? AND total_amount = ?
                """,
                (bill_id, item['item_name'], item['amount'], item['tax'], item['tax_rate'], item['total_amount'])
            )
            if cursor.fetchone() is None:
                cursor.execute(
                    """
                    INSERT INTO bill_items (bill_id, item_name, amount, tax, tax_rate, total_amount)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (bill_id, item['item_name'], item['amount'], item['tax'], item['tax_rate'], item['total_amount'])
                )
                conn.commit()
                logger.debug(f"账单详细信息已添加: {item}")
            else:
                logger.info(f"详细信息已存在: {item}")

    def get_all_bills(self):
        """获取所有账单"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT b.id, b.bill_number, b.date, b.user_name, b.vehicle_name
                FROM bills b
            """)
            return cursor.fetchall()