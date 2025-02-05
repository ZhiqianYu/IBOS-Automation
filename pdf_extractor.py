import pdfplumber
import logging
from typing import Dict, Optional
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFExtractor:
    def extract_bill_data(self, pdf_path: str) -> Optional[Dict]:
        """
        从PDF账单中提取关键信息
        """
        try:
            pdf_path = Path(pdf_path)
            if not pdf_path.exists():
                logger.error(f"PDF文件不存在: {pdf_path}")
                return None

            with pdfplumber.open(pdf_path) as pdf:
                text = '\n'.join(page.extract_text() for page in pdf.pages[:2])
                logger.debug(f"提取的文本内容: {text[:500]}")  # 记录前500个字符的文本内容
                extracted_data = self._parse_bill_text(text)
                if not extracted_data:
                    logger.error("解析账单文本失败")
                    return None

                bill_data = {
                    'bill_number': extracted_data['bill_number'],
                    'date': extracted_data['date'],
                    'user_name': extracted_data['driver_name'],
                    'vehicle_name': extracted_data['vehicle_name'],
                    'items': extracted_data['items']
                }
                logger.debug(f"提取的账单数据: {bill_data}")
                return bill_data

        except Exception as e:
            logger.error(f"处理PDF时出错: {str(e)}")
            return None

    def _parse_bill_text(self, text: str) -> Dict:
        """
        解析账单文本内容
        """
        bill_data_head = {
            'bill_number': None,
            'date': None,
            'driver_name': None,
            'vehicle_name': None
        }

        bill_data_items = {
            'items': [],
            'errors': []
        }
        
        try:
            pages = text.split('\n')
            for i, line in enumerate(pages):
                if 'Rechnung:' in line or 'Gutschrift:' in line:
                    if 'Rechnung:' in line:
                        bill_data_head['bill_number'] = line.split('Rechnung:')[1].split('/')[0].strip()
                    elif 'Gutschrift:' in line:
                        bill_data_head['bill_number'] = line.split('Gutschrift:')[1].split('/')[0].strip()
                elif 'Oberhaching,' in line:
                    bill_data_head['date'] = line.split('Oberhaching,')[1].strip()
                elif 'Vertragsnummer' in line:  # 找到第二页的合同号所在行
                    # 用户名在合同号上面一行
                    user_line = pages[i-1]
                    bill_data_head['driver_name'] = user_line.replace('Herr', '').replace('Frau', '').strip()
                    # 车辆型号在合同号上面两行
                    vehicle_line = pages[i-2]
                    parts = vehicle_line.split()
                    bill_data_head['vehicle_name'] = ''.join(parts[0]).strip().upper()
                elif 'Rechnung exkl. MwSt.' in line or 'Gesamtsumme Gutschrift exkl. MwSt.' in line:
                    # 开始解析详细支出项
                    for item_line in pages[i+1:]:
                        if 'Total MwSt.' in item_line:
                            break  # 遇到Total MwSt.时停止解析
                        if '%' in item_line:
                            try:
                                parts = item_line.split()
                                tax_rate = parts[0].replace('%', '')
                                if 'MwSt.' in item_line:
                                    mwst_index = item_line.find('MwSt.') + len('MwSt.')
                                    item_details = item_line[mwst_index:].strip().split()
                                else:
                                    item_details = parts[1:-2]

                                item_name = ' '.join(item_details[:-2])  # 取 `MwSt.` 后面的部分
                                amount = float(item_details[-2].replace(',', '.'))
                                tax = float(item_details[-1].replace(',', '.'))
                                total_amount = amount + tax

                                bill_data_items['items'].append({
                                    'tax_rate': tax_rate,
                                    'item_name': item_name,
                                    'amount': amount,
                                    'tax': tax,
                                    'total_amount': total_amount
                                })

                            except Exception as e:
                                # 如果解析失败，记录错误行
                                bill_data_items['errors'].append({
                                    'error': str(e),
                                    'line': item_line
                                })
                                logger.error(f"解析行时出错: {item_line}, 错误: {str(e)}")
        except Exception as e:
            logger.error(f"解析主文本时出错: {str(e)}")
        
        bill_data_head.update(bill_data_items)
        return bill_data_head

    def validate_data(self, data: Dict) -> bool:
        """
        验证提取的数据是否有效
        """
        try:
            if not data.get('bill_number'):
                logger.error("账单号缺失")
                return False
            if not data.get('date'):
                logger.error("日期缺失")
                return False
            if not data.get('user_name'):
                logger.error("用户名缺失")
                return False
            if not data.get('vehicle_name'):
                logger.error("车辆名称缺失")
                return False
            if not data.get('items'):
                logger.error("账单项目缺失")
                return False
            logger.debug("账单数据验证通过")
            return True
        except Exception as e:
            logger.exception(f"验证账单数据时发生异常: {e}")
            return False