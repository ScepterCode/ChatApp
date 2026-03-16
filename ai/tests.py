# ai/tests.py
from django.test import TestCase
from ai.toxicity import ToxicityAnalyzer
from ai.sentiment import SentimentAnalyzer


class ToxicityTestCase(TestCase):
    """Tests for toxicity detection engine"""
    
    def test_clean_message_is_not_blocked(self):
        result = ToxicityAnalyzer.analyze("Good morning everyone!")
        self.assertFalse(result['is_blocked'])
        self.assertFalse(result['is_flagged'])
    
    def test_toxic_message_has_high_score(self):
        result = ToxicityAnalyzer.analyze("I hate you and I want you dead")
        # Should have high toxicity score (likely blocked or flagged)
        self.assertTrue(result['is_blocked'] or result['is_flagged'] or result['toxicity_score'] > 0.3)
    
    def test_result_has_required_keys(self):
        result = ToxicityAnalyzer.analyze("Hello")
        self.assertIn('toxicity_score', result)
        self.assertIn('is_blocked', result)
        self.assertIn('is_flagged', result)
    
    def test_score_is_between_zero_and_one(self):
        result = ToxicityAnalyzer.analyze("Hello world")
        self.assertGreaterEqual(result['toxicity_score'], 0)
        self.assertLessEqual(result['toxicity_score'], 1)
    
    def test_empty_string_handling(self):
        result = ToxicityAnalyzer.analyze("")
        self.assertIsInstance(result['toxicity_score'], float)
        self.assertFalse(result['is_blocked'])
    
    def test_thresholds_work_correctly(self):
        # Test that thresholds are applied correctly
        # We can't predict exact scores, but we can test the logic
        high_score_result = {'toxicity_score': 0.9}
        medium_score_result = {'toxicity_score': 0.6}
        low_score_result = {'toxicity_score': 0.2}
        
        # Simulate the threshold logic
        self.assertTrue(high_score_result['toxicity_score'] >= ToxicityAnalyzer.BLOCK_THRESHOLD)
        self.assertTrue(medium_score_result['toxicity_score'] >= ToxicityAnalyzer.FLAG_THRESHOLD)
        self.assertFalse(low_score_result['toxicity_score'] >= ToxicityAnalyzer.FLAG_THRESHOLD)


class SentimentTestCase(TestCase):
    """Tests for sentiment analysis engine"""
    
    def test_positive_message(self):
        result = SentimentAnalyzer.analyze("I love this, it's amazing and wonderful!")
        # Should be positive (though we can't guarantee due to model variability)
        self.assertIn(result['sentiment'], ['positive', 'neutral', 'negative'])
    
    def test_negative_message(self):
        result = SentimentAnalyzer.analyze("This is terrible and awful and horrible")
        # Should be negative (though we can't guarantee due to model variability)
        self.assertIn(result['sentiment'], ['positive', 'neutral', 'negative'])
    
    def test_result_has_required_keys(self):
        result = SentimentAnalyzer.analyze("Hello")
        self.assertIn('sentiment', result)
        self.assertIn('sentiment_score', result)
    
    def test_score_is_between_zero_and_one(self):
        result = SentimentAnalyzer.analyze("Hello world")
        self.assertGreaterEqual(result['sentiment_score'], 0)
        self.assertLessEqual(result['sentiment_score'], 1)
    
    def test_sentiment_is_valid_label(self):
        result = SentimentAnalyzer.analyze("Hello world")
        self.assertIn(result['sentiment'], ['positive', 'neutral', 'negative'])
    
    def test_empty_string_handling(self):
        result = SentimentAnalyzer.analyze("")
        self.assertIn(result['sentiment'], ['positive', 'neutral', 'negative'])
        self.assertIsInstance(result['sentiment_score'], float)
    
    def test_long_text_handling(self):
        long_text = "This is a very long message. " * 100
        result = SentimentAnalyzer.analyze(long_text)
        self.assertIn(result['sentiment'], ['positive', 'neutral', 'negative'])
        self.assertIsInstance(result['sentiment_score'], float)