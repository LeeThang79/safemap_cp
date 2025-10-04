import logging
from services.community_processing.types import CommunityReport, ValidationResult
from services.community_processing.filtering import SpamDetector, ContentValidator, LanguageDetector

logger = logging.getLogger(__name__)

class CommunityReportProcessor:
    """Chỉ kiểm tra ngôn ngữ, độ dài, spam cho báo cáo cộng đồng"""
    def __init__(self):
        self.spam_detector = SpamDetector()
        self.content_validator = ContentValidator()
        self.language_detector = LanguageDetector()

    def process_report(self, report: CommunityReport) -> ValidationResult:
        content = report.content.strip()

        # 1. Kiểm tra ngôn ngữ
        is_vietnamese, reason = self.language_detector.is_vietnamese(content)
        if not is_vietnamese:
            logger.warning(f"Report {report.user_id}: Ngôn ngữ không hợp lệ - {reason}")
            return ValidationResult(is_valid=False, reason=f"Ngôn ngữ không hợp lệ: {reason}")

        # 2. Kiểm tra độ dài
        is_valid_length, reason = self.content_validator.check_content_length(content)
        if not is_valid_length:
            logger.warning(f"Report {report.user_id}: Độ dài không hợp lệ - {reason}")
            return ValidationResult(is_valid=False, reason=reason)

        # 3. Kiểm tra spam
        is_spam, reason = self.spam_detector.check_spam(content)
        if is_spam:
            logger.warning(f"Report {report.user_id}: Spam - {reason}")
            return ValidationResult(is_valid=False, reason=f"Spam: {reason}")

        # Nếu pass tất cả các bước
        logger.info(f"Report {report.user_id}: Hợp lệ")
        return ValidationResult(
            is_valid=True,
            reason="Báo cáo hợp lệ",
            filtered_content=content,
            extracted_info=None
        )
