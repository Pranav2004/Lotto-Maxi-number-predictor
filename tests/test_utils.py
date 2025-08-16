"""Test utilities for Lotto Max Analyzer tests."""

import random
from datetime import datetime, timedelta
from typing import List, Optional
from pathlib import Path

from lotto_max_analyzer.data.models import DrawResult, Pattern, FrequencyStats, Recommendation


class MockDataGenerator:
    """Generate mock data for testing."""
    
    def __init__(self, seed: int = 42):
        """Initialize with random seed for reproducible tests."""
        self.random = random.Random(seed)
    
    def generate_draw_result(self, 
                           draw_id: Optional[str] = None,
                           date: Optional[datetime] = None,
                           numbers: Optional[List[int]] = None,
                           bonus: Optional[int] = None,
                           jackpot_amount: Optional[float] = None) -> DrawResult:
        """
        Generate a single mock DrawResult.
        
        Args:
            draw_id: Custom draw ID (auto-generated if None)
            date: Custom date (auto-generated if None)
            numbers: Custom numbers (auto-generated if None)
            bonus: Custom bonus number (auto-generated if None)
            jackpot_amount: Custom jackpot amount (auto-generated if None)
            
        Returns:
            Mock DrawResult
        """
        if draw_id is None:
            draw_id = f"MOCK_{self.random.randint(1000, 9999)}"
        
        if date is None:
            # Random date within last 2 years
            days_ago = self.random.randint(0, 730)
            date = datetime.now() - timedelta(days=days_ago)
        
        if numbers is None:
            # Generate 7 unique numbers between 1-49
            numbers = sorted(self.random.sample(range(1, 50), 7))
        
        if bonus is None:
            # Generate bonus number not in main numbers
            available_numbers = [n for n in range(1, 50) if n not in numbers]
            bonus = self.random.choice(available_numbers)
        
        if jackpot_amount is None:
            # Random jackpot between 10M and 100M
            jackpot_amount = self.random.uniform(10_000_000, 100_000_000)
        
        return DrawResult(
            draw_id=draw_id,
            date=date,
            numbers=numbers,
            bonus=bonus,
            jackpot_amount=jackpot_amount
        )
    
    def generate_draw_sequence(self, 
                             count: int,
                             start_date: Optional[datetime] = None,
                             interval_days: int = 3) -> List[DrawResult]:
        """
        Generate a sequence of mock draws.
        
        Args:
            count: Number of draws to generate
            start_date: Starting date (defaults to 1 year ago)
            interval_days: Days between draws (default 3 for Tue/Fri)
            
        Returns:
            List of mock DrawResult objects
        """
        if start_date is None:
            start_date = datetime.now() - timedelta(days=365)
        
        draws = []
        current_date = start_date
        
        for i in range(count):
            draw = self.generate_draw_result(
                draw_id=f"SEQ_{i+1:04d}",
                date=current_date
            )
            draws.append(draw)
            current_date += timedelta(days=interval_days)
        
        return draws
    
    def generate_realistic_draws(self, count: int) -> List[DrawResult]:
        """
        Generate more realistic mock draws with patterns.
        
        Args:
            count: Number of draws to generate
            
        Returns:
            List of realistic mock DrawResult objects
        """
        draws = []
        base_date = datetime(2023, 1, 1)
        
        # Some numbers appear more frequently (hot numbers)
        hot_numbers = [7, 14, 21, 28, 35, 42, 49]
        cold_numbers = [2, 9, 16, 23, 30, 37, 44]
        
        for i in range(count):
            # Bias towards hot numbers occasionally
            if self.random.random() < 0.3:  # 30% chance for hot pattern
                numbers = self.random.sample(hot_numbers, 4)
                numbers.extend(self.random.sample([n for n in range(1, 50) if n not in numbers], 3))
            elif self.random.random() < 0.1:  # 10% chance for cold pattern
                numbers = self.random.sample(cold_numbers, 3)
                numbers.extend(self.random.sample([n for n in range(1, 50) if n not in numbers], 4))
            else:
                # Normal random selection
                numbers = self.random.sample(range(1, 50), 7)
            
            numbers = sorted(numbers)
            
            # Generate bonus
            available_numbers = [n for n in range(1, 50) if n not in numbers]
            bonus = self.random.choice(available_numbers)
            
            # Progressive jackpot amounts
            base_jackpot = 10_000_000
            jackpot_amount = base_jackpot + (i * 500_000) + self.random.uniform(-2_000_000, 5_000_000)
            jackpot_amount = max(jackpot_amount, base_jackpot)
            
            draw = DrawResult(
                draw_id=f"REAL_{i+1:04d}",
                date=base_date + timedelta(days=i*3),
                numbers=numbers,
                bonus=bonus,
                jackpot_amount=jackpot_amount
            )
            draws.append(draw)
        
        return draws
    
    def generate_frequency_stats(self, draws: List[DrawResult]) -> FrequencyStats:
        """
        Generate FrequencyStats from draws.
        
        Args:
            draws: List of DrawResult objects
            
        Returns:
            FrequencyStats object
        """
        number_frequencies = {}
        bonus_frequencies = {}
        
        for draw in draws:
            for number in draw.numbers:
                number_frequencies[number] = number_frequencies.get(number, 0) + 1
            
            bonus_frequencies[draw.bonus] = bonus_frequencies.get(draw.bonus, 0) + 1
        
        return FrequencyStats(
            number_frequencies=number_frequencies,
            bonus_frequencies=bonus_frequencies,
            total_draws=len(draws),
            date_range=(min(draw.date for draw in draws), max(draw.date for draw in draws))
        )
    
    def generate_patterns(self, count: int = 5) -> List[Pattern]:
        """
        Generate mock patterns.
        
        Args:
            count: Number of patterns to generate
            
        Returns:
            List of Pattern objects
        """
        patterns = []
        pattern_types = ['consecutive', 'odd_even', 'range_distribution', 'sum_range']
        
        for i in range(count):
            pattern = Pattern(
                pattern_type=self.random.choice(pattern_types),
                description=f"Mock pattern {i+1}",
                frequency=self.random.uniform(0.1, 0.8),
                significance=self.random.uniform(0.05, 0.95),
                examples=[
                    [self.random.randint(1, 49) for _ in range(7)]
                    for _ in range(self.random.randint(1, 4))
                ]
            )
            patterns.append(pattern)
        
        return patterns
    
    def generate_recommendations(self, count: int = 3) -> List[Recommendation]:
        """
        Generate mock recommendations.
        
        Args:
            count: Number of recommendations to generate
            
        Returns:
            List of Recommendation objects
        """
        recommendations = []
        strategies = ['hot_numbers', 'cold_numbers', 'balanced']
        
        for i in range(count):
            numbers = sorted(self.random.sample(range(1, 50), 7))
            
            recommendation = Recommendation(
                numbers=numbers,
                strategy=self.random.choice(strategies),
                confidence=self.random.uniform(0.3, 0.9),
                reasoning=f"Mock recommendation {i+1} based on test data"
            )
            recommendations.append(recommendation)
        
        return recommendations
    
    def generate_test_database_data(self, db_path: Path, draw_count: int = 100):
        """
        Generate and save test data to a database.
        
        Args:
            db_path: Path to database file
            draw_count: Number of draws to generate
        """
        from lotto_max_analyzer.data.storage import DataStorage
        
        storage = DataStorage(db_path)
        draws = self.generate_realistic_draws(draw_count)
        
        for draw in draws:
            storage.save_draw(draw)
        
        return draws


