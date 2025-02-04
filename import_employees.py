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

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                for _, row in df.iterrows():
                    name = str(row["Namen"]).strip().title()  # 去除前后空格并转换为统一大小写格式
                    department = str(row["Cost Center"]).strip()
                    vehicle_name = row["Vehicle Name"]

                    if vehicle_name:
                        # **情况 1：如果 Excel 中有车辆信息**
                        cursor.execute("SELECT id, name, department FROM employees WHERE vehicle_name = ?", (vehicle_name,))
                        results = cursor.fetchall()
                        if len(results) == 1:
                            db_name, db_department = results[0][1], results[0][2]
                            if db_department == 'Unknown':
                                cursor.execute(
                                    "UPDATE employees SET department = ? WHERE vehicle_name = ? AND department = 'Unknown'",
                                    (department, vehicle_name)
                                )
                                logger.info(f"车辆匹配更新: {vehicle_name} -> {department}")
                            else:
                                logger.info(f"跳过已有部门信息的车辆: {vehicle_name}")
                        elif len(results) > 1:
                            logger.warning(f"车辆信息重复: {vehicle_name}，不更新数据")
                        else:
                            # 如果车辆信息未找到匹配项，则根据姓名查找
                            cursor.execute("SELECT id, department FROM employees WHERE name = ?", (name,))
                            results = cursor.fetchall()
                            if len(results) == 1:
                                db_department = results[0][1]
                                if db_department == 'Unknown':
                                    cursor.execute(
                                        "UPDATE employees SET department = ? WHERE name = ? AND department = 'Unknown'",
                                        (department, name)
                                    )
                                    logger.info(f"姓名匹配更新: {name} -> {department}")
                                else:
                                    logger.info(f"跳过已有部门信息的姓名: {name}")
                            elif len(results) > 1:
                                logger.warning(f"姓名信息重复: {name}，不更新数据")
                            else:
                                logger.warning(f"未找到匹配的车辆信息和姓名: {vehicle_name}, {name}，不更新数据")
                    else:
                        # **情况 2：如果 Excel 中没有车辆信息**
                        cursor.execute("SELECT id, department FROM employees WHERE name = ?", (name,))
                        results = cursor.fetchall()
                        if len(results) == 1:
                            db_department = results[0][1]
                            if db_department == 'Unknown':
                                cursor.execute(
                                    "UPDATE employees SET department = ? WHERE name = ? AND department = 'Unknown'",
                                    (department, name)
                                )
                                logger.info(f"姓名匹配更新: {name} -> {department}")
                            else:
                                logger.info(f"跳过已有部门信息的姓名: {name}")
                                if vehicle_name:
                                    cursor.execute("SELECT id, department FROM employees WHERE vehicle_name = ?", (vehicle_name,))
                                    results = cursor.fetchall()
                                    if len(results) == 1:
                                        db_department = results[0][1]
                                        if db_department == 'Unknown':
                                            cursor.execute(
                                                "UPDATE employees SET department = ? WHERE vehicle_name = ? AND department = 'Unknown'",
                                                (department, vehicle_name)
                                            )
                                            logger.info(f"车辆匹配更新: {vehicle_name} -> {department}")
                                        else:
                                            logger.info(f"跳过已有部门信息的车辆: {vehicle_name}")
                                    elif len(results) > 1:
                                        logger.warning(f"车辆信息重复: {vehicle_name}，不更新数据")
                                    else:
                                        logger.warning(f"未找到匹配的车辆信息: {vehicle_name}，不更新数据")
                        elif len(results) > 1:
                            # 如果姓名查找是重复的，但是部门又不一样，则使用车辆信息查找数据库
                            if vehicle_name:
                                cursor.execute("SELECT id, department FROM employees WHERE vehicle_name = ?", (vehicle_name,))
                                results = cursor.fetchall()
                                if len(results) == 1:
                                    db_department = results[0][1]
                                    if db_department == 'Unknown':
                                        cursor.execute(
                                            "UPDATE employees SET department = ? WHERE vehicle_name = ? AND department = 'Unknown'",
                                            (department, vehicle_name)
                                        )
                                        logger.info(f"车辆匹配更新: {vehicle_name} -> {department}")
                                    else:
                                        logger.info(f"姓名重复，使用车辆信息查询，已存在部门信息: {vehicle_name}")
                                elif len(results) > 1:
                                    logger.warning(f"车辆信息重复: {vehicle_name}，不更新数据")
                                else:
                                    logger.warning(f"未找到匹配的车辆信息: {vehicle_name}，不更新数据")
                            else:
                                logger.warning(f"姓名信息重复: {name}，缺少车辆信息无法匹配")
                        else:
                            logger.warning(f"未找到匹配的姓名: {name}，缺少车辆信息无法匹配")

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
