"""Unit tests for frequency analysis operations."""

import pytest
from datetime import datetime, timedelta
from statistics import mean

from lotto_max_analyzer.analysis.frequency import FrequencyAnalyzer
from lotto_max_analyzer.data.models import DrawResult, FrequencyStats


class TestFrequencyAnalyzer:
    """Test cases for FrequencyAnalyzer class."""
    
    @pytest.fixture
    def analyzer(self):
        """Create a FrequencyAnalyzer instance for testing."""
        return FrequencyAnalyzer()
    
    @pytest.fixture
    def sample_draws(self):
        """Create sample draw results for testing."""
        draws = []
        base_date = datetime(2024, 1, 1)
        
        # Create 60 draws (enough for analysis)
        for i in range(60):
            # Create draws with some numbers appearing more frequently
            if i < 20:
                # First 20 draws: numbers 1-7 appear frequently
                numbers = [1, 2, 3, 4, 5, 6, 7]
            elif i < 40:
                # Next 20 draws: numbers 8-14 appear frequently
                numbers = [8, 9, 10, 11, 12, 13, 14]
            else:
                # Last 20 draws: mixed numbers
                numbers = [15, 16, 17, 18, 19, 20, 21]
            
            draw = DrawResult(
                date=base_date + timedelta(days=i * 3),  # Every 3 days
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
    
    def test_analyzer_initialization(self, analyzer):
        """Test that analyzer initializes properly."""
        assert analyzer.logger is not None
    
    def test_calculate_number_frequency(self, analyzer, sample_draws):
        """Test basic frequency calculation."""
        frequency = analyzer.calculate_number_frequency(sample_draws)
        
        # Should have entries for all numbers 1-50
        assert len(frequency) == 50
        assert all(num in frequency for num in range(1, 51))
        
        # Numbers 1-7 should appear 20 times each (first 20 draws)
        for num in range(1, 8):
            assert frequency[num] == 20
        
        # Numbers 8-14 should appear 20 times each (next 20 draws)
        for num in range(8, 15):
            assert frequency[num] == 20
        
        # Numbers 15-21 should appear 20 times each (last 20 draws)
        for num in range(15, 22):
            assert frequency[num] == 20
        
        # Other numbers should appear 0 times
        for num in range(22, 51):
            assert frequency[num] == 0
    
    def test_calculate_frequency_insufficient_data(self, analyzer, minimal_draws):
        """Test that insufficient data raises ValueError."""
        with pytest.raises(ValueError, match="Need at least .* draws for analysis"):
            analyzer.calculate_number_frequency(minimal_draws)
    
    def test_get_hot_numbers(self, analyzer, sample_draws):
        """Test hot number identification."""
        hot_numbers = analyzer.get_hot_numbers(sample_draws)
        
        # Should identify numbers that appear frequently
        assert len(hot_numbers) > 0
        
        # Hot numbers should be sorted by frequency (descending)
        frequency = analyzer.calculate_number_frequency(sample_draws)
        for i in range(len(hot_numbers) - 1):
            assert frequency[hot_numbers[i]] >= frequency[hot_numbers[i + 1]]
    
    def test_get_cold_numbers(self, analyzer, sample_draws):
        """Test cold number identification."""
        cold_numbers = analyzer.get_cold_numbers(sample_draws)
        
        # Should identify numbers that appear infrequently
        assert len(cold_numbers) > 0
        
        # Cold numbers should be sorted by frequency (ascending)
        frequency = analyzer.calculate_number_frequency(sample_draws)
        for i in range(len(cold_numbers) - 1):
            assert frequency[cold_numbers[i]] <= frequency[cold_numbers[i + 1]]
    
    def test_hot_cold_numbers_custom_threshold(self, analyzer, sample_draws):
        """Test hot/cold number identification with custom thresholds."""
        # Very strict threshold should find fewer hot numbers
        strict_hot = analyzer.get_hot_numbers(sample_draws, threshold=0.9)
        normal_hot = analyzer.get_hot_numbers(sample_draws, threshold=0.7)
        
        assert len(strict_hot) <= len(normal_hot)
        
        # Very lenient threshold should find fewer cold numbers
        strict_cold = analyzer.get_cold_numbers(sample_draws, threshold=0.1)
        normal_cold = analyzer.get_cold_numbers(sample_draws, threshold=0.3)
        
        assert len(strict_cold) <= len(normal_cold)
    
    def test_analyze_frequency_trends(self, analyzer, sample_draws):
        """Test comprehensive frequency trend analysis."""
        trends = analyzer.analyze_frequency_trends(sample_draws)
        
        # Check required keys
        required_keys = [
            'total_draws', 'date_range', 'overall_stats', 
            'hot_numbers', 'cold_numbers', 'frequency_distribution',
            'number_statistics', 'monthly_trends'
        ]
        for key in required_keys:
            assert key in trends
        
        # Check data types and values
        assert trends['total_draws'] == len(sample_draws)
        assert 'start' in trends['date_range']
        assert 'end' in trends['date_range']
        
        overall_stats = trends['overall_stats']
        assert 'expected_frequency' in overall_stats
        assert 'mean_frequency' in overall_stats
        assert 'std_deviation' in overall_stats
        
        assert isinstance(trends['hot_numbers'], list)
        assert isinstance(trends['cold_numbers'], list)
        assert isinstance(trends['frequency_distribution'], dict)
    
    def test_get_frequency_statistics(self, analyzer, sample_draws):
        """Test detailed frequency statistics calculation."""
        stats = analyzer.get_frequency_statistics(sample_draws)
        
        # Should have stats for all numbers 1-50
        assert len(stats) == 50
        
        for num in range(1, 51):
            assert num in stats
            stat = stats[num]
            assert isinstance(stat, FrequencyStats)
            assert stat.number == num
            assert stat.count >= 0
            assert 0 <= stat.percentage <= 100
            assert stat.average_gap >= 0
    
    def test_get_frequency_statistics_empty_draws(self, analyzer):
        """Test frequency statistics with empty draws list."""
        stats = analyzer.get_frequency_statistics([])
        assert stats == {}
    
    def test_calculate_expected_frequency(self, analyzer, sample_draws):
        """Test expected frequency calculation."""
        expected = analyzer._calculate_expected_frequency(sample_draws)
        
        # Expected frequency = (total_draws * 7) / 50
        total_draws = len(sample_draws)
        expected_manual = (total_draws * 7) / 50
        
        assert expected == expected_manual
        assert expected > 0
    
    def test_get_overdue_numbers(self, analyzer, sample_draws):
        """Test overdue number identification."""
        overdue = analyzer.get_overdue_numbers(sample_draws, threshold_days=30)
        
        # Should return list of tuples (number, days_since)
        assert isinstance(overdue, list)
        
        for number, days_since in overdue:
            assert 1 <= number <= 50
            assert days_since >= 30
        
        # Should be sorted by days_since (descending)
        for i in range(len(overdue) - 1):
            assert overdue[i][1] >= overdue[i + 1][1]
    
    def test_get_overdue_numbers_empty_draws(self, analyzer):
        """Test overdue numbers with empty draws list."""
        overdue = analyzer.get_overdue_numbers([])
        assert overdue == []
    
    def test_calculate_number_gaps(self, analyzer):
        """Test gap calculation for specific numbers."""
        # Create draws where number 7 appears in specific positions
        draws = []
        for i in range(10):
            if i in [1, 4, 8]:
                # Number 7 appears in these draws
                numbers = [1, 2, 3, 4, 5, 6, 7]
            else:
                # Number 7 doesn't appear in these draws
                numbers = [10, 11, 12, 13, 14, 15, 16]
            
            draw = DrawResult(
                date=datetime(2024, 1, 1) + timedelta(days=i),
                numbers=numbers,
                bonus=9,
                jackpot_amount=50000000.0,
                draw_id=f"2024-{i:03d}"
            )
            draws.append(draw)
        
        gaps = analyzer._calculate_number_gaps(7, draws)
        
        # Number 7 appears at positions 1, 4, 8
        # Gaps should be: 4-1=3, 8-4=4
        expected_gaps = [3, 4]
        assert gaps == expected_gaps
    
    def test_monthly_trends_analysis(self, analyzer):
        """Test monthly trend analysis."""
        # Create draws spanning multiple months
        draws = []
        for month in range(1, 4):  # Jan, Feb, Mar
            for day in [1, 15]:  # Two draws per month
                draw = DrawResult(
                    date=datetime(2024, month, day),
                    numbers=[1, 2, 3, 4, 5, 6, 7],
                    bonus=8,
                    jackpot_amount=50000000.0,
                    draw_id=f"2024-{month:02d}-{day:02d}"
                )
                draws.append(draw)
        
        monthly_trends = analyzer._analyze_monthly_trends(draws)
        
        # Should have entries for each month
        assert '2024-01' in monthly_trends
        assert '2024-02' in monthly_trends
        assert '2024-03' in monthly_trends
        
        # Each month should have frequency data
        for month_data in monthly_trends.values():
            assert isinstance(month_data, dict)
            # Numbers 1-7 should appear twice per month
            for num in range(1, 8):
                assert month_data[num] == 2
    
    def test_frequency_stats_last_seen(self, analyzer):
        """Test that last_seen is calculated correctly."""
        draws = [
            DrawResult(
                date=datetime(2024, 1, 1),
                numbers=[1, 2, 3, 4, 5, 6, 7],
                bonus=8,
                jackpot_amount=50000000.0,
                draw_id="2024-001"
            ),
            DrawResult(
                date=datetime(2024, 1, 15),
                numbers=[1, 8, 9, 10, 11, 12, 13],  # Number 1 appears again
                bonus=14,
                jackpot_amount=55000000.0,
                draw_id="2024-002"
            )
        ]
        
        # Add more draws to meet minimum requirement
        for i in range(50):
            draws.append(DrawResult(
                date=datetime(2024, 2, 1) + timedelta(days=i),
                numbers=[20, 21, 22, 23, 24, 25, 26],
                bonus=27,
                jackpot_amount=60000000.0,
                draw_id=f"2024-{100+i:03d}"
            ))
        
        stats = analyzer.get_frequency_statistics(draws)
        
        # Number 1 should have last_seen as Jan 15 (second appearance)
        assert stats[1].last_seen == datetime(2024, 1, 15)
        
        # Number 2 should have last_seen as Jan 1 (only appearance)
        assert stats[2].last_seen == datetime(2024, 1, 1)
        
        # Number 30 never appeared, should have None
        assert stats[30].last_seen is None


if __name__ == "__main__":
    pytest.main([__file__])