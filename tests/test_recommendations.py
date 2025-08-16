"""Unit tests for recommendation engine operations."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from lotto_max_analyzer.analysis.recommendations import RecommendationEngine
from lotto_max_analyzer.data.models import DrawResult, Recommendation


class TestRecommendationEngine:
    """Test cases for RecommendationEngine class."""
    
    @pytest.fixture
    def engine(self):
        """Create a RecommendationEngine instance for testing."""
        return RecommendationEngine()
    
    @pytest.fixture
    def sample_draws(self):
        """Create sample draw results for testing."""
        draws = []
        base_date = datetime(2024, 1, 1)
        
        # Create 60 draws with predictable patterns
        for i in range(60):
            if i < 20:
                # First 20 draws: numbers 1-7 appear frequently (hot numbers)
                numbers = [1, 2, 3, 4, 5, 6, 7]
            elif i < 40:
                # Next 20 draws: numbers 8-14 appear frequently
                numbers = [8, 9, 10, 11, 12, 13, 14]
            else:
                # Last 20 draws: numbers 15-21 appear frequently
                numbers = [15, 16, 17, 18, 19, 20, 21]
            
            draw = DrawResult(
                date=base_date + timedelta(days=i * 3),
                numbers=numbers,
                bonus=25,
                jackpot_amount=50000000.0,
                draw_id=f"2024-{i:03d}"
            )
            draws.append(draw)
        
        return draws
    
    @pytest.fixture
    def minimal_draws(self):
        """Create minimal set of draws for testing edge cases."""
        return [
            DrawResult(
                date=datetime(2024, 1, 1),
                numbers=[1, 2, 3, 4, 5, 6, 7],
                bonus=8,
                jackpot_amount=50000000.0,
                draw_id="2024-001"
            ),
            DrawResult(
                date=datetime(2024, 1, 4),
                numbers=[8, 9, 10, 11, 12, 13, 14],
                bonus=15,
                jackpot_amount=55000000.0,
                draw_id="2024-002"
            )
        ]
    
    def test_engine_initialization(self, engine):
        """Test that engine initializes properly."""
        assert engine.logger is not None
        assert engine.frequency_analyzer is not None
        assert engine.pattern_analyzer is not None
    
    def test_generate_hot_number_picks(self, engine, sample_draws):
        """Test hot number recommendation generation."""
        recommendations = engine.generate_hot_number_picks(sample_draws)
        
        # Should return exactly 7 numbers
        assert len(recommendations) == 7
        
        # All numbers should be unique
        assert len(set(recommendations)) == 7
        
        # All numbers should be in valid range
        assert all(1 <= num <= 50 for num in recommendations)
        
        # Should be sorted
        assert recommendations == sorted(recommendations)
        
        # Should include some of the most frequent numbers (1-21 from our test data)
        frequent_numbers = set(range(1, 22))
        recommended_set = set(recommendations)
        overlap = len(frequent_numbers.intersection(recommended_set))
        assert overlap >= 5  # At least 5 should be from frequent numbers
    
    def test_generate_hot_number_picks_invalid_count(self, engine, sample_draws):
        """Test that invalid count raises ValueError."""
        with pytest.raises(ValueError, match="Must generate exactly 7 numbers"):
            engine.generate_hot_number_picks(sample_draws, count=5)
    
    def test_generate_cold_number_picks(self, engine, sample_draws):
        """Test cold number recommendation generation."""
        recommendations = engine.generate_cold_number_picks(sample_draws)
        
        # Should return exactly 7 numbers
        assert len(recommendations) == 7
        
        # All numbers should be unique
        assert len(set(recommendations)) == 7
        
        # All numbers should be in valid range
        assert all(1 <= num <= 50 for num in recommendations)
        
        # Should be sorted
        assert recommendations == sorted(recommendations)
        
        # Should include some numbers that don't appear frequently (22-50 from our test data)
        infrequent_numbers = set(range(22, 51))
        recommended_set = set(recommendations)
        overlap = len(infrequent_numbers.intersection(recommended_set))
        assert overlap >= 5  # At least 5 should be from infrequent numbers
    
    def test_generate_cold_number_picks_invalid_count(self, engine, sample_draws):
        """Test that invalid count raises ValueError."""
        with pytest.raises(ValueError, match="Must generate exactly 7 numbers"):
            engine.generate_cold_number_picks(sample_draws, count=10)
    
    def test_generate_balanced_picks(self, engine, sample_draws):
        """Test balanced recommendation generation."""
        recommendations = engine.generate_balanced_picks(sample_draws)
        
        # Should return exactly 7 numbers
        assert len(recommendations) == 7
        
        # All numbers should be unique
        assert len(set(recommendations)) == 7
        
        # All numbers should be in valid range
        assert all(1 <= num <= 50 for num in recommendations)
        
        # Should be sorted
        assert recommendations == sorted(recommendations)
        
        # Should have reasonable odd/even balance (not all odd or all even)
        odd_count = sum(1 for n in recommendations if n % 2 == 1)
        assert 2 <= odd_count <= 5  # Reasonable balance
    
    def test_generate_balanced_picks_invalid_count(self, engine, sample_draws):
        """Test that invalid count raises ValueError."""
        with pytest.raises(ValueError, match="Must generate exactly 7 numbers"):
            engine.generate_balanced_picks(sample_draws, count=3)
    
    def test_create_full_combination_hot_strategy(self, engine, sample_draws):
        """Test full combination creation with hot strategy."""
        combination = engine.create_full_combination(sample_draws, 'hot_numbers')
        
        assert len(combination) == 7
        assert len(set(combination)) == 7
        assert all(1 <= num <= 50 for num in combination)
        assert combination == sorted(combination)
    
    def test_create_full_combination_cold_strategy(self, engine, sample_draws):
        """Test full combination creation with cold strategy."""
        combination = engine.create_full_combination(sample_draws, 'cold_numbers')
        
        assert len(combination) == 7
        assert len(set(combination)) == 7
        assert all(1 <= num <= 50 for num in combination)
        assert combination == sorted(combination)
    
    def test_create_full_combination_balanced_strategy(self, engine, sample_draws):
        """Test full combination creation with balanced strategy."""
        combination = engine.create_full_combination(sample_draws, 'balanced')
        
        assert len(combination) == 7
        assert len(set(combination)) == 7
        assert all(1 <= num <= 50 for num in combination)
        assert combination == sorted(combination)
    
    def test_create_full_combination_invalid_strategy(self, engine, sample_draws):
        """Test that invalid strategy raises ValueError."""
        with pytest.raises(ValueError, match="Strategy must be one of"):
            engine.create_full_combination(sample_draws, 'invalid_strategy')
    
    def test_create_full_combination_insufficient_data(self, engine, minimal_draws):
        """Test that insufficient data raises ValueError."""
        with pytest.raises(ValueError, match="Need at least 50 draws"):
            engine.create_full_combination(minimal_draws, 'hot_numbers')
    
    def test_generate_recommendation_with_rationale(self, engine, sample_draws):
        """Test recommendation generation with rationale."""
        recommendation = engine.generate_recommendation_with_rationale(sample_draws, 'balanced')
        
        # Check that it's a proper Recommendation object
        assert isinstance(recommendation, Recommendation)
        assert recommendation.strategy == 'balanced'
        assert len(recommendation.numbers) == 7
        assert len(set(recommendation.numbers)) == 7
        assert 0 <= recommendation.confidence <= 1
        assert len(recommendation.rationale) > 0
        assert isinstance(recommendation.rationale, str)
    
    def test_get_multiple_recommendations_default_strategies(self, engine, sample_draws):
        """Test generating multiple recommendations with default strategies."""
        recommendations = engine.get_multiple_recommendations(sample_draws)
        
        # Should have all three default strategies
        expected_strategies = ['hot_numbers', 'cold_numbers', 'balanced']
        assert set(recommendations.keys()) == set(expected_strategies)
        
        # Each should be a valid Recommendation object
        for strategy, rec in recommendations.items():
            assert isinstance(rec, Recommendation)
            assert rec.strategy == strategy
            assert len(rec.numbers) == 7
            assert len(set(rec.numbers)) == 7
    
    def test_get_multiple_recommendations_custom_strategies(self, engine, sample_draws):
        """Test generating multiple recommendations with custom strategies."""
        custom_strategies = ['hot_numbers', 'balanced']
        recommendations = engine.get_multiple_recommendations(sample_draws, custom_strategies)
        
        # Should have only the requested strategies
        assert set(recommendations.keys()) == set(custom_strategies)
        
        # Each should be a valid Recommendation object
        for strategy, rec in recommendations.items():
            assert isinstance(rec, Recommendation)
            assert rec.strategy == strategy
    
    def test_calculate_confidence(self, engine, sample_draws):
        """Test confidence calculation."""
        numbers = [1, 2, 3, 4, 5, 6, 7]
        
        # Test different strategies
        hot_confidence = engine._calculate_confidence(sample_draws, numbers, 'hot_numbers')
        cold_confidence = engine._calculate_confidence(sample_draws, numbers, 'cold_numbers')
        balanced_confidence = engine._calculate_confidence(sample_draws, numbers, 'balanced')
        
        # All should be in valid range
        assert 0.1 <= hot_confidence <= 1.0
        assert 0.1 <= cold_confidence <= 1.0
        assert 0.1 <= balanced_confidence <= 1.0
        
        # Balanced should typically have highest confidence
        assert balanced_confidence >= cold_confidence
    
    def test_generate_rationale(self, engine, sample_draws):
        """Test rationale generation."""
        numbers = [1, 2, 3, 4, 5, 6, 7]
        
        # Test different strategies
        hot_rationale = engine._generate_rationale(sample_draws, numbers, 'hot_numbers')
        cold_rationale = engine._generate_rationale(sample_draws, numbers, 'cold_numbers')
        balanced_rationale = engine._generate_rationale(sample_draws, numbers, 'balanced')
        
        # All should be non-empty strings
        assert isinstance(hot_rationale, str)
        assert isinstance(cold_rationale, str)
        assert isinstance(balanced_rationale, str)
        assert len(hot_rationale) > 0
        assert len(cold_rationale) > 0
        assert len(balanced_rationale) > 0
        
        # Should contain strategy-specific keywords
        assert 'hot number' in hot_rationale.lower()
        assert 'cold number' in cold_rationale.lower()
        assert 'balanced' in balanced_rationale.lower()
    
    def test_add_balanced_numbers(self, engine):
        """Test the balanced number addition helper method."""
        recommendations = [1, 2, 3]  # 2 odd, 1 even
        available_odd = [5, 7, 9, 11, 13]
        available_even = [4, 6, 8, 10, 12]
        frequency = {n: 10 for n in range(1, 51)}  # All equal frequency
        range_counts = {}
        
        # Need 1 more odd, 2 more even to reach 7 total with 3-4 split
        engine._add_balanced_numbers(
            recommendations, available_odd, available_even,
            needed_odd=1, needed_even=3, remaining_slots=4,
            frequency=frequency, range_counts=range_counts
        )
        
        # Should have 7 numbers total
        assert len(recommendations) == 7
        
        # Should have reasonable odd/even balance
        odd_count = sum(1 for n in recommendations if n % 2 == 1)
        assert 2 <= odd_count <= 5
    
    def test_recommendation_uniqueness(self, engine, sample_draws):
        """Test that different strategies produce different recommendations."""
        hot_rec = engine.generate_hot_number_picks(sample_draws)
        cold_rec = engine.generate_cold_number_picks(sample_draws)
        balanced_rec = engine.generate_balanced_picks(sample_draws)
        
        # Different strategies should generally produce different results
        # (Though there might be some overlap, they shouldn't be identical)
        assert hot_rec != cold_rec or hot_rec != balanced_rec or cold_rec != balanced_rec
    
    def test_recommendation_consistency(self, engine, sample_draws):
        """Test that recommendations are consistent for the same input."""
        # Generate recommendations multiple times with same data
        rec1 = engine.generate_balanced_picks(sample_draws)
        rec2 = engine.generate_balanced_picks(sample_draws)
        
        # Should be identical (assuming no randomness in balanced strategy)
        # Note: If randomness is added later, this test might need adjustment
        assert rec1 == rec2
    
    @patch('random.sample')
    def test_recommendation_fallback_with_insufficient_numbers(self, mock_sample, engine):
        """Test fallback behavior when not enough numbers are available."""
        # Mock random.sample to return predictable results
        mock_sample.return_value = [30, 31, 32]
        
        # Create draws with very limited number variety
        limited_draws = []
        for i in range(60):
            draw = DrawResult(
                date=datetime(2024, 1, 1) + timedelta(days=i),
                numbers=[1, 2, 3, 4, 5, 6, 7],  # Same numbers every time
                bonus=8,
                jackpot_amount=50000000.0,
                draw_id=f"2024-{i:03d}"
            )
            limited_draws.append(draw)
        
        # Should still generate valid recommendations
        recommendations = engine.generate_hot_number_picks(limited_draws)
        assert len(recommendations) == 7
        assert len(set(recommendations)) == 7


if __name__ == "__main__":
    pytest.main([__file__])