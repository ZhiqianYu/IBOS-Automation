import sqlite3
import tkinter as tk
import pyperclip
from tkinter import messagebox
from tkinter import ttk
from datetime import datetime
import os
import subprocess

class BillViewer:
    def __init__(self, root, db_path):
        self.root = root
        self.db_path = db_path
        self.root.title("Bill Info")
        
        # Set a minimum window size
        self.root.minsize(600, 400)

        # 账单信息区域（上部）
        self.info_frame = tk.Frame(root)
        self.info_frame.pack(fill="x", padx=10, pady=5, expand=False)

        # 左侧：账单基本信息
        self.bill_info_text = tk.Frame(self.info_frame)
        self.bill_info_text.pack(side="left", padx=10, expand=False)

        # 设置较小的字体
        small_font = ("Arial", 12)

        # 账单信息（可以点击复制）
        self.bill_number_label = tk.Label(self.bill_info_text, text="Invoice Number: ", font=small_font, anchor="w", cursor="hand2")
        self.bill_number_label.pack(anchor="w")
        self.bill_number_label.bind("<ButtonRelease-1>", lambda event: self.copy_to_clipboard(event, "bill_number"))

        self.date_label = tk.Label(self.bill_info_text, text="Datum: ", font=small_font, anchor="w", cursor="hand2")
        self.date_label.pack(anchor="w")
        self.date_label.bind("<ButtonRelease-1>", lambda event: self.copy_to_clipboard(event, "date"))

        self.user_label = tk.Label(self.bill_info_text, text="Benutzername: ", font=small_font, anchor="w", cursor="hand2")
        self.user_label.pack(anchor="w")
        self.user_label.bind("<ButtonRelease-1>", lambda event: self.copy_to_clipboard(event, "user"))

        self.vehicle_label = tk.Label(self.bill_info_text, text="Vehicle Name: ", font=small_font, anchor="w", cursor="hand2")
        self.vehicle_label.pack(anchor="w")
        self.vehicle_label.bind("<ButtonRelease-1>", lambda event: self.copy_to_clipboard(event, "vehicle"))

        self.department_label = tk.Label(self.bill_info_text, text="Department: ", font=small_font, anchor="w", cursor="hand2")
        self.department_label.pack(anchor="w")
        self.department_label.bind("<ButtonRelease-1>", lambda event: self.copy_to_clipboard(event, "department"))

        # 状态栏（显示复制成功）移到左侧信息框下方
        self.status_label = tk.Label(self.bill_info_text, text="", font=small_font, fg="green")
        self.status_label.pack(anchor="w")

        # 右侧：金额信息
        self.total_info_text = tk.Frame(self.info_frame)
        self.total_info_text.pack(side="right", padx=10, expand=False)

        # 使用相同的小字体
        self.sum_tax_excluded_label = tk.Label(self.total_info_text, text="Bill Sum: ", font=small_font, anchor="e", cursor="hand2")
        self.sum_tax_excluded_label.pack(anchor="e")
        self.sum_tax_excluded_label.bind("<ButtonRelease-1>", lambda event: self.copy_to_clipboard(event, "sum_tax_excluded"))

        self.sum_tax_label = tk.Label(self.total_info_text, text="Bill Tax: ", font=small_font, anchor="e", cursor="hand2")
        self.sum_tax_label.pack(anchor="e")
        self.sum_tax_label.bind("<ButtonRelease-1>", lambda event: self.copy_to_clipboard(event, "sum_tax"))

        self.sum_tax_included_label = tk.Label(self.total_info_text, text="Sum with Tax: ", font=small_font, anchor="e", cursor="hand2")
        self.sum_tax_included_label.pack(anchor="e")
        self.sum_tax_included_label.bind("<ButtonRelease-1>", lambda event: self.copy_to_clipboard(event, "sum_tax_included"))

        self.empty_label = tk.Label(self.total_info_text, text="-----------------", font=("Arial", 4), anchor="e")
        self.empty_label.pack(anchor="e")

        self.leasing_cost_label = tk.Label(self.total_info_text, text="Leasing Cost: ", font=small_font, anchor="e", cursor="hand2")
        self.leasing_cost_label.pack(anchor="e")
        self.leasing_cost_label.bind("<ButtonRelease-1>", lambda event: self.copy_to_clipboard(event, "leasing_cost"))

        self.leasing_tax_label = tk.Label(self.total_info_text, text="Leasing Tax: ", font=small_font, anchor="e", cursor="hand2")
        self.leasing_tax_label.pack(anchor="e")
        self.leasing_tax_label.bind("<ButtonRelease-1>", lambda event: self.copy_to_clipboard(event, "leasing_tax"))

        # 账单明细表格（中部）
        self.tree = ttk.Treeview(root, columns=("Items", "Amount", "Tax", "Sum"), show="headings", height=8)
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Arial", 12))
        style.configure("Treeview", font=("Arial", 12))
        self.tree.column("Items", anchor="w", width=300)
        self.tree.column("Amount", anchor="e", width=60)
        self.tree.column("Tax", anchor="e", width=60)
        self.tree.column("Sum", anchor="e", width=60)

        for col in ("Items", "Amount", "Tax", "Sum"):
            self.tree.heading(col, text=col, anchor="center")

        self.tree.pack(fill="x", padx=10, pady=5)

        # 设置更大的字体
        style = ttk.Style()
        style.configure("Treeview", font=("Arial", 12))

        # 查询输入框 + 按钮（底部）
        self.input_frame = tk.Frame(root)
        self.input_frame.pack(fill="x", padx=10, pady=5)

        self.entry = tk.Entry(self.input_frame, font=("Arial", 12))
        self.entry.pack(side="left", padx=5, expand=True, fill="x")

        self.search_button = tk.Button(self.input_frame, text="查询", font=("Arial", 10), height=1, command=self.fetch_and_display)
        self.search_button.pack(side="right", padx=5)
        self.entry.bind("<Return>", lambda event: self.fetch_and_display())

        # 添加打开 PDF 按钮
        self.open_pdf_button = tk.Button(self.input_frame, text="打开", font=("Arial", 10), height=1, command=self.open_pdf)
        self.open_pdf_button.pack(side="right", padx=5)

        # 绑定点击复制事件
        self.tree.bind("<ButtonRelease-1>", self.copy_to_clipboard)

    def fetch_bill_data(self, bill_number):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 查询账单基本信息
            cursor.execute("""
                SELECT bills.bill_number, bills.date, employees.name, employees.vehicle_name, employees.department, bills.vehicle_name
                FROM bills
                LEFT JOIN employees ON bills.user_name = employees.name AND bills.vehicle_name = employees.vehicle_name
                WHERE bills.bill_number LIKE ?
            """, (f"%{bill_number}%",))
            bill_info = cursor.fetchone()

            if not bill_info:
                messagebox.showerror("查询失败", f"未找到账单号 {bill_number} 对应的记录")
                return None, None

            bill_number, date, user, vehicle, department, vehicle_model = bill_info

            # 查询账单明细
            cursor.execute("""
                SELECT item_name, amount, tax, total_amount
                FROM bill_items
                WHERE bill_id = (SELECT id FROM bills WHERE bill_number = ?)
            """, (bill_number,))
            items = cursor.fetchall()

            return (bill_number, date, user, vehicle, department, vehicle_model), items

    def fetch_and_display(self):
        bill_number = self.entry.get().strip()
        if not bill_number:
            messagebox.showwarning("Wrong Data", "Please enter a bill number")
            return

        bill_info, items = self.fetch_bill_data(bill_number)
        if bill_info is None:
            return

        bill_number, date, user, vehicle, department, vehicle_model = bill_info

        # 格式化日期为年-月-日
        if date:
            parsed_date = datetime.strptime(date, "%d.%m.%Y")
            formatted_date = parsed_date.strftime("%Y-%m-%d")
        else:
            formatted_date = "未知"

        # 计算金额
        total_tax_included = sum(item[1] + item[2] for item in items)  # 含税金额
        total_tax = sum(item[2] for item in items)  # 总税额
        total_tax_excluded = total_tax_included - total_tax  # 不含税金额

        # 计算 Finanzleasingrate + Servicerate
        leasing_rate = sum(item[1] for item in items if item[0] == "Finanzleasingrate")
        service_rate = sum(item[1] for item in items if item[0] == "Servicerate")
        leasing_service_total = leasing_rate + service_rate
        leasing_tax = sum(item[2] for item in items if item[0] in ["Finanzleasingrate", "Servicerate"])

        # 更新账单信息文本
        self.bill_number_label.config(text=f"Invoice Number: {bill_number}")
        self.date_label.config(text=f"Datum: {formatted_date}")
        self.user_label.config(text=f"Benutzername: {user if user else '未知'}")
        self.vehicle_label.config(text=f"Vehicle Name: {vehicle if vehicle else vehicle_model if vehicle_model else '未知'}")
        self.department_label.config(text=f"Department: {department if department else '未知'}")

        # 更新金额信息文本
        self.sum_tax_excluded_label.config(text=f"Sum ohne Tax: {total_tax_excluded:.2f}")
        self.sum_tax_label.config(text=f"Sum Tax: {total_tax:.2f}")
        self.sum_tax_included_label.config(text=f"Sum mit Tax: {total_tax_included:.2f}")
        self.leasing_cost_label.config(text=f"Leasing Cost: {leasing_service_total:.2f}")
        self.leasing_tax_label.config(text=f"Leasing Tax: {leasing_tax:.2f}")

        # 清空旧数据
        self.tree.delete(*self.tree.get_children())

        # 添加新数据
        for item in items:
            item_name, amount, tax, total_amount = item
            tax_included = total_amount
            self.tree.insert("", "end", values=(item_name, f"{amount:.2f}", f"{tax:.2f}", f"{tax_included:.2f}"))

    def copy_to_clipboard(self, event, data_type=None):
        if data_type:
            # 复制账单信息或金额信息
            widget = event.widget
            text_to_copy = widget.cget("text").split(": ")[1]
            if text_to_copy.strip():  # 只有文本不为空时才复制
                pyperclip.copy(text_to_copy)  # 复制到剪贴板
                self.status_label.config(text=f"已复制: {text_to_copy}")  # 显示复制成功
                self.root.after(3000, lambda: self.status_label.config(text=""))  # 3秒后清除提示
        else:
            # 复制表格中的数字部分
            selected_item = self.tree.selection()
            if selected_item:
                item_values = self.tree.item(selected_item, "values")
                if item_values:
                    # 获取点击的列索引
                    col_id = self.tree.identify_column(event.x)  # 识别点击的列
                    col_index = int(col_id[1:]) - 1  # 转换为0-based索引

                    if 0 <= col_index < len(item_values):
                        text_to_copy = item_values[col_index]  # 获取选中的文本
                        pyperclip.copy(text_to_copy)  # 复制到剪贴板
                        self.status_label.config(text=f"已复制: {text_to_copy}")  # 显示复制成功
                        self.root.after(3000, lambda: self.status_label.config(text=""))  # 3秒后清除提示

    def open_pdf(self):
        bill_number = self.entry.get().strip()
        if not bill_number:
            messagebox.showwarning("错误", "请输入账单号")
            return

        # 在 Bills 文件夹中查找包含账单号的 PDF 文件
        bills_folder = "Bills"
        pdf_files = [f for f in os.listdir(bills_folder) if f.endswith(".pdf") and bill_number in f]

        if not pdf_files:
            messagebox.showwarning("未找到文件", f"未找到包含账单号 {bill_number} 的 PDF 文件")
            return

        # 打开第一个匹配的 PDF 文件
        pdf_path = os.path.join(bills_folder, pdf_files[0])
        try:
            if os.name == "nt":  # Windows
                os.startfile(pdf_path)
            elif os.name == "posix":  # macOS 或 Linux
                subprocess.run(["open", pdf_path] if os.uname().sysname == "Darwin" else ["xdg-open", pdf_path])
        except Exception as e:
            messagebox.showerror("打开文件失败", f"无法打开 PDF 文件: {e}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="查询账单信息")
    parser.add_argument("--db", default="bills.db", help="数据库路径 (默认: bills.db)")
    args = parser.parse_args()

    root = tk.Tk()
    app = BillViewer(root, args.db)
    root.mainloop()