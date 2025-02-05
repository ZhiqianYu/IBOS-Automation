import sqlite3
import os
import shutil
from datetime import datetime

def get_employees_with_high_bills(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    query = """
    SELECT employees.name, employees.department, employees.vehicle_name, bills.bill_number
    FROM employees
    JOIN bills ON employees.name = bills.user_name
    JOIN bill_items ON bills.id = bill_items.bill_id
    GROUP BY employees.name, employees.department, employees.vehicle_name, bills.bill_number
    HAVING SUM(bill_items.total_amount) > 1000
    ORDER BY employees.name;
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    conn.close()
    
    return results

def copy_files_for_employees(employees, source_dir, target_base_dir):
    today_str = datetime.today().strftime('%Y-%m-%d')
    target_dir = os.path.join(target_base_dir, today_str)
    os.makedirs(target_dir, exist_ok=True)

    for name, department, vehicle_name, bill_number in employees:
        # 假设文件名包含员工姓名
        for file_name in os.listdir(source_dir):
            if name in file_name:
                source_file = os.path.join(source_dir, file_name)
                target_file = os.path.join(target_dir, file_name)
                shutil.copy2(source_file, target_file)
                print(f"复制文件 {source_file} 到 {target_file}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="查询所有账单总金额大于1000的员工信息并复制相关文件")
    parser.add_argument("--db", default="bills.db", help="数据库路径 (默认: bills.db)")
    parser.add_argument("--source-dir", default=r"C:\Users\zhiqianyu\OneDrive - MIDEA INTERNATIONAL CORPORATION COMPANY LIMITED\Rechnungen\00 Vertrags der Mitarbeitern Autos", help="源文件夹路径")
    parser.add_argument("--target-dir", default=r"C:\Users\zhiqianyu\OneDrive - MIDEA INTERNATIONAL CORPORATION COMPANY LIMITED\Rechnungen", help="目标文件夹路径")
    args = parser.parse_args()

    employees = get_employees_with_high_bills(args.db)
    
    # 打印排序后的员工姓名
    print("账单总金额大于1000的员工信息（按字母排序）：")
    for row in employees:
        name, department, vehicle_name, bill_number = row
        print(f"姓名: {name}, 部门: {department}, 车辆: {vehicle_name}, 账单号: {bill_number}")
    
    copy_files_for_employees(employees, args.source_dir, args.target_dir)