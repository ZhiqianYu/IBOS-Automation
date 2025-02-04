import pandas as pd
import sqlite3
import argparse
import logging
import re
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmployeeImporter:
    def __init__(self, db_path="bills.db"):
        self.db_path = db_path

    def clean_department(self, department: str) -> str:
        """去掉部门信息中的数字"""
        return re.sub(r'\d+', '', department).strip()

    def import_from_excel(self, excel_path: str):
        """从 Excel 读取 name 和 cost center，并存入 employees 表"""
        excel_path = Path(excel_path)
        if not excel_path.exists():
            logger.error(f"Excel 文件不存在: {excel_path}")
            return

        try:
            # 读取 Excel 数据
            df = pd.read_excel(excel_path)

            # 打印所有列名，帮助调试
            logger.info(f"Excel 文件列名: {df.columns.tolist()}")

            # 读取 Excel 数据
            df = pd.read_excel(excel_path, usecols=["Namen", "Cost Center", "Vehicle Name"])
            df.dropna(subset=["Namen"], inplace=True)  # 移除空的姓名行
            df["Cost Center"] = df["Cost Center"].apply(self.clean_department)
            df["Vehicle Name"] = df["Vehicle Name"].fillna("")  # 填充车辆名称为空的行

            employees = df.to_records(index=False)

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                for _, row in df.iterrows():
                    name = row["Namen"]
                    department = row["Cost Center"]
                    vehicle_name = row["Vehicle Name"]

                    # 查询数据库中是否有多个相同 name 的记录
                    cursor.execute("SELECT COUNT(*) FROM employees WHERE name = ?", (name,))
                    name_count = cursor.fetchone()[0]

                    if name_count == 1:  
                        # **情况 1：如果 name 在数据库中是唯一的，直接更新**
                        cursor.execute(
                            "UPDATE employees SET department = ? WHERE name = ? AND department = 'Unknown'",
                            (department, name)
                        )
                        logger.info(f"唯一姓名更新: {name} -> {department}")

                    elif name_count > 1 and vehicle_name:  
                        # **情况 2：如果 name 不唯一，且 Excel 里有 Vehicle Name，则使用 vehicle_name 进行匹配**
                        cursor.execute(
                            "UPDATE employees SET department = ? WHERE name = ? AND vehicle_name = ? AND department = 'Unknown'",
                            (department, name, vehicle_name)
                        )
                        logger.info(f"匹配车辆更新: {name} ({vehicle_name}) -> {department}")

                conn.commit()
                logger.info(f"员工数据更新完成")

        except Exception as e:
            logger.error(f"导入失败: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="从 Excel 导入员工信息到数据库")
    parser.add_argument("excel_path", help="Excel 文件路径")
    args = parser.parse_args()

    importer = EmployeeImporter()
    importer.import_from_excel(args.excel_path)

if __name__ == "__main__":
    main()
