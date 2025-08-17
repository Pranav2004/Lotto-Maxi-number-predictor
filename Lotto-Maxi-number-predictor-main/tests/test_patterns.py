"""Unit tests for pattern detection operations."""

import pytest
from datetime import datetime, timedelta
from collections import Counter

from lotto_max_analyzer.analysis.patterns import PatternAnalyzer
from lotto_max_analyzer.data.models import DrawResult, Pattern


class TestPatternAnalyzer:
    """Test cases for PatternAnalyzer class."""
    
    @pytest.fixture
    def analyzer(self):
        """Create a PatternAnalyzer instance for testing."""
        return PatternAnalyzer()
    
    @pytest.fixture
    def consecutive_draws(self):
        """Create draws with consecutive number patterns."""
        draws = []
        base_date = datetime(2024, 1, 1)
        
        # Create 60 draws with various consecutive patterns
        patterns = [
            [1, 2, 3, 15, 25, 35, 45],      # 3 consecutive at start
            [5, 12, 13, 14, 15, 30, 40],   # 4 consecutive in middle
            [10, 20, 30, 40, 47, 48, 49],  # 3 consecutive at end
            [1, 8, 15, 22, 29, 36, 43],    # No consecutive
            [2, 3, 10, 20, 30, 40, 50],    # 2 consecutive at start
        ]
        
        # Repeat patterns to get enough draws
        for i in range(60):
            pattern = patterns[i % len(patterns)]
            draw = DrawResult(
                date=base_date + timedelta(days=i * 3),
                numbers=pattern,
                bonus=25,
                jackpot_amount=50000000.0,
                draw_id=f"2024-{i:03d}"
            )
            draws.append(draw)
        
        return draws
    
    @pytest.fixture
    def odd_even_draws(self):
        """Create draws with specific odd/even patterns."""
        draws = []
        base_date = datetime(2024, 1, 1)
        
        # Create patterns with different odd/even distributions
        patterns = [
            [1, 3, 5, 7, 9, 11, 13],       # All odd (7-0)
            [2, 4, 6, 8, 10, 12, 14],      # All even (0-7)
            [1, 2, 5, 6, 9, 10, 13],       # Balanced (4-3)
            [1, 3, 5, 8, 10, 12, 14],      # Mixed (3-4)
            [2, 4, 7, 9, 11, 13, 15],      # Mixed (5-2)
        ]
        
        # Repeat patterns to get enough draws
        for i in range(60):
            pattern = patterns[i % len(patterns)]
            draw = DrawResult(
                date=base_date + timedelta(days=i * 3),
                numbers=pattern,
                bonus=25,
                jackpot_amount=50000000.0,
                draw_id=f"2024-{i:03d}"
            )
            draws.append(draw)
        
        return draws
    
    @pytest.fixture
    def range_draws(self):
        """Create draws with specific range distributions."""
        draws = []
        base_date = datetime(2024, 1, 1)
        
        # Create patterns focusing on different ranges
        patterns = [
            [1, 2, 3, 4, 5, 6, 7],         # All low range
            [41, 42, 43, 44, 45, 46, 47],  # All high range
            [1, 11, 21, 31, 41, 45, 49],   # Spread across ranges
            [5, 15, 25, 35, 40, 45, 50],   # Mixed ranges
            [8, 9, 18, 19, 28, 29, 38],    # Pairs from different ranges
        ]
        
        # Repeat patterns to get enough draws
        for i in range(60):
            pattern = patterns[i % len(patterns)]
            draw = DrawResult(
                date=base_date + timedelta(days=i * 3),
                numbers=pattern,
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
    
    def test_analyzer_initialization(self, analyzer):
        """Test that analyzer initializes properly."""
        assert analyzer.logger is not None
    
    def test_detect_consecutive_patterns(self, analyzer, consecutive_draws):
        """Test consecutive pattern detection."""
        patterns = analyzer.detect_consecutive_patterns(consecutive_draws)
        
        # Should detect various consecutive patterns
        assert len(patterns) > 0
        
        # All patterns should be consecutive type
        for pattern in patterns:
            assert pattern.type == "consecutive"
            assert isinstance(pattern.frequency, int)
            assert 0 <= pattern.significance <= 1
            assert len(pattern.examples) > 0
    
    def test_consecutive_patterns_insufficient_data(self, analyzer, minimal_draws):
        """Test that insufficient data raises ValueError."""
        with pytest.raises(ValueError, match="Need at least .* draws for pattern analysis"):
            analyzer.detect_consecutive_patterns(minimal_draws)
    
    def test_find_consecutive_sequences(self, analyzer):
        """Test finding consecutive sequences in numbers."""
        # Test various number combinations
        test_cases = [
            ([1, 2, 3, 10, 20, 30, 40], {3: [[1, 2, 3]]}),
            ([5, 6, 15, 16, 17, 25, 35], {2: [[5, 6]], 3: [[15, 16, 17]]}),
            ([1, 3, 5, 7, 9, 11, 13], {}),  # No consecutive
            ([10, 11, 12, 13, 14, 20, 30], {5: [[10, 11, 12, 13, 14]]}),
        ]
        
        for numbers, expected in test_cases:
            result = analyzer._find_consecutive_sequences(numbers)
            assert result == expected
    
    def test_analyze_odd_even_distribution(self, analyzer, odd_even_draws):
        """Test odd/even distribution analysis."""
        analysis = analyzer.analyze_odd_even_distribution(odd_even_draws)
        
        # Check required keys
        required_keys = [
            'average_odd_count', 'average_even_count', 
            'odd_std_deviation', 'even_std_deviation',
            'most_common_pattern', 'pattern_distribution', 'pattern_percentages'
        ]
        for key in required_keys:
            assert key in analysis
        
        # Check data types and ranges
        assert 0 <= analysis['average_odd_count'] <= 7
        assert 0 <= analysis['average_even_count'] <= 7
        assert analysis['odd_std_deviation'] >= 0
        assert analysis['even_std_deviation'] >= 0
        
        # Check that percentages sum to 100%
        total_percentage = sum(analysis['pattern_percentages'].values())
        assert abs(total_percentage - 100.0) < 0.01  # Allow for floating point errors
    
    def test_analyze_odd_even_empty_draws(self, analyzer):
        """Test odd/even analysis with empty draws list."""
        analysis = analyzer.analyze_odd_even_distribution([])
        assert analysis == {}
    
    def test_analyze_range_distribution(self, analyzer, range_draws):
        """Test range distribution analysis."""
        analysis = analyzer.analyze_range_distribution(range_draws)
        
        # Check required keys
        required_keys = [
            'total_counts', 'percentages', 'average_per_draw', 
            'max_per_draw', 'range_balance_score'
        ]
        for key in required_keys:
            assert key in analysis
        
        # Check that all ranges are represented
        expected_ranges = ['low', 'mid_low', 'mid', 'mid_high', 'high']
        for range_name in expected_ranges:
            assert range_name in analysis['total_counts']
            assert range_name in analysis['percentages']
            assert range_name in analysis['average_per_draw']
            assert range_name in analysis['max_per_draw']
        
        # Check that percentages sum to approximately 100%
        total_percentage = sum(analysis['percentages'].values())
        assert abs(total_percentage - 100.0) < 1.0  # Allow some variance
        
        # Check balance score is in valid range
        assert 0 <= analysis['range_balance_score'] <= 100
    
    def test_analyze_range_distribution_empty_draws(self, analyzer):
        """Test range analysis with empty draws list."""
        analysis = analyzer.analyze_range_distribution([])
        assert analysis == {}
    
    def test_calculate_pattern_significance(self, analyzer):
        """Test pattern significance calculation."""
        # Test consecutive pattern
        consecutive_pattern = Pattern(
            type="consecutive",
            description="3 consecutive numbers",
            frequency=10,
            significance=0.0,  # Will be calculated
            examples=[[1, 2, 3]]
        )
        
        significance = analyzer.calculate_pattern_significance(consecutive_pattern)
        assert 0 <= significance <= 1
        
        # Test odd/even pattern
        odd_even_pattern = Pattern(
            type="odd_even",
            description="Odd/even distribution",
            frequency=4,  # 4 odd numbers
            significance=0.0,
            examples=[]
        )
        
        significance = analyzer.calculate_pattern_significance(odd_even_pattern)
        assert 0 <= significance <= 1
    
    def test_get_pattern_summary(self, analyzer, consecutive_draws):
        """Test comprehensive pattern summary."""
        summary = analyzer.get_pattern_summary(consecutive_draws)
        
        # Check required keys
        required_keys = [
            'total_draws', 'consecutive_patterns', 'odd_even_analysis',
            'range_analysis', 'sum_analysis', 'gap_analysis', 
            'repeat_analysis', 'pattern_score'
        ]
        for key in required_keys:
            assert key in summary
        
        # Check data types
        assert isinstance(summary['total_draws'], int)
        assert isinstance(summary['consecutive_patterns'], list)
        assert isinstance(summary['odd_even_analysis'], dict)
        assert isinstance(summary['range_analysis'], dict)
        assert isinstance(summary['pattern_score'], float)
        
        # Check pattern score is in valid range
        assert 0 <= summary['pattern_score'] <= 100
    
    def test_pattern_summary_insufficient_data(self, analyzer, minimal_draws):
        """Test that insufficient data raises ValueError for summary."""
        with pytest.raises(ValueError, match="Need at least .* draws for pattern analysis"):
            analyzer.get_pattern_summary(minimal_draws)
    
    def test_calculate_range_balance_score(self, analyzer):
        """Test range balance score calculation."""
        # Perfect balance (equal distribution)
        balanced_counts = {'low': 20, 'mid_low': 20, 'mid': 20, 'mid_high': 20, 'high': 20}
        balance_score = analyzer._calculate_range_balance_score(balanced_counts)
        assert balance_score > 90  # Should be high for balanced distribution
        
        # Unbalanced distribution
        unbalanced_counts = {'low': 80, 'mid_low': 5, 'mid': 5, 'mid_high': 5, 'high': 5}
        balance_score = analyzer._calculate_range_balance_score(unbalanced_counts)
        assert balance_score < 50  # Should be low for unbalanced distribution
        
        # Empty counts
        empty_counts = {}
        balance_score = analyzer._calculate_range_balance_score(empty_counts)
        assert balance_score == 0
    
    def test_analyze_number_sums(self, analyzer, consecutive_draws):
        """Test number sum analysis."""
        analysis = analyzer._analyze_number_sums(consecutive_draws)
        
        # Check required keys
        required_keys = ['average_sum', 'min_sum', 'max_sum', 'std_deviation', 'sum_distribution']
        for key in required_keys:
            assert key in analysis
        
        # Check logical relationships
        assert analysis['min_sum'] <= analysis['average_sum'] <= analysis['max_sum']
        assert analysis['std_deviation'] >= 0
        assert isinstance(analysis['sum_distribution'], Counter)
    
    def test_analyze_number_gaps(self, analyzer, consecutive_draws):
        """Test number gap analysis."""
        analysis = analyzer._analyze_number_gaps(consecutive_draws)
        
        # Check required keys
        required_keys = ['average_gap', 'min_gap', 'max_gap', 'std_deviation', 'gap_distribution']
        for key in required_keys:
            assert key in analysis
        
        # Check logical relationships
        assert analysis['min_gap'] <= analysis['average_gap'] <= analysis['max_gap']
        assert analysis['min_gap'] >= 1  # Minimum gap between sorted numbers is 1
        assert analysis['std_deviation'] >= 0
        assert isinstance(analysis['gap_distribution'], Counter)
    
    def test_analyze_repeat_patterns(self, analyzer):
        """Test repeat pattern analysis."""
        # Create draws with known repeat patterns
        draws = [
            DrawResult(
                date=datetime(2024, 1, 1),
                numbers=[1, 2, 3, 4, 5, 6, 7],
                bonus=8,
                jackpot_amount=50000000.0,
                draw_id="2024-001"
            ),
            DrawResult(
                date=datetime(2024, 1, 4),
                numbers=[1, 2, 8, 9, 10, 11, 12],  # 2 repeats (1, 2)
                bonus=13,
                jackpot_amount=55000000.0,
                draw_id="2024-002"
            ),
            DrawResult(
                date=datetime(2024, 1, 7),
                numbers=[1, 15, 16, 17, 18, 19, 20],  # 1 repeat (1)
                bonus=21,
                jackpot_amount=60000000.0,
                draw_id="2024-003"
            )
        ]
        
        analysis = analyzer._analyze_repeat_patterns(draws)
        
        # Check required keys
        required_keys = ['average_repeats', 'max_repeats', 'repeat_distribution']
        for key in required_keys:
            assert key in analysis
        
        # Check expected values based on our test data
        assert analysis['max_repeats'] == 2  # Maximum 2 repeats
        assert analysis['average_repeats'] == 1.5  # (2 + 1) / 2 = 1.5
        assert isinstance(analysis['repeat_distribution'], Counter)
    
    def test_analyze_repeat_patterns_insufficient_draws(self, analyzer):
        """Test repeat analysis with insufficient draws."""
        single_draw = [DrawResult(
            date=datetime(2024, 1, 1),
            numbers=[1, 2, 3, 4, 5, 6, 7],
            bonus=8,
            jackpot_amount=50000000.0,
            draw_id="2024-001"
        )]
        
        analysis = analyzer._analyze_repeat_patterns(single_draw)
        assert analysis == {}
    
    def test_calculate_overall_pattern_score(self, analyzer):
        """Test overall pattern score calculation."""
        # Create mock summary data
        summary = {
            'total_draws': 100,
            'consecutive_patterns': [
                Pattern("consecutive", "2 consecutive", 10, 0.5, []),
                Pattern("consecutive", "3 consecutive", 5, 0.8, [])
            ],
            'odd_even_analysis': {
                'most_common_pattern': ('4-3', 30)
            },
            'range_analysis': {
                'range_balance_score': 75.0
            }
        }
        
        score = analyzer._calculate_overall_pattern_score(summary)
        
        # Score should be calculated and in valid range
        assert 0 <= score <= 100
        assert isinstance(score, float)


if __name__ == "__main__":
    pytest.main([__file__])