class TestAssertions:
    """Custom assertions for testing Lotto Max Analyzer."""
    
    @staticmethod
    def assert_valid_draw_result(draw: DrawResult):
        """Assert that a DrawResult is valid."""
        assert isinstance(draw, DrawResult)
        assert isinstance(draw.draw_id, str)
        assert len(draw.draw_id) > 0
        assert isinstance(draw.date, datetime)
        assert isinstance(draw.numbers, list)
        assert len(draw.numbers) == 7
        assert all(isinstance(n, int) for n in draw.numbers)
        assert all(1 <= n <= 49 for n in draw.numbers)
        assert len(set(draw.numbers)) == 7  # No duplicates
        assert isinstance(draw.bonus, int)
        assert 1 <= draw.bonus <= 49
        assert draw.bonus not in draw.numbers
        assert isinstance(draw.jackpot_amount, (int, float))
        assert draw.jackpot_amount >= 0
    
    @staticmethod
    def assert_valid_frequency_stats(stats: FrequencyStats):
        """Assert that FrequencyStats is valid."""
        assert isinstance(stats, FrequencyStats)
        assert isinstance(stats.number_frequencies, dict)
        assert isinstance(stats.bonus_frequencies, dict)
        assert isinstance(stats.total_draws, int)
        assert stats.total_draws >= 0
        assert isinstance(stats.date_range, tuple)
        assert len(stats.date_range) == 2
        assert all(isinstance(d, datetime) for d in stats.date_range)
        
        # Check frequency values
        for number, freq in stats.number_frequencies.items():
            assert isinstance(number, int)
            assert 1 <= number <= 49
            assert isinstance(freq, int)
            assert freq >= 0
    
    @staticmethod
    def assert_valid_pattern(pattern: Pattern):
        """Assert that a Pattern is valid."""
        assert isinstance(pattern, Pattern)
        assert isinstance(pattern.pattern_type, str)
        assert len(pattern.pattern_type) > 0
        assert isinstance(pattern.description, str)
        assert isinstance(pattern.frequency, (int, float))
        assert 0 <= pattern.frequency <= 1
        assert isinstance(pattern.significance, (int, float))
        assert 0 <= pattern.significance <= 1
        assert isinstance(pattern.examples, list)
    
    @staticmethod
    def assert_valid_recommendation(recommendation: Recommendation):
        """Assert that a Recommendation is valid."""
        assert isinstance(recommendation, Recommendation)
        assert isinstance(recommendation.numbers, list)
        assert len(recommendation.numbers) == 7
        assert all(isinstance(n, int) for n in recommendation.numbers)
        assert all(1 <= n <= 49 for n in recommendation.numbers)
        assert len(set(recommendation.numbers)) == 7  # No duplicates
        assert isinstance(recommendation.strategy, str)
        assert len(recommendation.strategy) > 0
        assert isinstance(recommendation.confidence, (int, float))
        assert 0 <= recommendation.confidence <= 1
        assert isinstance(recommendation.reasoning, str)
    
    @staticmethod
    def assert_draws_chronological(draws: List[DrawResult]):
        """Assert that draws are in chronological order."""
        for i in range(1, len(draws)):
            assert draws[i-1].date <= draws[i].date, \
                f"Draws not in chronological order at index {i}"
    
    @staticmethod
    def assert_no_duplicate_draws(draws: List[DrawResult]):
        """Assert that there are no duplicate draw IDs."""
        draw_ids = [draw.draw_id for draw in draws]
        assert len(draw_ids) == len(set(draw_ids)), \
            "Duplicate draw IDs found"
    
    @staticmethod
    def assert_frequency_consistency(draws: List[DrawResult], stats: FrequencyStats):
        """Assert that frequency stats are consistent with draws."""
        # Count actual frequencies
        actual_number_freq = {}
        actual_bonus_freq = {}
        
        for draw in draws:
            for number in draw.numbers:
                actual_number_freq[number] = actual_number_freq.get(number, 0) + 1
            actual_bonus_freq[draw.bonus] = actual_bonus_freq.get(draw.bonus, 0) + 1
        
        # Compare with stats
        assert stats.total_draws == len(draws)
        assert stats.number_frequencies == actual_number_freq
        assert stats.bonus_frequencies == actual_bonus_freq


class PerformanceTimer:
    """Utility for measuring test performance."""
    
    def __init__(self):
        """Initialize the timer."""
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        """Start timing."""
        import time
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timing."""
        import time
        self.end_time = time.time()
    
    @property
    def elapsed(self) -> float:
        """Get elapsed time in seconds."""
        if self.start_time is None or self.end_time is None:
            raise RuntimeError("Timer not properly used with context manager")
        return self.end_time - self.start_time
    
    def assert_under_threshold(self, threshold: float, operation: str = "Operation"):
        """Assert that elapsed time is under threshold."""
        assert self.elapsed < threshold, \
            f"{operation} took {self.elapsed:.2f}s, expected under {threshold}s"


def create_temp_database() -> Path:
    """Create a temporary database for testing."""
    import tempfile
    temp_dir = tempfile.mkdtemp()
    return Path(temp_dir) / "test.db"


def cleanup_temp_database(db_path: Path):
    """Clean up temporary database and directory."""
    import shutil
    if db_path.exists():
        shutil.rmtree(db_path.parent, ignore_errors=True)