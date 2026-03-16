# ai/sentiment.py
from transformers import pipeline

# load model once at module level
_pipeline = pipeline(
    'sentiment-analysis',
    model='cardiffnlp/twitter-roberta-base-sentiment-latest',
    truncation=True,
    max_length=512,
)

# map model labels to clean labels
LABEL_MAP = {
    'positive': 'positive',
    'neutral':  'neutral',
    'negative': 'negative',
}


class SentimentAnalyzer:
    
    @classmethod
    def analyze(cls, text: str) -> dict:
        """
        Analyzes sentiment of text.
        
        Returns:
            dict with sentiment label and confidence score
        
        Time complexity:  O(n) where n is text length
        Space complexity: O(1)
        """
        result    = _pipeline(text)[0]
        label     = LABEL_MAP.get(result['label'].lower(), 'neutral')
        score     = float(result['score'])
        
        return {
            'sentiment':       label,
            'sentiment_score': round(score, 4),
        }