# ai/sentiment.py
try:
    from transformers import pipeline
    # load model once at module level
    _pipeline = pipeline(
        'sentiment-analysis',
        model='cardiffnlp/twitter-roberta-base-sentiment-latest',
        truncation=True,
        max_length=512,
    )
    AI_AVAILABLE = True
except (ImportError, Exception) as e:
    # AI not available - fallback to simple sentiment analysis
    _pipeline = None
    AI_AVAILABLE = False
    print(f"AI sentiment analysis not available: {e}")

# map model labels to clean labels
LABEL_MAP = {
    'positive': 'positive',
    'neutral':  'neutral',
    'negative': 'negative',
}


class SentimentAnalyzer:
    
    # Simple keyword-based fallback
    POSITIVE_KEYWORDS = ['good', 'great', 'awesome', 'love', 'excellent', 'amazing', 'happy', 'wonderful']
    NEGATIVE_KEYWORDS = ['bad', 'terrible', 'hate', 'awful', 'horrible', 'sad', 'angry', 'disappointed']
    
    @classmethod
    def analyze(cls, text: str) -> dict:
        """
        Analyzes sentiment of text.
        Uses AI model if available, otherwise falls back to keyword analysis.
        
        Returns:
            dict with sentiment label and confidence score
        
        Time complexity:  O(n) where n is text length
        Space complexity: O(1)
        """
        if AI_AVAILABLE and _pipeline:
            # Use AI model
            result    = _pipeline(text)[0]
            label     = LABEL_MAP.get(result['label'].lower(), 'neutral')
            score     = float(result['score'])
            
            return {
                'sentiment':       label,
                'sentiment_score': round(score, 4),
            }
        else:
            # Fallback to simple keyword analysis
            text_lower = text.lower()
            positive_count = sum(1 for word in cls.POSITIVE_KEYWORDS if word in text_lower)
            negative_count = sum(1 for word in cls.NEGATIVE_KEYWORDS if word in text_lower)
            
            if positive_count > negative_count:
                sentiment = 'positive'
                score = 0.7
            elif negative_count > positive_count:
                sentiment = 'negative'
                score = 0.7
            else:
                sentiment = 'neutral'
                score = 0.6
                
            return {
                'sentiment':       sentiment,
                'sentiment_score': score,
            }