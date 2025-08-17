"""Pattern detection module for Lotto Max draws."""

import logging
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Optional
from statistics import mean, stdev
import math

from ..data.models import DrawResult, Pattern
from ..config import NUMBER_RANGES, MIN_DRAWS_FOR_ANALYSIS


class PatternAnalyzer:
    """Analyzes patterns in Lotto Max draw results."""
    
    def __init__(self):
        """Initialize the pattern analyzer."""
        self.logger = logging.getLogger(__name__)
    
    def detect_consecutive_patterns(self, draws: List[DrawResult]) -> List[Pattern]:
        """
        Detect consecutive number patterns in draws.
        
        Args:
            draws: List of DrawResult objects to analyze
            
        Returns:
            List of Pattern objects representing consecutive patterns
        """
        if len(draws) < MIN_DRAWS_FOR_ANALYSIS:
            raise ValueError(f"Need at least {MIN_DRAWS_FOR_ANALYSIS} draws for pattern analysis")
        
        self.logger.info(f"Detecting consecutive patterns in {len(draws)} draws")
        
        patterns = []
        
        # Track different types of consecutive patterns
        consecutive_counts = defaultdict(int)
        examples = defaultdict(list)
        
        for draw in draws:
            sorted_numbers = sorted(draw.numbers)
            
            # Find consecutive sequences
            consecutive_sequences = self._find_consecutive_sequences(sorted_numbers)
            
            for seq_length, sequences in consecutive_sequences.items():
                if seq_length >= 2:
                    consecutive_counts[seq_length] += len(sequences)
                    examples[seq_length].extend(sequences[:3])  # Keep first 3 examples
        
        # Create pattern objects for each type
        for length, count in consecutive_counts.items():
            if count > 0:
                significance = self._calculate_consecutive_significance(count, len(draws), length)
                
                pattern = Pattern(
                    type="consecutive",
                    description=f"{length} consecutive numbers",
                    frequency=count,
                    significance=significance,
                    examples=examples[length][:5]  # Limit to 5 examples
                )
                patterns.append(pattern)
        
        self.logger.info(f"Found {len(patterns)} consecutive patterns")
        return patterns
    
    def analyze_odd_even_distribution(self, draws: List[DrawResult]) -> Dict[str, float]:
        """
        Analyze the distribution of odd and even numbers in draws.
        
        Args:
            draws: List of DrawResult objects to analyze
            
        Returns:
            Dictionary containing odd/even distribution statistics
        """
        if not draws:
            return {}
        
        self.logger.info(f"Analyzing odd/even distribution in {len(draws)} draws")
        
        odd_even_counts = []
        distribution_patterns = defaultdict(int)
        
        for draw in draws:
            odd_count = sum(1 for num in draw.numbers if num % 2 == 1)
            even_count = 7 - odd_count
            
            odd_even_counts.append((odd_count, even_count))
            
            # Track specific patterns (e.g., "4-3", "5-2")
            pattern_key = f"{odd_count}-{even_count}"
            distribution_patterns[pattern_key] += 1
        
        # Calculate statistics
        odd_counts = [odd for odd, _ in odd_even_counts]
        even_counts = [even for _, even in odd_even_counts]
        
        total_draws = len(draws)
        
        analysis = {
            'average_odd_count': mean(odd_counts),
            'average_even_count': mean(even_counts),
            'odd_std_deviation': stdev(odd_counts) if len(odd_counts) > 1 else 0,
            'even_std_deviation': stdev(even_counts) if len(even_counts) > 1 else 0,
            'most_common_pattern': max(distribution_patterns.items(), key=lambda x: x[1]),
            'pattern_distribution': dict(distribution_patterns),
            'pattern_percentages': {
                pattern: (count / total_draws) * 100 
                for pattern, count in distribution_patterns.items()
            }
        }
        
        self.logger.info(f"Most common odd/even pattern: {analysis['most_common_pattern']}")
        return analysis
    
    def analyze_range_distribution(self, draws: List[DrawResult]) -> Dict[str, int]:
        """
        Analyze how numbers are distributed across different ranges.
        
        Args:
            draws: List of DrawResult objects to analyze
            
        Returns:
            Dictionary containing range distribution statistics
        """
        if not draws:
            return {}
        
        self.logger.info(f"Analyzing range distribution in {len(draws)} draws")
        
        range_counts = {range_name: 0 for range_name in NUMBER_RANGES.keys()}
        range_appearances = {range_name: [] for range_name in NUMBER_RANGES.keys()}
        
        for draw in draws:
            draw_range_counts = {range_name: 0 for range_name in NUMBER_RANGES.keys()}
            
            for number in draw.numbers:
                for range_name, (min_val, max_val) in NUMBER_RANGES.items():
                    if min_val <= number <= max_val:
                        range_counts[range_name] += 1
                        draw_range_counts[range_name] += 1
                        break
            
            # Track how many numbers from each range appear per draw
            for range_name, count in draw_range_counts.items():
                range_appearances[range_name].append(count)
        
        # Calculate additional statistics
        total_numbers = len(draws) * 7
        
        analysis = {
            'total_counts': range_counts,
            'percentages': {
                range_name: (count / total_numbers) * 100 
                for range_name, count in range_counts.items()
            },
            'average_per_draw': {
                range_name: mean(appearances) if appearances else 0
                for range_name, appearances in range_appearances.items()
            },
            'max_per_draw': {
                range_name: max(appearances) if appearances else 0
                for range_name, appearances in range_appearances.items()
            },
            'range_balance_score': self._calculate_range_balance_score(range_counts)
        }
        
        self.logger.info(f"Range distribution calculated for {len(NUMBER_RANGES)} ranges")
        return analysis
    
    def calculate_pattern_significance(self, pattern: Pattern) -> float:
        """
        Calculate the statistical significance of a detected pattern.
        
        Args:
            pattern: Pattern object to analyze
            
        Returns:
            Significance score between 0 and 1
        """
        if pattern.type == "consecutive":
            # For consecutive patterns, significance based on rarity
            if "2 consecutive" in pattern.description:
                expected_frequency = 0.15  # Pairs are relatively common
            elif "3 consecutive" in pattern.description:
                expected_frequency = 0.05  # Triplets are less common
            elif "4 consecutive" in pattern.description:
                expected_frequency = 0.01  # Quadruplets are rare
            else:
                expected_frequency = 0.001  # Longer sequences are very rare
            
            # Compare actual vs expected frequency
            significance = min(1.0, pattern.frequency * expected_frequency)
            
        elif pattern.type == "odd_even":
            # For odd/even patterns, significance based on deviation from expected
            expected_ratio = 0.5  # Expected 50/50 split
            actual_ratio = pattern.frequency / 7  # Assuming frequency is odd count
            deviation = abs(actual_ratio - expected_ratio)
            significance = min(1.0, deviation * 2)  # Scale to 0-1
            
        elif pattern.type == "range":
            # For range patterns, significance based on balance
            significance = pattern.frequency / 100  # Assuming frequency is balance score
            
        else:
            significance = 0.5  # Default moderate significance
        
        return significance
    
    def get_pattern_summary(self, draws: List[DrawResult]) -> Dict[str, any]:
        """
        Get a comprehensive summary of all patterns in the draws.
        
        Args:
            draws: List of DrawResult objects to analyze
            
        Returns:
            Dictionary containing all pattern analysis results
        """
        if len(draws) < MIN_DRAWS_FOR_ANALYSIS:
            raise ValueError(f"Need at least {MIN_DRAWS_FOR_ANALYSIS} draws for pattern analysis")
        
        self.logger.info(f"Generating pattern summary for {len(draws)} draws")
        
        summary = {
            'total_draws': len(draws),
            'consecutive_patterns': self.detect_consecutive_patterns(draws),
            'odd_even_analysis': self.analyze_odd_even_distribution(draws),
            'range_analysis': self.analyze_range_distribution(draws),
            'sum_analysis': self._analyze_number_sums(draws),
            'gap_analysis': self._analyze_number_gaps(draws),
            'repeat_analysis': self._analyze_repeat_patterns(draws)
        }
        
        # Calculate overall pattern score
        summary['pattern_score'] = self._calculate_overall_pattern_score(summary)
        
        self.logger.info("Pattern summary generation complete")
        return summary
    
    def _find_consecutive_sequences(self, sorted_numbers: List[int]) -> Dict[int, List[List[int]]]:
        """Find all consecutive sequences in a sorted list of numbers."""
        sequences = defaultdict(list)
        
        i = 0
        while i < len(sorted_numbers):
            current_seq = [sorted_numbers[i]]
            j = i + 1
            
            # Extend the sequence as long as numbers are consecutive
            while j < len(sorted_numbers) and sorted_numbers[j] == sorted_numbers[j-1] + 1:
                current_seq.append(sorted_numbers[j])
                j += 1
            
            # If sequence has 2 or more numbers, record it
            if len(current_seq) >= 2:
                sequences[len(current_seq)].append(current_seq)
            
            i = j if j > i + 1 else i + 1
        
        return sequences
    
    def _calculate_consecutive_significance(self, count: int, total_draws: int, length: int) -> float:
        """Calculate significance of consecutive patterns."""
        # Probability of getting consecutive numbers decreases with length
        base_probability = {2: 0.3, 3: 0.1, 4: 0.03, 5: 0.01}.get(length, 0.001)
        expected_count = total_draws * base_probability
        
        if expected_count == 0:
            return 1.0 if count > 0 else 0.0
        
        # Significance based on how much actual exceeds expected
        significance = min(1.0, count / expected_count)
        return significance
    
    def _calculate_range_balance_score(self, range_counts: Dict[str, int]) -> float:
        """Calculate how balanced the distribution is across ranges."""
        if not range_counts:
            return 0.0
        
        total_count = sum(range_counts.values())
        if total_count == 0:
            return 0.0
        
        expected_per_range = total_count / len(range_counts)
        
        # Calculate variance from expected distribution
        variance = sum((count - expected_per_range) ** 2 for count in range_counts.values())
        variance /= len(range_counts)
        
        # Convert to balance score (lower variance = higher balance)
        max_possible_variance = expected_per_range ** 2
        balance_score = max(0, 100 - (variance / max_possible_variance) * 100)
        
        return balance_score
    
    def _analyze_number_sums(self, draws: List[DrawResult]) -> Dict[str, any]:
        """Analyze the sum of numbers in each draw."""
        sums = [sum(draw.numbers) for draw in draws]
        
        return {
            'average_sum': mean(sums),
            'min_sum': min(sums),
            'max_sum': max(sums),
            'std_deviation': stdev(sums) if len(sums) > 1 else 0,
            'sum_distribution': Counter(sums)
        }
    
    def _analyze_number_gaps(self, draws: List[DrawResult]) -> Dict[str, any]:
        """Analyze gaps between consecutive numbers in draws."""
        all_gaps = []
        
        for draw in draws:
            sorted_numbers = sorted(draw.numbers)
            gaps = [sorted_numbers[i+1] - sorted_numbers[i] for i in range(len(sorted_numbers)-1)]
            all_gaps.extend(gaps)
        
        if not all_gaps:
            return {}
        
        return {
            'average_gap': mean(all_gaps),
            'min_gap': min(all_gaps),
            'max_gap': max(all_gaps),
            'std_deviation': stdev(all_gaps) if len(all_gaps) > 1 else 0,
            'gap_distribution': Counter(all_gaps)
        }
    
    def _analyze_repeat_patterns(self, draws: List[DrawResult]) -> Dict[str, any]:
        """Analyze how often numbers repeat from previous draws."""
        if len(draws) < 2:
            return {}
        
        repeat_counts = []
        
        for i in range(1, len(draws)):
            current_numbers = set(draws[i].numbers)
            previous_numbers = set(draws[i-1].numbers)
            
            repeats = len(current_numbers.intersection(previous_numbers))
            repeat_counts.append(repeats)
        
        return {
            'average_repeats': mean(repeat_counts) if repeat_counts else 0,
            'max_repeats': max(repeat_counts) if repeat_counts else 0,
            'repeat_distribution': Counter(repeat_counts) if repeat_counts else {}
        }
    
    def _calculate_overall_pattern_score(self, summary: Dict[str, any]) -> float:
        """Calculate an overall pattern complexity score."""
        score = 0.0
        
        # Consecutive patterns contribute to score
        consecutive_patterns = summary.get('consecutive_patterns', [])
        score += len(consecutive_patterns) * 10
        
        # Odd/even balance contributes to score
        odd_even = summary.get('odd_even_analysis', {})
        if odd_even:
            most_common_freq = odd_even.get('most_common_pattern', (None, 0))[1]
            total_draws = summary.get('total_draws', 1)
            balance_score = (most_common_freq / total_draws) * 100
            score += balance_score
        
        # Range balance contributes to score
        range_analysis = summary.get('range_analysis', {})
        if range_analysis:
            balance_score = range_analysis.get('range_balance_score', 0)
            score += balance_score
        
        # Normalize to 0-100 scale
        return min(100.0, score)