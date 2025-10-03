import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB = int(os.getenv("REDIS_DB", 0))

    # --- Configs tối thiểu cho Filtering ---
    SPAM_KEYWORDS = [
        r'mua\s*ngay', r'giảm\s*giá', r'khuyến\s*mãi', r'liên\s*hệ', r'09\d{8}' # Thêm mẫu số điện thoại đơn giản
    ]
    OFFENSIVE_KEYWORDS = [r'đ[mđ]', r'c[cặ]c', r'l[oồ]n']
    PHONE_PATTERN = r'(?:0|\+84)(?:[\s\-\.]?\d{2,3}[\s\-\.]?\d{3}[\s\-\.]?\d{3,4}|\d{9,10})'
    URL_PATTERN = r'https?://[^\s]+|www\.[^\s]+'
    MAX_ALLOWED_LINKS = 2
    MIN_LENGTH_FOR_UPPER_CHECK = 20
    MAX_UPPERCASE_RATIO = 0.5
    MIN_LENGTH_FOR_LANG_DETECT = 10 

    MIN_REPORT_LENGTH = 20
    MAX_REPORT_LENGTH = 2000
    MIN_WORDS_FOR_REPORT = 5

    DATE_PATTERNS = [r'hôm\s*(?:nay|qua)']
    TIME_PATTERNS = [r'\d{1,2}(?::|h)']
    LOCATION_PATTERNS = [r'ngã\s*tư\s*\S+', r'quận\s*\S+'] # Rất đơn giản hóa

    # --- Configs tối thiểu cho Credibility ---
    REPUTATION_WEIGHT_W1 = 0.4
    AGREE_VOTE_WEIGHT_W2 = 0.4
    DISAGREE_VOTE_WEIGHT_W3 = -0.2
    MIN_VOTES_THRESHOLD = 3
    SIGMOID_K = 0.1 
    
    CREDIBILITY_THRESHOLD_HIGH = 0.9 
    CREDIBILITY_THRESHOLD_MEDIUM = 0.7 

    CREDIBILITY_THRESHOLD_LOW_REMOVE = 0.3 
    DAYS_THRESHOLD_LOW_REMOVE = 7 
    CREDIBILITY_THRESHOLD_MEDIUM_REMOVE = 0.5 
    DAYS_THRESHOLD_MEDIUM_REMOVE = 14 

    # --- Configs tối thiểu cho Rewards ---
    HIGH_CREDIBILITY_THRESHOLD = 0.9
    MIN_POSTS_FOR_REWARD = 10
    MIN_TOTAL_UPVOTES = 50
    REWARD_PER_HIGH_CREDIBILITY_POST = 1000

    LOW_CREDIBILITY_THRESHOLD_PENALTY = 0.3
    BAN_LEVEL_1_THRESHOLD = 3 
    BAN_LEVEL_2_THRESHOLD = 5
    BAN_LEVEL_3_THRESHOLD = 10

    FAKE_SOS_BAN_DURATION = {1: 90, 2: 180, 3: -1}

    # --- Configs tối thiểu cho NLP (mock) ---
    PHOBERT_MODEL_PATH = "mock_path/phobert_base" # Chỉ là đường dẫn giả
    SPAM_CLASSIFIER_PATH = "mock_path/spam_classifier.pkl"
    TOPIC_CLASSIFIER_PATH = "mock_path/topic_classifier.pkl"
    
    # --- Configs tối thiểu cho Rate Limiting ---
    RATE_LIMIT_REPORTS_PER_MINUTE = 5

    # --- Configs tối thiểu cho Report Expiration ---
    REPORT_EXPIRE_SECONDS_FOR_UNVERIFIED = 7 * 24 * 3600 # 7 days

    # --- Configs tối thiểu cho Duplicate Checking ---
    COSINE_SIMILARITY_THRESHOLD_DUPLICATE = 0.85
    COSINE_SIMILARITY_THRESHOLD_REFERENCE = 0.70