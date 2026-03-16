# ai/toxicity.py
from detoxify import Detoxify

# load model once at module level — not on every message
# this prevents reloading the model for each request
_model = Detoxify('original')


class ToxicityAnalyzer:
    
    BLOCK_THRESHOLD = 0.8   # block message entirely
    FLAG_THRESHOLD  = 0.5   # allow but mark as flagged
    
    @classmethod
    def analyze(cls, text: str) -> dict:
        """
        Analyzes text for toxicity.
        
        Returns:
            dict with score, is_blocked, is_flagged
        
        Time complexity:  O(n) where n is text length
        Space complexity: O(1)
        """
        results = _model.predict(text)
        score   = float(results['toxicity'])
        
        return {
            'toxicity_score': round(score, 4),
            'is_blocked':     score >= cls.BLOCK_THRESHOLD,
            'is_flagged':     cls.FLAG_THRESHOLD <= score < cls.BLOCK_THRESHOLD,
        }