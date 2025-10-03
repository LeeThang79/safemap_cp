import logging
from datetime import datetime, timedelta # Import timedelta để tính toán ngày trôi qua

# Import các lớp từ package community_processing
from services.community_processing.types import CommunityReport, ValidationResult
from services.community_processing.core_processor import CommunityReportProcessor
from services.community_processing.reputation import UserReputationManager
from services.community_processing.credibility import ReportCredibilityCalculator
from services.community_processing.rewards import RewardSystem

# Cấu hình logging cho demo script
# Sử dụng level DEBUG để thấy các log chi tiết hơn từ các lớp
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==================== DEMO USAGE - PHẦN LỌC ====================

def demo_filtering():
    """Demo sử dụng module lọc thông tin báo cáo"""
    processor = CommunityReportProcessor()
    
    test_reports = [
        # Báo cáo hợp lệ
        CommunityReport(
            user_id="user001",
            content="Tai nạn giao thông nghiêm trọng tại ngã tư Láng Hạ - Thái Hà lúc 14h30 hôm nay. Một xe máy va chạm với ô tô, giao thông bị ùn tắc.",
            location="Ngã tư Láng Hạ - Thái Hà",
            latitude=21.0167,
            longitude=105.8163
        ),
        
        # Thiếu thông tin thời gian (từ nội dung)
        CommunityReport(
            user_id="user002",
            content="Có cháy nhà ở quận Đống Đa, mọi người cẩn thận.",
            location="Quận Đống Đa"
            # Thêm latitude/longitude để test phần địa điểm có đủ thông tin
            , latitude=21.005, longitude=105.815 
        ),
        
        # Spam quảng cáo
        CommunityReport(
            user_id="user003",
            content="Bán hàng giảm giá sốc 50% hôm nay. Mua ngay kẻo hết. Liên hệ: 0912345678",
            location="Hà Nội",
            latitude=21.0, longitude=105.8
        ),
        
        # Nội dung vi phạm
        CommunityReport(
            user_id="user004",
            content="Con đường đm này lúc nào cũng tắc, chó chết hết đi",
            location="Đường Giải Phóng",
            latitude=21.0, longitude=105.8
        ),
        
        # Nội dung quá ngắn
        CommunityReport(
            user_id="user005",
            content="Tắc đường",
            location="Hà Nội",
            latitude=21.0, longitude=105.8
        ),
        
        # Báo cáo hợp lệ với thời gian tương đối
        CommunityReport(
            user_id="user006",
            content="Vừa xảy ra vụ cướp giật điện thoại tại khu vực Hồ Gươm lúc chiều nay khoảng 17h. Một phụ nữ bị giật túi xách khi đang đi bộ.",
            latitude=21.0285,
            longitude=105.8542
        ),
        # Báo cáo thiếu tọa độ và location_text, nhưng có thể trích xuất từ content
        CommunityReport(
            user_id="user007",
            content="Có một đám đông tụ tập trái phép ở trước cổng SVĐ Mỹ Đình vào buổi tối ngày 12 tháng 5.",
            timestamp=datetime.now() # Cung cấp timestamp để nó không bị coi là thiếu thông tin thời gian nếu không trích xuất được từ content
        ),
        # Báo cáo bằng tiếng Anh (hoặc ngôn ngữ khác)
        CommunityReport(
            user_id="user008",
            content="Traffic jam in Hanoi old quarter this morning.",
            latitude=21.03, longitude=105.85
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

def demo_credibility_system():
    """Demo hệ thống tính điểm uy tín và thưởng phạt"""
    
    print("\n" + "=" * 80)
    print("DEMO: HỆ THỐNG TÍNH UY TÍN VÀ THƯỞNG PHẠT")
    print("=" * 80)
    
    # Khởi tạo các manager
    reputation_mgr = UserReputationManager()
    credibility_calc = ReportCredibilityCalculator(reputation_mgr)
    reward_system = RewardSystem()
    
    # Mô phỏng lịch sử người dùng
    logger.info("\n[1] MÔ PHỎNG LỊCH SỬ NGƯỜI DÙNG")
    print("-" * 80)
    
    users = {
        'user_reliable': {'correct': 18, 'incorrect': 2},
        'user_average': {'correct': 10, 'incorrect': 10},
        'user_bad': {'correct': 2, 'incorrect': 15}
    }
    
    for user_id, history in users.items():
        logger.info(f"\nUser: {user_id}")
        for _ in range(history['correct']):
            reputation_mgr.update_reputation(user_id, True)
        for _ in range(history['incorrect']):
            reputation_mgr.update_reputation(user_id, False)
        
        stats = reputation_mgr.get_user_stats(user_id)
        logger.info(f"  Tổng bài: {stats['total_reports']}")
        logger.info(f"  Đúng: {stats['correct_reports']} | Sai: {stats['incorrect_reports']}")
        logger.info(f"  Độ chính xác: {stats['accuracy']:.1%}")
        logger.info(f"  Uy tín: {stats['reputation']:.3f} ({stats['level']})")
    
    # Test tính độ tin cậy của báo cáo
    logger.info("\n\n[2] TÍNH ĐỘ TIN CẬY CỦA BÁO CÁO")
    print("-" * 80)
    
    test_cases = [
        {
            'name': 'User uy tín cao, nhiều upvote',
            'user_id': 'user_reliable',
            'upvotes': 15,
            'downvotes': 2,
            'is_verified_by_news': False,
            'days_since_posted': 1
        },
        {
            'name': 'User trung bình, ít vote',
            'user_id': 'user_average',
            'upvotes': 3,
            'downvotes': 2,
            'is_verified_by_news': False,
            'days_since_posted': 2
        },
        {
            'name': 'User kém, nhiều downvote',
            'user_id': 'user_bad',
            'upvotes': 2,
            'downvotes': 10,
            'is_verified_by_news': False,
            'days_since_posted': 3
        },
        {
            'name': 'Đã xác thực bởi báo chí',
            'user_id': 'user_average',
            'upvotes': 5,
            'downvotes': 1,
            'is_verified_by_news': True,
            'days_since_posted': 5
        },
        {
            'name': 'Tin cậy thấp, đã 8 ngày (dự kiến xóa)',
            'user_id': 'user_bad',
            'upvotes': 0,
            'downvotes': 5,
            'is_verified_by_news': False,
            'days_since_posted': 8
        },
        {
            'name': 'Tin cậy trung bình, đã 15 ngày (dự kiến xóa)',
            'user_id': 'user_average',
            'upvotes': 3,
            'downvotes': 3,
            'is_verified_by_news': False,
            'days_since_posted': 15
        }
    ]
    
    for case in test_cases:
        logger.info(f"\n{case['name']}:")
        result = credibility_calc.calculate_credibility(
            case['user_id'],
            case['upvotes'],
            case['downvotes'],
            case['is_verified_by_news']
        )
        
        logger.info(f"  Điểm tin cậy: {result['credibility_score']} ({result['credibility_level']})")
        logger.info(f"  Trạng thái: {result['status']}")
        logger.info(f"  Uy tín user: {result['user_reputation']}")
        logger.info(f"  Votes: ↑{result['upvotes']} / ↓{result['downvotes']}")
        logger.info(f"  Thời gian trôi qua: {case['days_since_posted']} ngày")

        should_remove = credibility_calc.should_remove_report(
            result['credibility_score'],
            case['days_since_posted'],
            case['is_verified_by_news']
        )
        logger.info(f"  Quyết định xóa: {'✓ CÓ' if should_remove else '✗ KHÔNG'}")
        
        if 'calculation_details' in result:
            logger.info(f"  Công thức: {result['calculation_details']['formula']}")
    
    # Test hệ thống thưởng
    logger.info("\n\n[3] HỆ THỐNG THƯỞNG")
    print("-" * 80)
    
    reward_cases = [
        {'user_id': 'user_reliable', 'high_posts': 12, 'total_upvotes': 80}, # Đủ điều kiện
        {'user_id': 'user_average', 'high_posts': 5, 'total_upvotes': 30}, # Thiếu bài uy tín cao và upvotes
        {'user_id': 'user_bad', 'high_posts': 1, 'total_upvotes': 5} # Thiếu nghiêm trọng
    ]
    
    for case in reward_cases:
        logger.info(f"\nUser: {case['user_id']}")
        reward = reward_system.calculate_reward(
            case['user_id'],
            case['high_posts'],
            case['total_upvotes']
        )
        
        logger.info(f"  Bài uy tín cao: {case['high_posts']}")
        logger.info(f"  Tổng upvotes: {case['total_upvotes']}")
        logger.info(f"  Đủ điều kiện: {'✓ CÓ' if reward['eligible'] else '✗ KHÔNG'}")
        logger.info(f"  Lý do: {reward['reason']}")
        if reward['eligible']:
            logger.info(f"  💰 Thưởng: {reward['reward_amount']:,} VND")
    
    # Test hệ thống phạt
    logger.info("\n\n[4] HỆ THỐNG PHẠT")
    print("-" * 80)
    
    penalty_cases = [
        {'name': 'User có 2 bài kém', 'user_id': 'pen_user_1', 'low_posts': 2, 'fake_sos': 0}, # Không phạt
        {'name': 'User có 4 bài kém', 'user_id': 'pen_user_2', 'low_posts': 4, 'fake_sos': 0}, # Cấp 1: Hạn chế thưởng
        {'name': 'User có 6 bài kém', 'user_id': 'pen_user_3', 'low_posts': 6, 'fake_sos': 0}, # Cấp 2: Cấm tạm thời
        {'name': 'User có 12 bài kém', 'user_id': 'pen_user_4', 'low_posts': 12, 'fake_sos': 0}, # Cấp 3: Cấm vĩnh viễn
        {'name': 'User gửi 1 SOS giả', 'user_id': 'pen_user_5', 'low_posts': 0, 'fake_sos': 1}, # Cấm 90 ngày
        {'name': 'User gửi 2 SOS giả', 'user_id': 'pen_user_6', 'low_posts': 0, 'fake_sos': 2}, # Cấm 180 ngày
        {'name': 'User gửi 3 SOS giả', 'user_id': 'pen_user_7', 'low_posts': 0, 'fake_sos': 3}, # Cấm vĩnh viễn
        {'name': 'User có 4 bài kém & 1 SOS giả', 'user_id': 'pen_user_8', 'low_posts': 4, 'fake_sos': 1} # Cấm 90 ngày (SOS nặng hơn)
    ]
    
    for case in penalty_cases:
        logger.info(f"\n{case['name']}: (User: {case['user_id']})")
        penalty = reward_system.check_penalty(case['user_id'], case['low_posts'], case['fake_sos'])
        
        if penalty['has_penalty']:
            logger.info(f"  ⚠️  Hình phạt: {penalty['penalty_type']}")
            logger.info(f"  Lý do: {penalty['reason']}")
            if penalty['ban_duration_days'] == -1:
                logger.info(f"  Thời hạn: VĨnh viễn")
            elif penalty['ban_duration_days'] > 0:
                logger.info(f"  Thời hạn: {penalty['ban_duration_days']} ngày")
            logger.info(f"  Đăng bài: {'✗' if not penalty.get('can_post', True) else '✓'}")
            logger.info(f"  Tương tác: {'✗' if not penalty.get('can_interact', True) else '✓'}")
            if penalty.get('reward_disabled'):
                logger.info(f"  Nhận thưởng: ✗")
        else:
            logger.info(f"  ✓ Không có hình phạt")


if __name__ == "__main__":
    # Chạy các hàm demo
    demo_filtering()
    demo_credibility_system()