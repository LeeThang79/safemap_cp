import logging
import math
from typing import Dict
from config import Config

logger = logging.getLogger(__name__)

class ReportCredibilityCalculator:
    """Tính toán độ tin cậy của báo cáo"""
    
    def __init__(self):
        self.w1 = Config.REPUTATION_WEIGHT_W1 # Trọng số uy tín người đăng
        self.w2 = Config.AGREE_VOTE_WEIGHT_W2 # Trọng số lượt đồng ý
        self.w3 = Config.DISAGREE_VOTE_WEIGHT_W3 # Trọng số lượt không đồng ý (âm)

        self.min_votes_threshold = Config.MIN_VOTES_THRESHOLD # Ngưỡng số vote tối thiểu
        self.sigmoid_k = Config.SIGMOID_K # Tham số điều chỉnh độ dốc sigmoid

        self.credibility_threshold_high = Config.CREDIBILITY_THRESHOLD_HIGH
        self.credibility_threshold_medium = Config.CREDIBILITY_THRESHOLD_MEDIUM
        self.credibility_threshold_low_remove = Config.CREDIBILITY_THRESHOLD_LOW_REMOVE
        self.credibility_threshold_medium_remove = Config.CREDIBILITY_THRESHOLD_MEDIUM_REMOVE
        self.days_threshold_low_remove = Config.DAYS_THRESHOLD_LOW_REMOVE
        self.days_threshold_medium_remove = Config.DAYS_THRESHOLD_MEDIUM_REMOVE

    def calculate_credibility(
        self,
        user_id: str,
        upvotes: int,
        downvotes: int,
        is_verified_by_news: bool = False
    ) -> Dict:
        """
        Tính điểm tin cậy của báo cáo
        """
        if is_verified_by_news:
            return {
                'credibility_score': 1.0,
                'credibility_level': 'Cao',
                'status': 'Đã xác thực bởi nguồn chính thống',
                'user_reputation': self.reputation_manager.get_reputation(user_id),
                'upvotes': upvotes,
                'downvotes': downvotes,
                'total_votes': upvotes + downvotes
            }
        
        x = self.reputation_manager.get_reputation(user_id)
        total_votes = upvotes + downvotes
        
        y_normalized = self._sigmoid_normalize(upvotes, self.sigmoid_k)
        z_normalized = self._sigmoid_normalize(downvotes, self.sigmoid_k)
        
        credibility_score = (
            self.w1 * x +
            self.w2 * y_normalized +
            self.w3 * z_normalized
        )
        
        # Chuẩn hóa tổng trọng số để điểm nằm trong [0,1]
        # (chỉ khi có đủ các yếu tố tham gia)
        sum_of_weights = self.w1 + abs(self.w2) + abs(self.w3)
        if sum_of_weights > 0:
            credibility_score /= sum_of_weights

        credibility_score = max(0.0, min(1.0, credibility_score))
        
        credibility_level = self._get_credibility_level(credibility_score)
        
        if total_votes < self.min_votes_threshold:
            status = f"Chưa xác thực (cần thêm {self.min_votes_threshold - total_votes} đánh giá)"
        else:
            status = "Đã đánh giá bởi cộng đồng"
        
        return {
            'credibility_score': round(credibility_score, 3),
            'credibility_level': credibility_level,
            'status': status,
            'user_reputation': round(x, 3),
            'upvotes': upvotes,
            'downvotes': downvotes,
            'total_votes': total_votes,
            'calculation_details': {
                'x_user_reputation': round(x, 3),
                'y_upvotes_normalized': round(y_normalized, 3),
                'z_downvotes_normalized': round(z_normalized, 3),
                'formula': f"({self.w1}*{round(x,3)} + {self.w2}*{round(y_normalized,3)} + {self.w3}*{round(z_normalized,3)}) / {round(sum_of_weights,3)}"
            }
        }
    
    def _sigmoid_normalize(self, value: int, k: float) -> float:
        """Chuẩn hóa giá trị bằng hàm sigmoid"""
        return 1 / (1 + math.exp(-k * value))
    
    def _get_credibility_level(self, score: float) -> str:
        """Chuyển điểm tin cậy thành mức độ"""
        if score >= self.credibility_threshold_high: return "Cao"
        elif score >= self.credibility_threshold_medium: return "Trung bình"
        else: return "Thấp"
    
    def should_remove_report(
        self,
        credibility_score: float,
        days_since_posted: int,
        is_verified_by_news: bool
    ) -> bool:
        """
        Quyết định có nên xóa báo cáo không
        """
        if is_verified_by_news:
            return False
        
        if days_since_posted >= self.days_threshold_medium_remove and credibility_score < self.credibility_threshold_medium_remove:
            logger.info(f"Report removal: {credibility_score:.2f} after {days_since_posted} days (threshold {self.credibility_threshold_medium_remove} after {self.days_threshold_medium_remove} days)")
            return True
        
        if days_since_posted >= self.days_threshold_low_remove and credibility_score < self.credibility_threshold_low_remove:
            logger.info(f"Report removal: {credibility_score:.2f} after {days_since_posted} days (threshold {self.credibility_threshold_low_remove} after {self.days_threshold_low_remove} days)")
            return True
        
        return False