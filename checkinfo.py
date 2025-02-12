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
        self.root.minsize(600, 400)

        # Add a frame for invoice list
        self.invoice_list_frame = tk.Frame(root)
        self.invoice_list_frame.pack(fill="x", padx=10, pady=5, expand=True)
        self.invoice_list_frame.pack_forget()  # Hide by default

        # Add label for invoice list
        self.invoice_list_label = tk.Label(self.invoice_list_frame, text="Related Bills:", font=("Arial", 12))
        self.invoice_list_label.pack(anchor="w")

        # Add listbox for invoices with scrollbar
        self.listbox_frame = tk.Frame(self.invoice_list_frame)
        self.listbox_frame.pack(fill="both", expand=True)
        
        self.invoice_listbox = tk.Listbox(self.listbox_frame, font=("Arial", 12), height=4)
        self.scrollbar = tk.Scrollbar(self.listbox_frame, orient="vertical", command=self.invoice_listbox.yview)
        self.invoice_listbox.configure(yscrollcommand=self.scrollbar.set)
        
        self.invoice_listbox.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.invoice_listbox.bind('<<ListboxSelect>>', self.on_select_invoice)

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

        # Modified input frame to include a radio button for search type
        self.input_frame = tk.Frame(root)
        self.input_frame.pack(fill="x", padx=10, pady=5)

        # Add radio buttons for search type
        self.search_type = tk.StringVar(value="bill")
        self.bill_radio = tk.Radiobutton(self.input_frame, text="账单号", variable=self.search_type, 
                                       value="bill", font=("Arial", 10), 
                                       command=self.on_search_type_change)
        self.bill_radio.pack(side="left", padx=5)
        self.employee_radio = tk.Radiobutton(self.input_frame, text="用户名", variable=self.search_type, 
                                           value="employee", font=("Arial", 10),
                                           command=self.on_search_type_change)
        self.employee_radio.pack(side="left", padx=5)

        self.entry = tk.Entry(self.input_frame, font=("Arial", 12))
        self.entry.pack(side="left", padx=5, expand=True, fill="x")

        self.search_button = tk.Button(self.input_frame, text="查询", font=("Arial", 10), height=1, command=self.fetch_and_display)
        self.search_button.pack(side="right", padx=5)
        self.entry.bind("<Return>", lambda event: self.fetch_and_display())

        self.open_pdf_button = tk.Button(self.input_frame, text="打开", font=("Arial", 10), height=1, command=self.open_pdf)
        self.open_pdf_button.pack(side="right", padx=5)

        # 绑定点击复制事件
        self.tree.bind("<ButtonRelease-1>", self.copy_to_clipboard)

    def on_search_type_change(self):
        """Handle search type change"""
        if self.search_type.get() == "bill":
            self.invoice_list_frame.pack_forget()  # 切换到账单号搜索时隐藏 Related Bills 框架
            self.clear_display()
            self.entry.delete(0, tk.END)
        else:
            # 切换到用户名搜索时，保持 Related Bills 框架显示
            pass

    def toggle_invoice_list(self):
        """Toggle visibility of invoice list based on search type"""
        if self.search_type.get() == "employee":
            self.invoice_list_frame.pack(fill="x", padx=10, pady=5, after=self.input_frame)
        else:
            self.invoice_list_frame.pack_forget()

    def fetch_user_bills(self, username):
        """Fetch all bills for a given username"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT bills.bill_number
                FROM bills
                WHERE bills.user_name LIKE ?
                ORDER BY bills.date DESC
            """, (f"%{username}%",))
            return [row[0] for row in cursor.fetchall()]
        
    def on_select_invoice(self, event):
        """Handle invoice selection from listbox"""
        if not self.invoice_listbox.curselection():
            return
        selected_invoice = self.invoice_listbox.get(self.invoice_listbox.curselection())
        self.entry.delete(0, tk.END)
        self.entry.insert(0, selected_invoice)
        self.search_type.set("bill")  # 切换到账单号查询模式
        self.fetch_and_display()  # 直接查询详细信息

    def fetch_bill_data(self, search_term):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            if self.search_type.get() == "bill":
                # Original bill number search
                cursor.execute("""
                    SELECT bills.bill_number, bills.date, employees.name, employees.vehicle_name, employees.department, bills.vehicle_name
                    FROM bills
                    LEFT JOIN employees ON bills.user_name = employees.name AND bills.vehicle_name = employees.vehicle_name
                    WHERE bills.bill_number LIKE ?
                """, (f"%{search_term}%",))
            else:
                # New employee name search
                cursor.execute("""
                    SELECT bills.bill_number, bills.date, employees.name, employees.vehicle_name, employees.department, bills.vehicle_name
                    FROM employees
                    LEFT JOIN bills ON employees.name = bills.user_name
                    WHERE employees.name LIKE ?
                    LIMIT 1
                """, (f"%{search_term}%",))

            bill_info = cursor.fetchone()

            if not bill_info:
                if self.search_type.get() == "bill":
                    messagebox.showerror("查询失败", f"未找到账单号 {search_term} 对应的记录")
                else:
                    messagebox.showerror("查询失败", f"未找到用户名 {search_term} 对应的记录")
                return None, None

            bill_number, date, user, vehicle, department, vehicle_model = bill_info

            # Only fetch bill items if we have a valid bill number
            if bill_number:
                cursor.execute("""
                    SELECT item_name, amount, tax, total_amount
                    FROM bill_items
                    WHERE bill_id = (SELECT id FROM bills WHERE bill_number = ?)
                """, (bill_number,))
                items = cursor.fetchall()
            else:
                items = []

            return (bill_number, date, user, vehicle, department, vehicle_model), items

    def fetch_and_display(self):
        search_term = self.entry.get().strip()
        if not search_term:
            messagebox.showwarning("Wrong Data", "请输入查询内容")
            return

        if self.search_type.get() == "employee":
            # 使用用户名搜索
            bills = self.fetch_user_bills(search_term)
            if not bills:
                messagebox.showwarning("未找到记录", f"未找到用户名 {search_term} 的账单记录")
                return
            
            # 清空并更新账单列表
            self.invoice_listbox.delete(0, tk.END)
            for bill in bills:
                self.invoice_listbox.insert(tk.END, bill)
            
            if len(bills) > 1:
                # 如果有多个账单，显示 Related Bills 框架
                self.invoice_list_frame.pack(fill="x", padx=10, pady=5, expand=True)
                # 清空当前显示，直到用户选择具体的账单
                self.clear_display()
            else:
                # 如果只有一个账单，隐藏列表并直接显示详细信息
                self.invoice_list_frame.pack_forget()
                bill_info, items = self.fetch_bill_data(bills[0])
                if bill_info is not None:
                    self.update_display(bill_info, items)
            return
        
        # 使用账单号搜索
        self.invoice_list_frame.pack_forget()  # 隐藏 Related Bills 框架
        bill_info, items = self.fetch_bill_data(search_term)
        if bill_info is not None:
            self.update_display(bill_info, items)
    
    def clear_display(self):
        """Clear all display fields"""
        self.bill_number_label.config(text="Invoice Number: ")
        self.date_label.config(text="Datum: ")
        self.user_label.config(text="Benutzername: ")
        self.vehicle_label.config(text="Vehicle Name: ")
        self.department_label.config(text="Department: ")
        self.sum_tax_excluded_label.config(text="Sum ohne Tax: 0.00")
        self.sum_tax_label.config(text="Sum Tax: 0.00")
        self.sum_tax_included_label.config(text="Sum mit Tax: 0.00")
        self.leasing_cost_label.config(text="Leasing Cost: 0.00")
        self.leasing_tax_label.config(text="Leasing Tax: 0.00")
        self.tree.delete(*self.tree.get_children())

    def on_select_invoice(self, event):
        """Handle invoice selection from listbox"""
        if not self.invoice_listbox.curselection():
            return
        
        # 获取选中的账单号
        selected_invoice = self.invoice_listbox.get(self.invoice_listbox.curselection())
        
        # 清空输入框并填入选中的账单号
        self.entry.delete(0, tk.END)
        self.entry.insert(0, selected_invoice)
        
        # 切换到账单号搜索模式
        self.search_type.set("bill")  # 设置为账单号搜索模式
        
        # 直接调用查询方法
        self.fetch_and_display()

    def update_display(self, bill_info, items):
        """Update the display with bill information"""
        bill_number, date, user, vehicle, department, vehicle_model = bill_info

        # Format date if available
        formatted_date = "未知"
        if date:
            try:
                parsed_date = datetime.strptime(date, "%d.%m.%Y")
                formatted_date = parsed_date.strftime("%Y-%m-%d")
            except:
                pass

        # Update labels
        self.bill_number_label.config(text=f"Invoice Number: {bill_number if bill_number else '未知'}")
        self.date_label.config(text=f"Datum: {formatted_date}")
        self.user_label.config(text=f"Benutzername: {user if user else '未知'}")
        self.vehicle_label.config(text=f"Vehicle Name: {vehicle if vehicle else vehicle_model if vehicle_model else '未知'}")
        self.department_label.config(text=f"Department: {department if department else '未知'}")

        # Clear and update the tree
        self.tree.delete(*self.tree.get_children())

        if items:
            # Calculate and display financial information
            total_tax_included = sum(item[1] + item[2] for item in items)
            total_tax = sum(item[2] for item in items)
            total_tax_excluded = total_tax_included - total_tax

            leasing_rate = sum(item[1] for item in items if item[0] == "Finanzleasingrate")
            service_rate = sum(item[1] for item in items if item[0] == "Servicerate")
            leasing_service_total = leasing_rate + service_rate
            leasing_tax = sum(item[2] for item in items if item[0] in ["Finanzleasingrate", "Servicerate"])

            # Update financial labels
            self.sum_tax_excluded_label.config(text=f"Sum ohne Tax: {total_tax_excluded:.2f}")
            self.sum_tax_label.config(text=f"Sum Tax: {total_tax:.2f}")
            self.sum_tax_included_label.config(text=f"Sum mit Tax: {total_tax_included:.2f}")
            self.leasing_cost_label.config(text=f"Leasing Cost: {leasing_service_total:.2f}")
            self.leasing_tax_label.config(text=f"Leasing Tax: {leasing_tax:.2f}")

            # Display items in tree
            for item in items:
                item_name, amount, tax, total_amount = item
                self.tree.insert("", "end", values=(item_name, f"{amount:.2f}", f"{tax:.2f}", f"{total_amount:.2f}"))
        else:
            # Clear financial information if no items
            self.sum_tax_excluded_label.config(text="Sum ohne Tax: 0.00")
            self.sum_tax_label.config(text="Sum Tax: 0.00")
            self.sum_tax_included_label.config(text="Sum mit Tax: 0.00")
            self.leasing_cost_label.config(text="Leasing Cost: 0.00")
            self.leasing_tax_label.config(text="Leasing Tax: 0.00")

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