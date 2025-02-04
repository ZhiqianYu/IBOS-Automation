from pdf_extractor import PDFExtractor
import logging
import argparse
from pathlib import Path

def setup_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='PDF账单数据提取工具')
    parser.add_argument('pdf_path', help='PDF文件路径')
    parser.add_argument('-v', '--verbose', action='store_true', help='显示详细日志')
    return parser

def main():
    parser = setup_argparser()
    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    try:
        pdf_path = Path(args.pdf_path)
        if not pdf_path.exists():
            logger.error(f"文件不存在: {pdf_path}")
            return

        extractor = PDFExtractor()
        bill_data = extractor.extract_bill_data(str(pdf_path))
        
        if bill_data and extractor.validate_data(bill_data):
            for key, value in bill_data.items():
                print(f"{key}: {value}")
                print("Writing data to DB...")
        else:
            logger.error("数据提取失败")

    except Exception as e:
        logger.error(f"处理出错: {str(e)}")

if __name__ == "__main__":
    main()