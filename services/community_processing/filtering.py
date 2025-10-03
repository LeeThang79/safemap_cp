# filtering.py - Lọc báo cáo cộng đồng
def filter_reports(reports, min_length=10):
    return [r for r in reports if len(r.content) >= min_length]
