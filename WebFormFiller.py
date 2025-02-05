from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

class WebFormFiller:
    def __init__(self, driver_path, url):
        self.driver_path = driver_path
        self.url = url
        self.driver = None

    def start_browser(self):
        # 启动浏览器
        self.driver = webdriver.Chrome(executable_path=self.driver_path)
        self.driver.get(self.url)
        time.sleep(2)  # 等待页面加载

    def fill_form(self, bill_info):
        # 填写表单
        try:
            # 定位表单元素并填写数据
            bill_number_input = self.driver.find_element(By.ID, "bill_number_input_id")
            bill_number_input.send_keys(bill_info["bill_number"])

            date_input = self.driver.find_element(By.ID, "date_input_id")
            date_input.send_keys(bill_info["date"])

            user_input = self.driver.find_element(By.ID, "user_input_id")
            user_input.send_keys(bill_info["user"])

            vehicle_input = self.driver.find_element(By.ID, "vehicle_input_id")
            vehicle_input.send_keys(bill_info["vehicle"])

            department_input = self.driver.find_element(By.ID, "department_input_id")
            department_input.send_keys(bill_info["department"])

            # 提交表单
            submit_button = self.driver.find_element(By.ID, "submit_button_id")
            submit_button.click()

            time.sleep(2)  # 等待表单提交

        except Exception as e:
            print(f"填写表单时出错: {e}")

    def close_browser(self):
        # 关闭浏览器
        if self.driver:
            self.driver.quit()

if __name__ == "__main__":
    # 示例数据
    bill_info = {
        "bill_number": "123456",
        "date": "2023-10-01",
        "user": "John Doe",
        "vehicle": "Toyota Camry",
        "department": "Sales"
    }

    # 驱动路径和网页URL
    driver_path = "path/to/chromedriver"
    url = "https://example.com/bill-form"

    # 创建WebFormFiller实例并填写表单
    form_filler = WebFormFiller(driver_path, url)
    form_filler.start_browser()
    form_filler.fill_form(bill_info)
    form_filler.close_browser()