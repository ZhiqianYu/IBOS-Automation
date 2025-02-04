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
                    name TEXT UNIQUE NOT NULL,
                    department TEXT NOT NULL,
                    vehicle_name TEXT NOT NULL,
                    UNIQUE(name, vehicle_name)
                );

                CREATE TABLE IF NOT EXISTS bills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bill_number TEXT UNIQUE NOT NULL,
                    date TEXT NOT NULL,
                    employee_id INTEGER,
                    vehicle_model TEXT NOT NULL,
                    FOREIGN KEY (employee_id) REFERENCES employees(id)
                );

                CREATE TABLE IF NOT EXISTS bill_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bill_id INTEGER,
                    item_name TEXT NOT NULL,
                    amount REAL NOT NULL,
                    tax REAL NOT NULL,
                    tax_rate TEXT NOT NULL,
                    FOREIGN KEY (bill_id) REFERENCES bills(id)
                );
            """)
            conn.commit()
            logger.info("数据库表已初始化")

    def add_employee(self, name: str, department: str, vehicle_name:str) -> int:
        """添加员工信息"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO employees (name, department, vehicle_name) VALUES (?, ?, ?)",
                (name, department, vehicle_name)
            )
            conn.commit()
            return cursor.lastrowid or self.get_employee_id(name)

    def get_employee_id(self, name: str) -> Optional[int]:
        """获取员工ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM employees WHERE name = ?", (name,))
            result = cursor.fetchone()
            return result[0] if result else None

    def add_bill(self, bill_data: Dict, pdf_filename: str) -> int:
        """添加账单信息，并在日志中显示文件名"""
        employee_id = self.add_employee(bill_data["driver_name"], "Unknown", bill_data["vehicle_model"])
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO bills (bill_number, date, employee_id, vehicle_model) VALUES (?, ?, ?, ?)",
                (bill_data["bill_number"], bill_data["date"], employee_id, bill_data["vehicle_model"])
            )
            conn.commit()
            bill_id = cursor.lastrowid or self.get_bill_id(bill_data["bill_number"])
            logger.info(f"账单 {bill_data['bill_number']} ({pdf_filename}) 已存入数据库")
            return bill_id

    def get_bill_id(self, bill_number: str) -> Optional[int]:
        """获取账单ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM bills WHERE bill_number = ?", (bill_number,))
            result = cursor.fetchone()
            return result[0] if result else None

    def add_bill_items(self, bill_id: int, items: List[Dict], pdf_filename: str):
        """添加账单详细信息，并在日志中显示文件名"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for item in items:
                cursor.execute(
                    "INSERT INTO bill_items (bill_id, item_name, amount, tax, tax_rate) VALUES (?, ?, ?, ?, ?)",
                    (bill_id, item["item_name"], item["amount"], item["tax"], item["tax_rate"])
                )
            conn.commit()
            logger.info(f"账单 {pdf_filename} 的详细信息已添加")

    def get_all_bills(self):
        """获取所有账单"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT b.id, b.bill_number, b.date, e.name, b.vehicle_model
                FROM bills b
                LEFT JOIN employees e ON b.employee_id = e.id
            """)
            return cursor.fetchall()
