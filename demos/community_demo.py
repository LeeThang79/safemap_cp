import logging
from datetime import datetime

# Import các lớp cần thiết
from services.community_processing.types import CommunityReport
from services.community_processing.core_processor import CommunityReportProcessor

# Cấu hình logging cho demo script
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==================== DEMO USAGE - PHẦN LỌC ====================

def demo_filtering():
    """Demo kiểm tra lọc thông tin báo cáo"""
    processor = CommunityReportProcessor()
    
    test_reports = [
        # Báo cáo hợp lệ tiếng Việt
        CommunityReport(
            user_id="user001",
            content="Đạo chó ngu",
            location="Ngã tư Láng Hạ - Thái Hà",
            latitude=21.0167,
            longitude=105.8163
        ),
        
        # Spam bán hàng
        CommunityReport(
            user_id="user002",
            content="Liên hệ: 01212817412",
            location="Hà Nội",
            latitude=21.0,
            longitude=105.8
        ),
        
        # Nội dung chửi bậy
        CommunityReport(
            user_id="user003",
            content="Con đường này lúc nào cũng tắc, đm thật",
            location="Đường Giải Phóng",
            latitude=21.0,
            longitude=105.8
        ),
        
        # Nội dung quá ngắn
        CommunityReport(
            user_id="user004",
            content="Tắc đường",
            location="Hà Nội",
            latitude=21.0,
            longitude=105.8
        ),
        
        # Tiếng Anh (không hợp lệ)
        CommunityReport(
            user_id="user005",
            content="Traffic jam in Hanoi old quarter this morning.",
            latitude=21.03,
            longitude=105.85
        )
    ]
    
    print("\n" + "=" * 80)
    print("DEMO: Xử lý báo cáo từ cộng đồng - PHẦN LỌC")
    print("=" * 80)
    
    for i, report in enumerate(test_reports, 1):
        logger.info(f"\n[TEST {i}] User: {report.user_id}")
        logger.info(f"Content: {report.content[:70]}...") # Giới hạn độ dài content để dễ đọc
        logger.info(f"Location (from report object): Text='{report.location}', Lat={report.latitude}, Lon={report.longitude}")
        
        result = processor.process_report(report)
        
        logger.info(f"Status: {'✓ HỢP LỆ' if result.is_valid else '✗ KHÔNG HỢP LỆ'}")
        logger.info(f"Lý do: {result.reason}")
        
        if result.extracted_info:
            logger.info(f"Thông tin trích xuất từ nội dung:")
            logger.info(f"  - Ngày: {result.extracted_info['datetime']['date']}")
            logger.info(f"  - Giờ: {result.extracted_info['datetime']['time']}")
            logger.info(f"  - Địa điểm: {result.extracted_info['location']}")
        
        print("-" * 80)

# ==================== DEMO UY TÍN & THƯỞNG PHẠT ====================


    
    users = {
        'user_reliable': {'correct': 18, 'incorrect': 2},
        'user_average': {'correct': 10, 'incorrect': 10},
        'user_bad': {'correct': 2, 'incorrect': 15}
    }
    
    print("\n" + "=" * 80)
    print("DEMO: KIỂM TRA LỌC BÁO CÁO CỘNG ĐỒNG")
    print("=" * 80)
    
    for i, report in enumerate(test_reports, 1):
        logger.info(f"\n[TEST {i}] User: {report.user_id}")
        logger.info(f"Content: {report.content}")
        logger.info(f"Location: Text='{report.location}', Lat={report.latitude}, Lon={report.longitude}")
        
        result = processor.process_report(report)
        
        logger.info(f"Status: {'✓ HỢP LỆ' if result.is_valid else '✗ KHÔNG HỢP LỆ'}")
        logger.info(f"Lý do: {result.reason}")
        print("-" * 80)


if __name__ == "__main__":
    demo_filtering()