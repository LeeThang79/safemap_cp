import uuid
import time
import json
from datetime import datetime
from typing import Dict, Any, List, Tuple
import numpy as np
import logging

from utils.redis_utils import RedisClient
from utils.nlp_utils import nlp_processor # Vẫn dùng nlp_processor từ utils/
from config import Config

# Import từ package community_processing
from services.community_processing.types import CommunityReport, ValidationResult
from services.community_processing.core_processor import CommunityReportProcessor
from services.community_processing.reputation import UserReputationManager
from services.community_processing.credibility import ReportCredibilityCalculator
from services.community_processing.rewards import RewardSystem

logger = logging.getLogger(__name__)
redis_conn = RedisClient().get_client()

# Mock storage for existing events to check for duplicates
# In a real app, this would be a DB query, potentially with vector search capabilities (e.g., PostGIS with pgvector)
MOCK_EXISTING_EVENTS: List[Dict[str, Any]] = []

class CommunityReportService:
    def __init__(self):
        self.report_processor = CommunityReportProcessor()
        self.reputation_manager = UserReputationManager()
        self.credibility_calculator = ReportCredibilityCalculator(self.reputation_manager)
        self.reward_system = RewardSystem()

    async def process_new_report(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes a new community report: rate limits, filters, classifies, checks for duplicates,
        and prepares it for storage/verification.
        """
        user_id = report_data.get("user_id", "anonymous")
        content = report_data.get("description", "")
        location_text = report_data.get("location_text") # If user provides text location
        latitude = report_data.get("latitude")
        longitude = report_data.get("longitude")

        # Tạo đối tượng CommunityReport
        report_obj = CommunityReport(
            user_id=user_id,
            content=content,
            location=location_text,
            latitude=latitude,
            longitude=longitude,
            timestamp=datetime.now() # Thời điểm gửi báo cáo
        )

        # --- Lọc ban đầu và kiểm tra tính hợp lệ ---

        # 1. Rate Limiting (Kiểm tra tần suất gửi báo cáo của người dùng)
        if not self._check_rate_limit(user_id):
            logger.warning(f"User {user_id}: Rate limit exceeded for new report.")
            return {"status": "error", "message": "Giới hạn tần suất báo cáo đã bị vượt quá. Vui lòng thử lại sau.", "code": "RATE_LIMIT_EXCEEDED"}

        # 2. Layered Validation (Lọc theo lớp sử dụng CommunityReportProcessor)
        validation_result = self.report_processor.process_report(report_obj)
        if not validation_result.is_valid:
            logger.warning(f"User {user_id}: Invalid report - {validation_result.reason}")
            return {"status": "error", "message": validation_result.reason, "code": "INVALID_REPORT"}
        
        # Nếu hợp lệ, sử dụng nội dung đã lọc và thông tin đã trích xuất
        processed_content = validation_result.filtered_content
        extracted_info = validation_result.extracted_info
        
        # Cập nhật tọa độ từ extracted_info nếu chưa có từ report_data và trích xuất được
        if not (report_obj.latitude and report_obj.longitude) and extracted_info and extracted_info['location']:
            # Ở đây bạn sẽ gọi Geocoding API (ví dụ: Google Maps Geocoding)
            # để chuyển `extracted_info['location']` thành lat/lon.
            # lat, lon = await geocoder_utils.geocode(extracted_info['location'])
            # report_obj.latitude = lat
            # report_obj.longitude = lon
            logger.info(f"DEBUG: Địa điểm trích xuất từ nội dung: {extracted_info['location']}")
            # Để demo, gán tạm nếu có thể (chỉ khi có mock geocoding hoặc giá trị mặc định)
            if "Láng Hạ" in extracted_info['location']:
                report_obj.latitude = 21.0167
                report_obj.longitude = 105.8163
            elif "Mỹ Đình" in extracted_info['location']:
                report_obj.latitude = 21.0177
                report_obj.longitude = 105.7766
            elif "Đống Đa" in extracted_info['location']:
                report_obj.latitude = 21.005
                report_obj.longitude = 105.815
            # ... (thêm logic geocoding thực tế ở đây)

        if not (report_obj.latitude is not None and report_obj.longitude is not None):
            logger.warning(f"User {user_id}: Could not determine precise geolocation for report.")
            return {"status": "error", "message": "Không thể xác định tọa độ địa lý chính xác cho báo cáo.", "code": "MISSING_GEOLOCATION"}

        # --- Xử lý NLP và Phân loại ---

        # 3. NLP Processing: Embedding, Topic/Urgency Classification
        embedding = nlp_processor.get_embedding(processed_content)
        
        if np.all(embedding == 0):
             logger.warning(f"User {user_id}: Report content too generic for NLP embedding.")
             return {"status": "error", "message": "Nội dung báo cáo không đủ thông tin để xử lý bằng AI.", "code": "INSUFFICIENT_NLP_INFO"}

        topic, urgency = nlp_processor.classify_topic_and_urgency(embedding)

        # --- Kiểm tra trùng lặp ---

        # 4. Duplicate Checking (Kiểm tra xem có báo cáo/sự kiện nào trùng lặp không)
        current_location_dict = {"lat": report_obj.latitude, "lon": report_obj.longitude}
        existing_event_id, similarity = self._check_for_duplicates(embedding, topic, current_location_dict)
        
        if existing_event_id:
            if similarity >= Config.COSINE_SIMILARITY_THRESHOLD_DUPLICATE:
                logger.info(f"User {user_id}: Report is a duplicate of {existing_event_id} (similarity: {similarity:.2f}). Discarding new report.")
                return {"status": "success", "message": "Báo cáo này có vẻ là trùng lặp với một sự kiện đã có và sẽ không được tạo mới.", "code": "DUPLICATE_REPORT", "event_id": existing_event_id}
            elif similarity >= Config.COSINE_SIMILARITY_THRESHOLD_REFERENCE:
                logger.info(f"User {user_id}: Report similar to {existing_event_id} (similarity: {similarity:.2f}). Could be a reference.")

        # --- Lưu trữ và phản hồi ---

        # 5. Store Report (Lưu báo cáo vào cơ sở dữ liệu hoặc hàng đợi)
        report_id = str(uuid.uuid4())
        
        # Lấy uy tín người dùng tại thời điểm đăng
        user_reputation_at_submit = self.reputation_manager.get_reputation(user_id)

        new_report_data = {
            "id": report_id,
            "user_id": user_id,
            "description": processed_content,
            "location_text": report_obj.location,
            "latitude": report_obj.latitude,
            "longitude": report_obj.longitude,
            "embedding": embedding.tolist(), # Lưu embedding để so sánh sau
            "topic": topic,
            "urgency": urgency,
            "status": "pending_verification", # Trạng thái ban đầu
            "reliability_score": self.credibility_calculator.calculate_credibility(user_id, 0, 0)['credibility_score'], # Điểm tin cậy ban đầu
            "created_at": report_obj.timestamp.isoformat(), # Lưu dạng ISO string
            "updated_at": datetime.now().isoformat(),
            "votes_up": 0,
            "votes_down": 0,
            "official_sources": [],
            "user_reputation_at_submit": user_reputation_at_submit
        }

        # Lưu vào Redis Hash để dễ dàng truy cập và cập nhật bởi các chức năng vote/xác thực
        # Chuyển đổi các giá trị không phải string sang JSON string trước khi hset
        hset_data = {k: json.dumps(v) if isinstance(v, (list, dict)) else str(v) for k,v in new_report_data.items()}
        redis_conn.hset(f"report:{report_id}", mapping=hset_data)
        redis_conn.expire(f"report:{report_id}", Config.REPORT_EXPIRE_SECONDS_FOR_UNVERIFIED) # Đặt thời gian hết hạn

        # Thêm vào danh sách mock để demo kiểm tra trùng lặp
        MOCK_EXISTING_EVENTS.append({"id": report_id, "embedding": embedding, "topic": topic, "location": current_location_dict, "source_type": "community"})

        logger.info(f"User {user_id}: New report {report_id} processed successfully. Status: {new_report_data['status']}.")

        return {"status": "success", "message": "Báo cáo đã được gửi thành công và đang chờ xác thực cộng đồng.", "report_id": report_id, "data": new_report_data}

    def _check_rate_limit(self, user_id: str) -> bool:
        key = f"rate_limit:community_report:{user_id}"
        count = redis_conn.incr(key)
        if count == 1:
            redis_conn.expire(key, 60)
        return count <= Config.RATE_LIMIT_REPORTS_PER_MINUTE

    def _check_for_duplicates(self, new_embedding: np.ndarray, topic: str, location: Dict[str, float]) -> Tuple[str | None, float]:
        """
        Kiểm tra trùng lặp với các sự kiện/báo cáo đã có.
        """
        closest_event_id = None
        highest_similarity = 0.0

        for event in MOCK_EXISTING_EVENTS:
            # Kiểm tra vị trí địa lý gần nhau
            dist_lat = abs(event["location"]["lat"] - location["lat"])
            dist_lon = abs(event["location"]["lon"] - location["lon"])
            
            if dist_lat < 0.02 and dist_lon < 0.02: # Giả định khoảng cách ~2km
                similarity = nlp_processor.calculate_cosine_similarity(new_embedding, event["embedding"])
                
                if similarity > highest_similarity:
                    highest_similarity = similarity
                    closest_event_id = event["id"]
        
        if highest_similarity >= Config.COSINE_SIMILARITY_THRESHOLD_REFERENCE:
            return closest_event_id, highest_similarity
        return None, 0.0

    async def update_report_status_after_vote(self, report_id: str, voter_id: str, vote_type: str):
        """
        Cập nhật số lượt vote và tính toán lại điểm tin cậy cho báo cáo.
        """
        # --- Lấy thông tin báo cáo từ Redis ---
        report_data_raw = redis_conn.hgetall(f"report:{report_id}")
        if not report_data_raw:
            logger.error(f"Report {report_id} not found for voting.")
            raise ValueError(f"Report {report_id} not found.")

        # Decode values from Redis (hset stores everything as strings)
        # Handle fields that were stored as JSON strings
        current_report = {
            k.decode('utf-8'): json.loads(v.decode('utf-8')) if k.decode('utf-8') in ["embedding"] else v.decode('utf-8')
            for k,v in report_data_raw.items()
        }
        current_report["votes_up"] = int(current_report.get("votes_up", 0))
        current_report["votes_down"] = int(current_report.get("votes_down", 0))
        current_report["reliability_score"] = float(current_report.get("reliability_score", 0.0))
        current_report["user_reputation_at_submit"] = float(current_report.get("user_reputation_at_submit", 0.5))
        current_report["status"] = current_report.get("status", "pending_verification")
        current_report["user_id"] = current_report.get("user_id", "anonymous")

        # Ngăn không cho người đăng tự vote
        if voter_id == current_report["user_id"]:
            logger.warning(f"User {voter_id} attempted to vote on their own report {report_id}.")
            raise ValueError("Cannot vote on your own report.")

        # Kiểm tra xem người dùng đã vote cho báo cáo này chưa
        vote_key = f"user_vote:{voter_id}:{report_id}"
        previous_vote = redis_conn.get(vote_key)
        
        if previous_vote == vote_type:
            logger.info(f"User {voter_id} already voted '{vote_type}' for report {report_id}. No change.")
            return # Không làm gì thêm

        # --- Cập nhật lượt vote ---
        if vote_type == "up":
            current_report["votes_up"] += 1
            if previous_vote == "down": # Nếu trước đó đã vote 'down', thì hủy vote 'down' cũ
                current_report["votes_down"] = max(0, current_report["votes_down"] - 1)
        elif vote_type == "down":
            current_report["votes_down"] += 1
            if previous_vote == "up": # Nếu trước đó đã vote 'up', thì hủy vote 'up' cũ
                current_report["votes_up"] = max(0, current_report["votes_up"] - 1)
        
        # Lưu vote mới vào Redis
        redis_conn.set(vote_key, vote_type)

        # --- Tính toán lại điểm tin cậy ---
        credibility_result = self.credibility_calculator.calculate_credibility(
            user_id=current_report["user_id"],
            upvotes=current_report["votes_up"],
            downvotes=current_report["votes_down"],
            is_verified_by_news=False # Assume not verified by news in this flow
        )
        current_report["reliability_score"] = credibility_result['credibility_score']
        
        # --- Cập nhật trạng thái và uy tín người dùng ---
        old_status = current_report["status"]
        new_status = old_status

        # Logic cập nhật trạng thái
        if current_report["reliability_score"] >= Config.CREDIBILITY_THRESHOLD_HIGH and old_status == "pending_verification":
            new_status = "verified_community"
            logger.info(f"Report {report_id} status changed to 'verified_community' (score: {current_report['reliability_score']:.2f}).")
            self.reputation_manager.update_reputation(current_report["user_id"], is_correct=True)
        elif current_report["reliability_score"] < Config.CREDIBILITY_THRESHOLD_MEDIUM and old_status == "verified_community":
            new_status = "pending_verification" # Trở lại chờ xác thực
            logger.info(f"Report {report_id} status changed to 'pending_verification' (score: {current_report['reliability_score']:.2f}).")
            self.reputation_manager.update_reputation(current_report["user_id"], is_correct=False) # Giảm uy tín
        elif current_report["reliability_score"] < Config.CREDIBILITY_THRESHOLD_LOW_REMOVE and old_status not in ["unverified_low_score", "deleted"]:
            new_status = "unverified_low_score" # Đánh dấu là không xác thực, điểm thấp
            logger.info(f"Report {report_id} status changed to 'unverified_low_score' (score: {current_report['reliability_score']:.2f}).")
            self.reputation_manager.update_reputation(current_report["user_id"], is_correct=False) # Giảm uy tín

        current_report["status"] = new_status
        current_report["updated_at"] = datetime.now().isoformat()

        # --- Lưu lại các thay đổi vào Redis ---
        redis_conn.hset(f"report:{report_id}", mapping={
            "votes_up": str(current_report["votes_up"]), # Lưu dưới dạng string
            "votes_down": str(current_report["votes_down"]), # Lưu dưới dạng string
            "reliability_score": str(current_report["reliability_score"]), # Lưu dưới dạng string
            "status": current_report["status"],
            "updated_at": current_report["updated_at"]
        })
        logger.info(f"Report {report_id} vote update saved. Up={current_report['votes_up']}, Down={current_report['votes_down']}, Score={current_report['reliability_score']:.2f}, Status={current_report['status']}.")

        # Thông báo cho các client real-time (qua WebSocket) để cập nhật bản đồ
        # self._publish_report_update(current_report)


# Initialize service
community_report_service = CommunityReportService()

# --- Hàm khởi tạo các báo cáo mẫu cho demo ---
async def initialize_mock_reports():
    # Only initialize if reports don't exist in Redis to avoid overwriting
    if not redis_conn.keys("report:*"):
        logger.info("Initializing mock reports in Redis...")
        
        sample_report_id_1 = str(uuid.uuid4())
        await community_report_service.process_new_report({
            "user_id": "test_user_reporter_1",
            "description": "Có một vụ va chạm nhỏ ở cầu Chương Dương, gây ùn ứ vào khoảng 7h sáng.",
            "location_text": "cầu Chương Dương",
            "latitude": 21.033, "longitude": 105.877
        })
        
        sample_report_id_2 = str(uuid.uuid4())
        await community_report_service.process_new_report({
            "user_id": "test_user_reporter_2",
            "description": "Phát hiện một nhóm người khả nghi đang tụ tập ở công viên Thống Nhất vào buổi tối.",
            "location_text": "công viên Thống Nhất",
            "latitude": 21.008, "longitude": 105.842
        })
        logger.info("Mock reports initialized.")
    else:
        logger.info("Mock reports already exist in Redis. Skipping initialization.")