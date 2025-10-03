import logging
from typing import Dict

logger = logging.getLogger(__name__)

class UserReputationManager:
    """Quản lý điểm uy tín người dùng"""
    
    def __init__(self):
        # Trong thực tế dùng database (ví dụ: Redis, PostgreSQL)
        self.user_reputation = {}  # {user_id: reputation_score}
        self.user_history = {}  # {user_id: {'correct': int, 'incorrect': int, 'total': int}}
        
        self.default_reputation = 0.5
        self.min_reputation = 0.0
        self.max_reputation = 1.0
        self.learning_rate = 0.1 # Tốc độ học của uy tín
    
    def get_reputation(self, user_id: str) -> float:
        """Lấy điểm uy tín hiện tại của user"""
        if user_id not in self.user_reputation:
            self.user_reputation[user_id] = self.default_reputation
            self.user_history[user_id] = {'correct': 0, 'incorrect': 0, 'total': 0}
        return self.user_reputation[user_id]
    
    def update_reputation(self, user_id: str, is_correct: bool):
        """
        Cập nhật uy tín sau khi xác thực bài đăng
        is_correct: True nếu bài đăng được xác nhận đúng, False nếu sai/spam
        """
        current = self.get_reputation(user_id) # Ensures history is initialized
        history = self.user_history[user_id]
        
        history['total'] += 1
        if is_correct:
            history['correct'] += 1
        else:
            history['incorrect'] += 1
        
        if history['total'] > 0:
            accuracy = history['correct'] / history['total']
            new_reputation = current * (1 - self.learning_rate) + accuracy * self.learning_rate
            new_reputation = max(self.min_reputation, min(self.max_reputation, new_reputation))
            self.user_reputation[user_id] = new_reputation
            
            logger.info(f"User {user_id} reputation updated: {current:.3f} -> {new_reputation:.3f} (Correct: {history['correct']}, Incorrect: {history['incorrect']})")
    
    def get_user_stats(self, user_id: str) -> Dict:
        """Lấy thống kê chi tiết của user"""
        rep = self.get_reputation(user_id)
        history = self.user_history[user_id]
        
        accuracy = history['correct'] / history['total'] if history['total'] > 0 else 0
        
        return {
            'user_id': user_id,
            'reputation': rep,
            'total_reports': history['total'],
            'correct_reports': history['correct'],
            'incorrect_reports': history['incorrect'],
            'accuracy': accuracy,
            'level': self._get_reputation_level(rep)
        }
    
    def _get_reputation_level(self, reputation: float) -> str:
        """Chuyển điểm uy tín thành cấp độ"""
        if reputation >= 0.9: return "Xuất sắc"
        elif reputation >= 0.75: return "Tốt"
        elif reputation >= 0.5: return "Trung bình"
        elif reputation >= 0.3: return "Thấp"
        else: return "Rất thấp"