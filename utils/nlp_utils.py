import torch
# from transformers import AutoModel, AutoTokenizer # Không dùng nếu không có file model
# from underthesea import word_tokenize # Không dùng nếu không có thư viện
import numpy as np
import os
import joblib # Dùng để mock việc tải model
from config import Config
import re # Cho clean_text mock

class NLPProcessor:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(NLPProcessor, cls).__new__(cls)
            cls._instance._load_models()
        return cls._instance

    def _load_models(self):
        # Đây là MOCK để tránh lỗi import Transformer khi không có thư viện/model
        print("DEBUG: Loading Mock NLP models. Real models not loaded.")
        class MockTokenizer:
            def __call__(self, text, return_tensors, padding, truncation, max_length):
                # Mock tokenization
                return {"input_ids": torch.tensor([[0, 1, 2, 3]])} # Dummy tensor
        self.tokenizer = MockTokenizer()
        
        class MockPhoBERTModel:
            def __init__(self):
                self.config = type('obj', (object,), {'hidden_size': 768})() # Mock config
            def __call__(self, input_ids):
                # Mock output
                return type('obj', (object,), {'last_hidden_state': torch.rand(1, 4, 768)})()
        self.phobert_model = MockPhoBERTModel()
        self.device = "cpu"

        # Load custom classification heads (these need to be trained and saved separately)
        self.spam_classifier = self._load_mock_classifier(Config.SPAM_CLASSIFIER_PATH, "spam_classifier")
        self.topic_classifier = self._load_mock_classifier(Config.TOPIC_CLASSIFIER_PATH, "topic_classifier")

    def _load_mock_classifier(self, path, model_name):
        # This is a placeholder. In reality, you'd load a pre-trained PyTorch model
        # or a scikit-learn model using joblib.load(path)
        class MockClassifier:
            def predict(self, embeddings):
                if model_name == "spam_classifier":
                    return np.random.choice(["spam", "not_spam"], len(embeddings))
                else: # topic_classifier
                    return np.random.choice([["giao_thong"], ["chay_no"], ["toi_pham"]], len(embeddings)), \
                           np.random.choice([["nguy_hiem"], ["trung_binh"]], len(embeddings))

            def predict_proba(self, embeddings):
                if model_name == "spam_classifier":
                    return np.random.rand(len(embeddings), 2)
                else: # topic_classifier (mock for 2 predictions)
                    return np.random.rand(len(embeddings), 5), np.random.rand(len(embeddings), 4) # 5 topics, 4 urgencies

        return MockClassifier()

    def clean_text(self, text: str) -> str:
        # Basic cleaning: lowercase, remove extra spaces, etc.
        text = re.sub(r"http\S+|www\S+|https\S+", "", text, flags=re.MULTILINE)
        text = re.sub(r'<.*?>', '', text) 
        text = re.sub(r'[^a-zA-ZÀ-ỹ0-9\s.,?!]', '', text) 
        text = text.lower().strip()
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def tokenize_vietnamese(self, text: str) -> str:
        # Mock tokenization for demo
        return " ".join(text.split())

    def get_embedding(self, text: str) -> np.ndarray:
        if not text.strip():
            return np.zeros(self.phobert_model.config.hidden_size)

        cleaned_text = self.tokenize_vietnamese(self.clean_text(text))
        # Mock embedding
        return np.random.rand(self.phobert_model.config.hidden_size)

    def classify_spam(self, embedding: np.ndarray) -> str:
        if embedding.ndim == 1:
            embedding = embedding.reshape(1, -1)
        prediction = self.spam_classifier.predict(embedding)[0]
        return prediction

    def classify_topic_and_urgency(self, embedding: np.ndarray) -> tuple[str, str]:
        if embedding.ndim == 1:
            embedding = embedding.reshape(1, -1)
        topic, urgency = self.topic_classifier.predict(embedding)
        return topic[0], urgency[0]

    def calculate_cosine_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        # Mock similarity
        return np.random.rand() # Return a random float for similarity for demo purposes

# Initialize NLP processor as a singleton
nlp_processor = NLPProcessor()
