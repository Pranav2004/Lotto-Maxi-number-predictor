"""Frequency analysis module for Lotto Max numbers."""

import logging
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from statistics import mean, stdev

from ..data.models import DrawResult, FrequencyStats
from ..config import (
    LOTTO_MAX_MIN_NUMBER, LOTTO_MAX_MAX_NUMBER, 
    HOT_NUMBER_THRESHOLD, COLD_NUMBER_THRESHOLD,
    MIN_DRAWS_FOR_ANALYSIS
)


class FrequencyAnalyzer:
    """Analyzes frequency patterns in Lotto Max draw results."""
    
    def __init__(self):
        """Initialize the frequency analyzer."""
        self.logger = logging.getLogger(__name__)
    
    def calculate_number_frequency(self, draws: List[DrawResult]) -> Dict[int, int]:
        """
        Calculate how often each number appears in the draws.
        
        Args:
            draws: List of DrawResult objects to analyze
            
        Returns:
            Dictionary mapping number to frequency count
            
        Raises:
            ValueError: If insufficient data for analysis
        """
        if len(draws) < MIN_DRAWS_FOR_ANALYSIS:
            raise ValueError(f"Need at least {MIN_DRAWS_FOR_ANALYSIS} draws for analysis, got {len(draws)}")
        
        self.logger.info(f"Calculating frequency for {len(draws)} draws")
        
        # Count all numbers across all draws
        all_numbers = []
        for draw in draws:
            all_numbers.extend(draw.numbers)
        
        frequency_counter = Counter(all_numbers)
        
        # Ensure all numbers 1-50 are represented (even if count is 0)
        frequency_dict = {}
        for num in range(LOTTO_MAX_MIN_NUMBER, LOTTO_MAX_MAX_NUMBER + 1):
            frequency_dict[num] = frequency_counter.get(num, 0)
        
        self.logger.debug(f"Frequency calculation complete. Most common: {frequency_counter.most_common(5)}")
        return frequency_dict
    
    def get_hot_numbers(self, draws: List[DrawResult], threshold: Optional[float] = None) -> List[int]:
        """
        Identify hot numbers (appearing more frequently than expected).
        
        Args:
            draws: List of DrawResult objects to analyze
            threshold: Custom threshold for hot numbers (default from config)
            
        Returns:
            List of hot numbers sorted by frequency (descending)
        """
        if threshold is None:
            threshold = HOT_NUMBER_THRESHOLD
        
        frequency = self.calculate_number_frequency(draws)
        expected_frequency = self._calculate_expected_frequency(draws)
        
        hot_numbers = []
        for number, count in frequency.items():
            if count > expected_frequency * threshold:
                hot_numbers.append((number, count))
        
        # Sort by frequency (descending)
        hot_numbers.sort(key=lambda x: x[1], reverse=True)
        
        result = [num for num, _ in hot_numbers]
        self.logger.info(f"Found {len(result)} hot numbers (threshold: {threshold})")
        return result
    
    def get_cold_numbers(self, draws: List[DrawResult], threshold: Optional[float] = None) -> List[int]:
        """
        Identify cold numbers (appearing less frequently than expected).
        
        Args:
            draws: List of DrawResult objects to analyze
            threshold: Custom threshold for cold numbers (default from config)
            
        Returns:
            List of cold numbers sorted by frequency (ascending)
        """
        if threshold is None:
            threshold = COLD_NUMBER_THRESHOLD
        
        frequency = self.calculate_number_frequency(draws)
        expected_frequency = self._calculate_expected_frequency(draws)
        
        cold_numbers = []
        for number, count in frequency.items():
            if count < expected_frequency * threshold:
                cold_numbers.append((number, count))
        
        # Sort by frequency (ascending)
        cold_numbers.sort(key=lambda x: x[1])
        
        result = [num for num, _ in cold_numbers]
        self.logger.info(f"Found {len(result)} cold numbers (threshold: {threshold})")
        return result
    
    def analyze_frequency_trends(self, draws: List[DrawResult]) -> Dict[str, any]:
        """
        Analyze frequency trends over time periods.
        
        Args:
            draws: List of DrawResult objects to analyze
            
        Returns:
            Dictionary containing trend analysis results
        """
        if len(draws) < MIN_DRAWS_FOR_ANALYSIS:
            raise ValueError(f"Need at least {MIN_DRAWS_FOR_ANALYSIS} draws for trend analysis")
        
        self.logger.info(f"Analyzing frequency trends for {len(draws)} draws")
        
        # Sort draws by date
        sorted_draws = sorted(draws, key=lambda d: d.date)
        
        # Calculate overall statistics
        frequency = self.calculate_number_frequency(draws)
        expected_freq = self._calculate_expected_frequency(draws)
        
        # Calculate frequency statistics for each number
        freq_stats = self._calculate_frequency_stats(sorted_draws)
        
        # Analyze trends over time periods
        monthly_trends = self._analyze_monthly_trends(sorted_draws)
        
        # Calculate statistical measures
        frequencies = list(frequency.values())
        
        trends = {
            'total_draws': len(draws),
            'date_range': {
                'start': sorted_draws[0].date.isoformat(),
                'end': sorted_draws[-1].date.isoformat()
            },
            'overall_stats': {
                'expected_frequency': expected_freq,
                'mean_frequency': mean(frequencies),
                'std_deviation': stdev(frequencies) if len(frequencies) > 1 else 0,
                'min_frequency': min(frequencies),
                'max_frequency': max(frequencies)
            },
            'hot_numbers': self.get_hot_numbers(draws),
            'cold_numbers': self.get_cold_numbers(draws),
            'frequency_distribution': frequency,
            'number_statistics': freq_stats,
            'monthly_trends': monthly_trends
        }
        
        self.logger.info("Frequency trend analysis complete")
        return trends
    
    def get_frequency_statistics(self, draws: List[DrawResult]) -> Dict[int, FrequencyStats]:
        """
        Get detailed frequency statistics for each number.
        
        Args:
            draws: List of DrawResult objects to analyze
            
        Returns:
            Dictionary mapping number to FrequencyStats object
        """
        if not draws:
            return {}
        
        sorted_draws = sorted(draws, key=lambda d: d.date)
        frequency = self.calculate_number_frequency(draws)
        total_draws = len(draws)
        
        stats = {}
        
        for number in range(LOTTO_MAX_MIN_NUMBER, LOTTO_MAX_MAX_NUMBER + 1):
            count = frequency[number]
            percentage = (count / (total_draws * 7)) * 100  # 7 numbers per draw
            
            # Find last occurrence
            last_seen = None
            for draw in reversed(sorted_draws):
                if number in draw.numbers:
                    last_seen = draw.date
                    break
            
            # Calculate average gap between appearances
            gaps = self._calculate_number_gaps(number, sorted_draws)
            average_gap = mean(gaps) if gaps else float('inf')
            
            stats[number] = FrequencyStats(
                number=number,
                count=count,
                percentage=percentage,
                last_seen=last_seen,
                average_gap=average_gap
            )
        
        return stats
    
    def _calculate_expected_frequency(self, draws: List[DrawResult]) -> float:
        """Calculate the expected frequency for a number in the given draws."""
        total_draws = len(draws)
        numbers_per_draw = 7
        total_possible_numbers = LOTTO_MAX_MAX_NUMBER - LOTTO_MAX_MIN_NUMBER + 1
        
        # Expected frequency = (total numbers drawn) / (total possible numbers)
        expected = (total_draws * numbers_per_draw) / total_possible_numbers
        return expected
    
    def _calculate_frequency_stats(self, sorted_draws: List[DrawResult]) -> Dict[int, Dict[str, any]]:
        """Calculate detailed statistics for each number."""
        stats = {}
        
        for number in range(LOTTO_MAX_MIN_NUMBER, LOTTO_MAX_MAX_NUMBER + 1):
            appearances = []
            
            for i, draw in enumerate(sorted_draws):
                if number in draw.numbers:
                    appearances.append(i)
            
            if appearances:
                gaps = []
                for i in range(1, len(appearances)):
                    gap = appearances[i] - appearances[i-1]
                    gaps.append(gap)
                
                stats[number] = {
                    'appearances': len(appearances),
                    'first_seen': appearances[0],
                    'last_seen': appearances[-1],
                    'gaps': gaps,
                    'average_gap': mean(gaps) if gaps else 0,
                    'min_gap': min(gaps) if gaps else 0,
                    'max_gap': max(gaps) if gaps else 0
                }
            else:
                stats[number] = {
                    'appearances': 0,
                    'first_seen': None,
                    'last_seen': None,
                    'gaps': [],
                    'average_gap': float('inf'),
                    'min_gap': 0,
                    'max_gap': 0
                }
        
        return stats
    
    def _analyze_monthly_trends(self, sorted_draws: List[DrawResult]) -> Dict[str, Dict[int, int]]:
        """Analyze frequency trends by month."""
        monthly_frequency = defaultdict(lambda: defaultdict(int))
        
        for draw in sorted_draws:
            month_key = draw.date.strftime('%Y-%m')
            for number in draw.numbers:
                monthly_frequency[month_key][number] += 1
        
        return dict(monthly_frequency)
    
    def _calculate_number_gaps(self, number: int, sorted_draws: List[DrawResult]) -> List[int]:
        """Calculate gaps between appearances of a specific number."""
        appearances = []
        
        for i, draw in enumerate(sorted_draws):
            if number in draw.numbers:
                appearances.append(i)
        
        gaps = []
        for i in range(1, len(appearances)):
            gap = appearances[i] - appearances[i-1]
            gaps.append(gap)
        
        return gaps
    
    def get_overdue_numbers(self, draws: List[DrawResult], threshold_days: int = 30) -> List[Tuple[int, int]]:
        """
        Find numbers that haven't appeared recently.
        
        Args:
            draws: List of DrawResult objects to analyze
            threshold_days: Number of days to consider a number overdue
            
        Returns:
            List of tuples (number, days_since_last_seen)
        """
        if not draws:
            return []
        
        sorted_draws = sorted(draws, key=lambda d: d.date)
        latest_date = sorted_draws[-1].date
        
        overdue_numbers = []
        
        for number in range(LOTTO_MAX_MIN_NUMBER, LOTTO_MAX_MAX_NUMBER + 1):
            last_seen = None
            
            # Find the most recent appearance
            for draw in reversed(sorted_draws):
                if number in draw.numbers:
                    last_seen = draw.date
                    break
            
            if last_seen:
                days_since = (latest_date - last_seen).days
                if days_since >= threshold_days:
                    overdue_numbers.append((number, days_since))
            else:
                # Never appeared in the dataset
                days_since = (latest_date - sorted_draws[0].date).days
                overdue_numbers.append((number, days_since))
        
        # Sort by days since last seen (descending)
        overdue_numbers.sort(key=lambda x: x[1], reverse=True)
        
        return overdue_numbers