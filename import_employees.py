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
        return re.sub(r'\d+', '', str(department)).strip()

    def import_from_excel(self, excel_path: str):
        """从 Excel 读取 name 和 cost center，并存入 employees 表"""
        excel_path = Path(excel_path)
        if not excel_path.exists():
            logger.error(f"Excel 文件不存在: {excel_path}")
            return

        try:
            df = pd.read_excel(excel_path)

            # 打印所有列名，帮助调试
            logger.info(f"Excel 文件列名: {df.columns.tolist()}")

            # 读取所需列
            df = df[["Namen", "Cost Center", "Vehicle Name"]].copy()
            df.dropna(subset=["Namen"], inplace=True)  # 移除空的姓名行
            df["Cost Center"] = df["Cost Center"].apply(self.clean_department)
            df["Vehicle Name"] = df["Vehicle Name"].fillna("")  # 填充空的车辆名称

            # 统计 Excel 里每个 name 出现的次数
            name_counts = df["Namen"].value_counts().to_dict()

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # **获取数据库中的所有员工和车辆信息**
                cursor.execute("""
                    SELECT name, vehicle_name FROM employees
                """)
                db_employee_vehicles = cursor.fetchall()  
                
                # 构建字典：name -> 可能的 vehicle_name
                db_employee_dict = {}  
                for name, vehicle in db_employee_vehicles:
                    if name not in db_employee_dict:
                        db_employee_dict[name] = set()
                    db_employee_dict[name].add(vehicle)

                update_count = 0
                for _, row in df.iterrows():
                    name = row["Namen"]
                    department = row["Cost Center"]
                    vehicle_name = row["Vehicle Name"]

                    # **Excel 里 name 只出现一次（唯一）**
                    if name_counts[name] == 1:
                        cursor.execute("""
                            UPDATE employees 
                            SET department = ? 
                            WHERE name = ? 
                            AND department = 'Unknown'
                        """, (department, name))
                        update_count += cursor.rowcount
                        logger.info(f"唯一姓名更新: {name} -> {department}")

                    else:
                        # **Excel 里 name 不是唯一的，需要使用 vehicle_name 匹配**
                        possible_vehicles = db_employee_dict.get(name, set())
                        updated = False

                        # **情况 1：完整匹配**
                        if vehicle_name in possible_vehicles:
                            cursor.execute("""
                                UPDATE employees 
                                SET department = ? 
                                WHERE name = ? 
                                AND vehicle_name = ? 
                                AND department = 'Unknown'
                            """, (department, name, vehicle_name))
                            update_count += cursor.rowcount
                            updated = True

                        else:
                            # **情况 2：数据库 vehicle_name 是 Excel name 的一部分**
                            for db_vehicle in possible_vehicles:
                                if isinstance(db_vehicle, str) and db_vehicle in str(name):
                                    cursor.execute("""
                                        UPDATE employees 
                                        SET department = ? 
                                        WHERE name = ? 
                                        AND vehicle_name = ? 
                                        AND department = 'Unknown'
                                    """, (department, name, db_vehicle))
                                    update_count += cursor.rowcount
                                    updated = True
                                    break  # 只更新一次

                            # **情况 3：Excel vehicle_name 是数据库 name 的一部分**
                            if not updated:
                                for db_vehicle in possible_vehicles:
                                    if isinstance(db_vehicle, str) and vehicle_name and str(vehicle_name) in db_vehicle:
                                        cursor.execute("""
                                            UPDATE employees 
                                            SET department = ? 
                                            WHERE name = ? 
                                            AND vehicle_name = ? 
                                            AND department = 'Unknown'
                                        """, (department, name, db_vehicle))
                                        update_count += cursor.rowcount
                                        updated = True
                                        break  # 只更新一次

                        if updated:
                            logger.info(f"匹配车辆更新: {name} ({vehicle_name}) -> {department}")

                conn.commit()
                logger.info(f"更新完成，共更新了 {update_count} 条记录")

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
