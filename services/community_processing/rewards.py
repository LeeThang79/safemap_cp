import logging
from typing import Dict
from config import Config

logger = logging.getLogger(__name__)

class RewardSystem:
    """Hệ thống thưởng phạt"""
    
    def __init__(self):
        self.high_credibility_threshold = Config.HIGH_CREDIBILITY_THRESHOLD
        self.min_posts_for_reward = Config.MIN_POSTS_FOR_REWARD
        self.min_total_upvotes = Config.MIN_TOTAL_UPVOTES
        self.reward_per_high_credibility_post = Config.REWARD_PER_HIGH_CREDIBILITY_POST
        
        self.low_credibility_threshold_penalty = Config.LOW_CREDIBILITY_THRESHOLD_PENALTY
        self.ban_level_1_threshold = Config.BAN_LEVEL_1_THRESHOLD
        self.ban_level_2_threshold = Config.BAN_LEVEL_2_THRESHOLD
        self.ban_level_3_threshold = Config.BAN_LEVEL_3_THRESHOLD
        
        self.fake_sos_ban_duration = Config.FAKE_SOS_BAN_DURATION
    
    def calculate_reward(
        self,
        user_id: str, # user_id để log
        high_credibility_posts: int,
        total_upvotes: int
    ) -> Dict:
        """
        Tính toán phần thưởng cho user
        """
        if high_credibility_posts < self.min_posts_for_reward:
            logger.info(f"User {user_id}: Không đủ bài uy tín cao ({high_credibility_posts}/{self.min_posts_for_reward}) để nhận thưởng.")
            return {
                'eligible': False,
                'reason': f"Cần ít nhất {self.min_posts_for_reward} bài đăng có độ uy tín cao",
                'reward_amount': 0
            }
        
        if total_upvotes < self.min_total_upvotes:
            logger.info(f"User {user_id}: Không đủ lượt đồng ý ({total_upvotes}/{self.min_total_upvotes}) để nhận thưởng.")
            return {
                'eligible': False,
                'reason': f"Cần ít nhất {self.min_total_upvotes} lượt đồng ý",
                'reward_amount': 0
            }
        
        reward_amount = high_credibility_posts * self.reward_per_high_credibility_post
        logger.info(f"User {user_id}: Đủ điều kiện nhận thưởng {reward_amount:,} VND.")
        return {
            'eligible': True,
            'reason': 'Đủ điều kiện nhận thưởng',
            'reward_amount': reward_amount,
            'high_credibility_posts': high_credibility_posts,
            'total_upvotes': total_upvotes
        }
    
    def check_penalty(
        self,
        user_id: str, # user_id để log
        low_credibility_posts: int,
        fake_sos_count: int
    ) -> Dict:
        """
        Kiểm tra và áp dụng hình phạt
        """
        penalty = {
            'has_penalty': False,
            'penalty_type': None,
            'reason': None,
            'ban_duration_days': 0,
            'can_post': True, # Mặc định được đăng
            'can_interact': True, # Mặc định được tương tác
            'reward_disabled': False # Mặc định được nhận thưởng
        }
        
        # Kiểm tra phạt do bài đăng kém chất lượng
        if low_credibility_posts >= self.ban_level_3_threshold:
            penalty['has_penalty'] = True
            penalty['penalty_type'] = 'Cấm vĩnh viễn'
            penalty['reason'] = f'Có {low_credibility_posts} bài đăng độ uy tín thấp (>= {self.ban_level_3_threshold})'
            penalty['ban_duration_days'] = -1
            penalty['can_post'] = False
            penalty['can_interact'] = False
            
        elif low_credibility_posts >= self.ban_level_2_threshold:
            penalty['has_penalty'] = True
            penalty['penalty_type'] = 'Cấm tạm thời - Mức 2'
            penalty['reason'] = f'Có {low_credibility_posts} bài đăng độ uy tín thấp (>= {self.ban_level_2_threshold})'
            penalty['ban_duration_days'] = 30
            penalty['can_post'] = False
            penalty['can_interact'] = False
            
        elif low_credibility_posts >= self.ban_level_1_threshold:
            penalty['has_penalty'] = True
            penalty['penalty_type'] = 'Hạn chế - Mức 1'
            penalty['reason'] = f'Có {low_credibility_posts} bài đăng độ uy tín thấp (>= {self.ban_level_1_threshold})'
            penalty['ban_duration_days'] = 0 # Không cấm, chỉ hạn chế
            penalty['reward_disabled'] = True
        
        # Kiểm tra phạt do SOS giả (có thể override penalty từ bài đăng nếu nặng hơn)
        if fake_sos_count > 0:
            sos_penalty_days = self.fake_sos_ban_duration.get(
                min(fake_sos_count, 3), # Tối đa 3 lần để lấy mức phạt
                self.fake_sos_ban_duration[3] # Mức 3 là vĩnh viễn
            )
            
            # Nếu hình phạt SOS giả nặng hơn hình phạt hiện tại
            if not penalty['has_penalty'] or sos_penalty_days == -1 or sos_penalty_days > penalty['ban_duration_days']:
                penalty['has_penalty'] = True
                penalty['penalty_type'] = f'Cấm {sos_penalty_days} ngày do SOS giả' if sos_penalty_days > 0 else 'Cấm vĩnh viễn do SOS giả'
                penalty['reason'] = f'Gửi SOS giả {fake_sos_count} lần'
                penalty['ban_duration_days'] = sos_penalty_days
                penalty['can_post'] = False
                penalty['can_interact'] = False
        
        if penalty['has_penalty']:
            logger.warning(f"User {user_id}: Áp dụng hình phạt: {penalty['penalty_type']} - Lý do: {penalty['reason']}")
        else:
            logger.info(f"User {user_id}: Không có hình phạt.")

        return penalty