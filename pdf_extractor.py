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
                return self._parse_bill_text(text)

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
            'vehicle_model': None
        }

        bill_data_items = {
            'items': [],
            'errors': []
        }
        
        try:
            pages = text.split('\n')
            for i, line in enumerate(pages):
                if 'Rechnung:' in line:
                    bill_data_head['bill_number'] = line.split('Rechnung:')[1].split('/')[0].strip()
                elif 'Oberhaching,' in line:
                    bill_data_head['date'] = line.split('Oberhaching,')[1].strip()
                elif 'Vertragsnummer' in line:  # 找到第二页的合同号所在行
                    # 用户名在合同号上面一行
                    user_line = pages[i-1]
                    bill_data_head['driver_name'] = user_line.replace('Herr', '').replace('Frau', '').strip()
                    # 车辆型号在合同号上面两行
                    vehicle_line = pages[i-2]
                    parts = vehicle_line.split()
                    bill_data_head['vehicle_model'] = f"{parts[0]} {parts[1]}"
                elif 'Rechnung exkl. MwSt.' in line:
                    # 开始解析详细支出项
                    for item_line in pages[i+1:]:
                        if 'Total MwSt.' in item_line:
                            break  # 遇到Total MwSt.时停止解析
                        if '%' in item_line:
                            try:
                                parts = item_line.split()
                                tax_rate = parts[0].replace('%', '')
                                item_name = ' '.join(parts[1:-2])
                                amount = float(parts[-2].replace(',', '.'))
                                tax = float(parts[-1].replace(',', '.'))
                                bill_data_items['items'].append({
                                    'tax_rate': tax_rate,
                                    'item_name': item_name,
                                    'amount': amount,
                                    'tax': tax
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
        验证提取的数据是否完整
        """
        required_fields = ['bill_number', 'date', 'driver_name', 'vehicle_model']
        return all(data.get(field) for field in required_fields)