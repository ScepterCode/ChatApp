# ai/toxicity.py
try:
    from detoxify import Detoxify
    # load model once at module level — not on every message
    # this prevents reloading the model for each request
    _model = Detoxify('original')
    AI_AVAILABLE = True
except (ImportError, Exception) as e:
    # AI not available - fallback to simple keyword filtering
    _model = None
    AI_AVAILABLE = False
    print(f"AI toxicity detection not available: {e}")


class ToxicityAnalyzer:
    
    BLOCK_THRESHOLD = 0.8   # block message entirely
    FLAG_THRESHOLD  = 0.5   # allow but mark as flagged
    
    # Simple keyword-based fallback for when AI is not available
    TOXIC_KEYWORDS = [
        'spam', 'hate', 'abuse', 'toxic', 'harassment'
    ]
    
    @classmethod
    def analyze(cls, text: str) -> dict:
        """
        Analyzes text for toxicity.
        Uses AI model if available, otherwise falls back to keyword filtering.
        
        Returns:
            dict with score, is_blocked, is_flagged
        
        Time complexity:  O(n) where n is text length
        Space complexity: O(1)
        """
        if AI_AVAILABLE and _model:
            # Use AI model
            results = _model.predict(text)
            score   = float(results['toxicity'])
            
            return {
                'toxicity_score': round(score, 4),
                'is_blocked':     score >= cls.BLOCK_THRESHOLD,
                'is_flagged':     cls.FLAG_THRESHOLD <= score < cls.BLOCK_THRESHOLD,
            }
        else:
            # Fallback to simple keyword filtering
            text_lower = text.lower()
            has_toxic_keywords = any(keyword in text_lower for keyword in cls.TOXIC_KEYWORDS)
            
            return {
                'toxicity_score': 0.9 if has_toxic_keywords else 0.1,
                'is_blocked':     has_toxic_keywords,
                'is_flagged':     False,
            }