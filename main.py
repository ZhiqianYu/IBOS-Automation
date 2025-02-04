from pdf_extractor import PDFExtractor
from db_manager import DBManager
import logging
import argparse
from pathlib import Path

def setup_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='PDF账单数据提取工具')
    parser.add_argument('bills_path', nargs='?', default='Bills', help='账单文件夹路径 (默认: Bills)')
    parser.add_argument('-v', '--verbose', action='store_true', help='显示详细日志')
    return parser

def process_pdf(pdf_path: Path, extractor: PDFExtractor, db: DBManager):
    """ 处理单个 PDF 账单 """
    logging.info(f"处理文件: {pdf_path.name}")
    bill_data = extractor.extract_bill_data(str(pdf_path))

    if bill_data and extractor.validate_data(bill_data):
        bill_id = db.add_bill(bill_data, pdf_path.name)
        db.add_bill_items(bill_id, bill_data["items"], pdf_path.name)
        logging.info(f"账单 {bill_data['bill_number']} ({pdf_path.name}) 已存入数据库")
        print(f"\n{pdf_path.name} 提取成功:\n{bill_data}\n")
    else:
        logging.error(f"账单提取失败: {pdf_path.name}")

def main():
    parser = setup_argparser()
    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    bills_path = Path(args.bills_path)
    if not bills_path.exists() or not bills_path.is_dir():
        logging.error(f"指定的账单目录不存在: {bills_path}")
        return

    extractor = PDFExtractor()
    db = DBManager()

    pdf_files = list(bills_path.glob("*.pdf"))
    if not pdf_files:
        logging.warning(f"目录 {bills_path} 中未找到 PDF 文件")
        return

    for pdf_file in pdf_files:
        process_pdf(pdf_file, extractor, db)

if __name__ == "__main__":
    main()
