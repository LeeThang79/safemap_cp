from datetime import datetime
from typing import Dict, Optional
from dataclasses import dataclass

@dataclass
class CommunityReport:
    """Cấu trúc dữ liệu báo cáo từ cộng đồng"""
    user_id: str
    content: str
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timestamp: Optional[datetime] = None

@dataclass
class ValidationResult:
    """Kết quả kiểm tra báo cáo"""
    is_valid: bool
    reason: str
    filtered_content: Optional[str] = None
    extracted_info: Optional[Dict] = None
