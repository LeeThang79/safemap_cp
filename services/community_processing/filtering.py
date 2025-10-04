# filtering.py - Lọc báo cáo cộng đồng

# Mock class: kiểm tra spam (giả lập)
class SpamDetector:
    def __init__(self):
        # Danh sách từ khóa spam bán hàng và từ ngữ tục tĩu (có thể mở rộng)
        self.spam_keywords = [
            'spam', 'bán hàng', 'khuyến mãi', 'mua ngay', 'giảm giá', 'tặng quà', 'liên hệ', 'inbox', 'số điện thoại', 'zalo', 'facebook'
        ]
        self.badwords = [
            'địt', 'cặc', 'lồn', 'đéo', 'mẹ mày', 'vcl', 'dm', 'cc', 'shit', 'fuck', 'bitch', 'ngu', 'chó', 'đụ', 'phò', 'dâm', 'dốt', 'khốn nạn', 'con mẹ', 'con chó', 'cút', 'đồ ngu', 'đồ chó', 'đồ khốn', 'đồ rác', 'rác rưởi', 'bố láo', 'bố đời', 'bố mày', 'mẹ kiếp', 'vãi lồn', 'vãi cặc', 'vãi đái', 'vãi cả lồn', 'vãi cả cặc', 'vãi cả đái'
        ]

    def check_spam(self, content):
        content_lower = content.lower()
        # Kiểm tra spam bán hàng
        for kw in self.spam_keywords:
            if kw in content_lower:
                return True, f'Nội dung chứa spam/bán hàng: "{kw}"'
        # Kiểm tra từ ngữ tục tĩu/chửi bậy
        for bad in self.badwords:
            if bad in content_lower:
                return True, f'Nội dung chứa từ ngữ tục tĩu/chửi bậy: "{bad}"'
        return False, ''

# Mock class: kiểm tra độ dài nội dung
class ContentValidator:
    def check_content_length(self, content, min_length=10):
        if len(content) < min_length:
            return False, f'Nội dung quá ngắn (<{min_length} ký tự)'
        return True, ''

# Mock class: kiểm tra ngôn ngữ (giả lập)
class LanguageDetector:
    def is_vietnamese(self, content):
        # Giả lập: nếu có ký tự tiếng Việt phổ biến thì coi là tiếng Việt
        for char in 'ăâêôơưđ':
            if char in content.lower():
                return True, ''
        return False, 'Không phát hiện tiếng Việt'

def filter_reports(reports, min_length=10):
    return [r for r in reports if len(r.content) >= min_length]
