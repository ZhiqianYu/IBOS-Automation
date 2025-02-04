from pdf_extractor import PDFExtractor
from db_manager import DBManager
import logging
import argparse
from pathlib import Path

def setup_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='PDF账单数据提取工具')
    parser.add_argument('bills_path', nargs='?', default='Bills', help='账单文件夹路径 (默认: Bills)')
    parser.add_argument('-v', '--verbose', action='store_true', help='显示详细日志')
    parser.add_argument('-d', '--details', action='store_true', help='显示详细提取信息')
    return parser

def process_pdf(pdf_path: Path, extractor: PDFExtractor, db: DBManager, show_details: bool, verbose: bool):
    """ 处理单个 PDF 账单 """
    logging.debug(f"处理文件: {pdf_path.name}...")
    bill_data = extractor.extract_bill_data(str(pdf_path))

    if bill_data and extractor.validate_data(bill_data):
        bill_id = db.add_bill(bill_data, pdf_path.name)
        for item in bill_data["items"]:
            db.add_bill_item(bill_id, item)
        logging.debug(f"账单 {bill_data['bill_number']} ({pdf_path.name}) 已存入数据库")
        if show_details:
            print(f"\n{pdf_path.name} 提取成功:\n{bill_data}\n")
        elif verbose:
            print(f"\n{bill_data['bill_number']} {pdf_path.name} 提取成功\n")
    else:
        logging.error(f"账单提取失败: {pdf_path.name}")

def main():
    parser = setup_argparser()
    args = parser.parse_args()

    logging.basicConfig(level=logging.WARNING)  # 默认日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)

    extractor = PDFExtractor()
    db = DBManager()

    bills_path = Path(args.bills_path)
    if not bills_path.exists() or not bills_path.is_dir():
        logging.error(f"账单文件夹路径无效: {bills_path}")
        return

    for pdf_file in bills_path.glob("*.pdf"):
        process_pdf(pdf_file, extractor, db, args.details, args.verbose)

if __name__ == "__main__":
    main()
